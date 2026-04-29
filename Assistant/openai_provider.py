from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Generator, Literal, Optional

import httpx


class ProviderError(Exception):
    """Provider 相关基础异常"""
    pass


class TimeoutException(ProviderError):
    """请求超时异常"""
    pass


class APIError(ProviderError):
    """API 返回错误"""
    pass


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "developer"]
    content: str
    name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = {"role": self.role, "content": self.content}
        if self.name:
            data["name"] = self.name
        return data


@dataclass
class ChatCompletion:
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int]
    id: str

    @classmethod
    def from_response(cls, model: str, data: dict[str, Any]) -> ChatCompletion:
        return cls(
            id=data.get("id", "chatcmpl"),
            model=model,
            choices=data.get("choices", []),
            usage=data.get("usage", {}),
        )


class OpenAIProvider:
    """OpenAI 兼容 API 封装，支持标准 OpenAI 和自定义端点"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
        max_retries: int = 10,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[httpx.Client] = None

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout, headers=self._headers)
        return self._client

    def chat_completions(
        self,
        model: str,
        messages: list[Message | dict[str, Any]],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        stop: Optional[list[str]] = None,
        **kwargs,
    ) -> ChatCompletion | Generator[str, None, None]:
        """发送聊天补全请求"""
        payload = {
            "model": model,
            "messages": [
                m.to_dict() if isinstance(m, Message) else m for m in messages
            ],
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if stop:
            payload["stop"] = stop
        payload.update(kwargs)

        url = f"{self.base_url}/chat/completions"

        for attempt in range(self.max_retries):
            try:
                if stream:
                    return self._stream_request(url, payload)
                response = self.client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return ChatCompletion.from_response(model, data)
            except httpx.TimeoutException as e:
                if attempt == self.max_retries - 1:
                    raise TimeoutException(f"请求超时（已重试{self.max_retries}次）: {e}")
                time.sleep(self.retry_delay * (2 ** attempt))
            except httpx.HTTPStatusError as e:
                raise APIError(f"API 错误: {e.response.status_code} - {e}")

    def _stream_request(
        self, url: str, payload: dict[str, Any]
    ) -> Generator[str, None, None]:
        """处理流式请求"""
        with httpx.stream("POST", url, json=payload, headers=self._headers, timeout=self.timeout) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break

                data = json.loads(data_str)
                delta = data.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content

    def completions(
        self,
        model: str,
        prompt: str | list[str],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """发送文本补全请求"""
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)

        url = f"{self.base_url}/completions"
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def list_models(self) -> dict[str, Any]:
        """列出可用模型"""
        url = f"{self.base_url}/models"
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> OpenAIProvider:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


def create_provider(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    provider: Literal["openai", "azure", "claude", "custom"] = "openai",
    **kwargs,
) -> OpenAIProvider:
    """工厂函数：创建不同类型的 OpenAI 兼容 provider"""
    if provider == "openai":
        return OpenAIProvider(api_key=api_key, base_url=base_url or "https://api.openai.com/v1", **kwargs)
    elif provider == "azure":
        if not base_url:
            raise ValueError("Azure OpenAI requires base_url (endpoint)")
        return OpenAIProvider(api_key=api_key, base_url=base_url, **kwargs)
    else:
        if not base_url:
            raise ValueError("Custom provider requires base_url")
        return OpenAIProvider(api_key=api_key, base_url=base_url, **kwargs)
