"""Compatibility wrapper around the November 2022 LangChain API."""

from __future__ import annotations

import os


def generate_code(prompt: str, model_name: str = "text-davinci-003", base_url: str | None = None) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("未设置 OPENAI_API_KEY")

    try:
        from langchain import LLMChain, OpenAI, PromptTemplate
    except ImportError as exc:
        raise RuntimeError("未安装 Python 依赖，请运行 pip install -r python/requirements.txt") from exc

    if base_url:
        os.environ["OPENAI_API_BASE"] = base_url
    kwargs = {
        "model_name": model_name,
        "temperature": 0,
        "openai_api_key": api_key,
    }
    if base_url:
        kwargs["openai_api_base"] = base_url
    try:
        llm = OpenAI(**kwargs)
    except TypeError:
        # A few early patch releases read the base URL only from the environment.
        kwargs.pop("openai_api_base", None)
        llm = OpenAI(**kwargs)

    prompt_template = PromptTemplate(input_variables=["input"], template="{input}")
    chain = LLMChain(llm=llm, prompt=prompt_template)
    return str(chain.run(input=prompt))

