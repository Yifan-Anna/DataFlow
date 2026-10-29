from __future__ import annotations

import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi

from backend.config import Settings


class LLMError(RuntimeError):
    pass


class OpenAICompatibleClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.settings.api_key:
            raise LLMError("未配置 DATAPILOT_API_KEY")

        payload = {
            "model": self.settings.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "parallel_tool_calls": False,
        }
        request = Request(
            f"{self.settings.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            with urlopen(request, timeout=self.settings.timeout_seconds, context=ssl_context) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            # Provider error bodies may echo credentials or request contents.
            raise LLMError(f"模型服务返回 HTTP {exc.code}") from exc
        except URLError as exc:
            raise LLMError("无法连接模型服务，请检查服务地址和网络配置") from exc
        except TimeoutError as exc:
            raise LLMError("模型服务请求超时") from exc

        try:
            return body["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("模型服务返回了无法识别的响应") from exc
