const vscode = require('vscode');
const childProcess = require('child_process');
const path = require('path');

const SUPPORTED_LANGUAGES = new Set(['html', 'wxml', 'javascript', 'typescript']);
let backend;
let nextRequestId = 1;
const pending = new Map();

function activate(context) {
  const command = vscode.commands.registerCommand('gencode.generate', generateCode);
  const confirmCommand = vscode.commands.registerCommand('gencode.confirmGenerate', () => generateCode());
  context.subscriptions.push(command, confirmCommand);
  context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(updateInvocationContext));
  context.subscriptions.push(vscode.window.onDidChangeTextEditorSelection((event) => updateInvocationContext(event.textEditor)));
  context.subscriptions.push(vscode.workspace.onDidChangeTextDocument((event) => {
    const editor = vscode.window.activeTextEditor;
    if (editor && event.document === editor.document) updateInvocationContext(editor);
  }));
  updateInvocationContext(vscode.window.activeTextEditor);
  startBackend(context);
}

function invocationAtCursor(source, offset) {
  const pattern = /\bgenCode\s*\(\s*(["'])(?:\\.|(?!\1)[^\\])*?\1\s*\)/gi;
  let match;
  while ((match = pattern.exec(source)) !== null) {
    if (match.index <= offset && offset <= match.index + match[0].length) return true;
  }
  return false;
}

function updateInvocationContext(editor) {
  const active = editor && SUPPORTED_LANGUAGES.has(editor.document.languageId);
  const value = active && invocationAtCursor(
    editor.document.getText(),
    editor.document.offsetAt(editor.selection.active)
  );
  vscode.commands.executeCommand('setContext', 'gencode.invocationAtCursor', Boolean(value));
}

function startBackend(context) {
  const config = vscode.workspace.getConfiguration('gencode');
  const pythonPath = config.get('pythonPath', 'python');
  const backendRoot = path.join(context.extensionPath, 'python');
  backend = childProcess.spawn(pythonPath, ['-m', 'gencode_backend'], {
    cwd: backendRoot,
    env: { ...process.env, PYTHONPATH: backendRoot, PYTHONIOENCODING: 'utf-8' }
  });

  let buffer = '';
  backend.stdout.on('data', (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop();
    for (const line of lines) {
      if (!line.trim()) continue;
      let message;
      try {
        message = JSON.parse(line);
      } catch (error) {
        continue;
      }
      const resolver = pending.get(message.id);
      if (!resolver) continue;
      pending.delete(message.id);
      if (message.ok) resolver.resolve(message);
      else resolver.reject(new Error(message.error || 'GenCode backend failed'));
    }
  });
  backend.stderr.on('data', (chunk) => console.error(`[gencode] ${chunk.toString()}`));
  backend.on('error', (error) => {
    vscode.window.showErrorMessage(`GenCode 无法启动 Python：${error.message}`);
  });
  backend.on('exit', () => {
    for (const resolver of pending.values()) resolver.reject(new Error('Python backend exited'));
    pending.clear();
    backend = undefined;
  });
  context.subscriptions.push({ dispose: () => backend && backend.kill() });
}

function requestBackend(payload) {
  if (!backend || !backend.stdin.writable) {
    return Promise.reject(new Error('Python backend is not running'));
  }
  const id = String(nextRequestId++);
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    backend.stdin.write(`${JSON.stringify({ ...payload, id })}\n`);
  });
}

async function generateCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || !SUPPORTED_LANGUAGES.has(editor.document.languageId)) {
    vscode.window.showInformationMessage('GenCode 仅支持 html、wxml、js、ts 文件。');
    return;
  }
  const workspaceFolder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
  if (!workspaceFolder) {
    vscode.window.showErrorMessage('请先打开一个 workspace。');
    return;
  }
  const config = vscode.workspace.getConfiguration('gencode');
  const source = editor.document.getText();
  if (!/\bgenCode\s*\(/i.test(source)) {
    vscode.window.showInformationMessage('当前文件没有 genCode("...") 调用。');
    return;
  }
  const cursorOffset = editor.document.offsetAt(editor.selection.active);
  const documentVersion = editor.document.version;
  const request = {
    action: 'generate',
    language: editor.document.languageId,
    filePath: editor.document.uri.fsPath,
    workspaceRoot: workspaceFolder.uri.fsPath,
    source,
    cursorOffset,
    config: {
      baseUrl: config.get('baseUrl', ''),
      model: config.get('model', 'text-davinci-003'),
      maxContextChars: config.get('maxContextChars', 24000)
    }
  };
  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: 'GenCode 正在读取关联文件并生成代码…' },
    async () => {
      try {
        const result = await requestBackend(request);
        if (editor.document.version !== documentVersion) {
          vscode.window.showWarningMessage('文件在生成期间发生了变化，请重新执行 GenCode。');
          return;
        }
        const start = editor.document.positionAt(result.markerStart);
        const end = editor.document.positionAt(result.markerEnd);
        const edit = new vscode.WorkspaceEdit();
        edit.replace(editor.document.uri, new vscode.Range(start, end), result.code);
        await vscode.workspace.applyEdit(edit);
        updateInvocationContext(editor);
      } catch (error) {
        vscode.window.showErrorMessage(`GenCode 生成失败：${error.message}`);
      }
    }
  );
}

function deactivate() {
  if (backend) backend.kill();
}

module.exports = { activate, deactivate };

