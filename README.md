# GenCode

在编辑器里写一句需求，直接生成当前项目风格的代码。

GenCode 读取当前文件以及它引用的相对文件，把生成结果放回原位置。适合快速补齐页面片段、请求函数、类型定义和常用业务逻辑。

## 示例

在 `html`、`wxml`、`js` 或 `ts` 文件中输入：

```ts
const button = genCode("创建一个按钮，点击调用接口apiExample")
```

光标放在 `genCode("...")` 内，按 `Shift+Enter` 确认生成。生成代码会替换整个调用表达式。

默认快捷键只有 `Shift+Enter`。需要换成其他按键时，在 VSCode 中打开 **Keyboard Shortcuts**，搜索 `GenCode: Confirm Generate` 并修改绑定即可。也可以从命令面板执行 `GenCode: Generate Code`。

## 支持范围

- 文件类型：HTML、WXML、JavaScript、TypeScript。
- 关联上下文：相对路径 `import`、`require`、HTML/WXML 的 `script`、`src`、`href`，以及同名文件。
- 上下文范围：默认最多 24,000 个字符，自动跳过 `node_modules`、`.git`、`dist` 和 `build`。
- 生成接口：OpenAI 兼容的 Completion API。

## 安装依赖

```bash
python -m pip install -r python/requirements.txt
```

设置 API Key：

```bash
# PowerShell
$env:OPENAI_API_KEY = "your-key"

# macOS/Linux
export OPENAI_API_KEY="your-key"
```

## 设置

在 VSCode `settings.json` 中可以调整：

```json
{
  "gencode.pythonPath": "python",
  "gencode.baseUrl": "",
  "gencode.model": "text-davinci-003",
  "gencode.maxContextChars": 24000
}
```

## 开发

```bash
npm run compile
python -m pytest
npm run package
```

VSCode 扩展入口负责编辑器交互，Python 目录负责标记解析、文件关联、提示词和模型调用。两者通过 JSON Lines 通信。

