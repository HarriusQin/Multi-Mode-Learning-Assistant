from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx


class EmbeddingError(Exception):
    """Embedding 相关基础异常"""
    pass


class EmbeddingTimeoutException(EmbeddingError):
    """请求超时异常"""
    pass


class EmbeddingAPIError(EmbeddingError):
    """API 返回错误"""
    pass


@dataclass
class EmbeddingUsage:
    prompt_tokens: int
    total_tokens: int


@dataclass
class EmbeddingData:
    index: int
    embedding: list[float]
    object: str = "embedding"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmbeddingData:
        return cls(
            index=data.get("index", 0),
            embedding=data.get("embedding", []),
            object=data.get("object", "embedding"),
        )


@dataclass
class EmbeddingResponse:
    object: str
    data: list[EmbeddingData]
    model: str
    usage: EmbeddingUsage

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> EmbeddingResponse:
        usage_data = data.get("usage", {})
        return cls(
            object=data.get("object", "list"),
            data=[EmbeddingData.from_dict(d) for d in data.get("data", [])],
            model=data.get("model", ""),
            usage=EmbeddingUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ),
        )


class OpenAIEmbeddingProvider:
    """OpenAI 兼容 Embedding API 封装"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
        max_retries: int = 10,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[httpx.Client] = None

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _new_client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout, headers=self._headers, trust_env=False)

    @property
    def client(self) -> httpx.Client:
        return self._new_client()

    def embed(
        self,
        model: str,
        input: str | list[str],
        *,
        encoding_format: str = "float",
        dimensions: Optional[int] = None,
        **kwargs,
    ) -> EmbeddingResponse:
        """发送 embedding 请求"""
        payload: dict[str, Any] = {
            "model": model,
            "input": input,
            "encoding_format": encoding_format,
        }
        if dimensions is not None:
            payload["dimensions"] = dimensions
        payload.update(kwargs)

        url = f"{self.base_url}/embeddings"

        for attempt in range(self.max_retries):
            try:
                response = self.client.post(url, json=payload)
                response.raise_for_status()
                return EmbeddingResponse.from_response(response.json())
            except httpx.TimeoutException as e:
                if attempt == self.max_retries - 1:
                    raise EmbeddingTimeoutException(
                        f"请求超时（已重试{self.max_retries}次）: {e}"
                    )
                time.sleep(self.retry_delay * (2 ** attempt))
            except httpx.HTTPStatusError as e:
                raise EmbeddingAPIError(f"API 错误: {e.response.status_code} - {e}")

    def embed_single(
        self,
        model: str,
        text: str,
        *,
        encoding_format: str = "float",
        dimensions: Optional[int] = None,
        **kwargs,
    ) -> list[float]:
        """发送单条 embedding 请求，返回 embedding 向量"""
        response = self.embed(
            model,
            text,
            encoding_format=encoding_format,
            dimensions=dimensions,
            **kwargs,
        )
        if not response.data:
            raise EmbeddingError("响应中无 embedding 数据")
        return response.data[0].embedding

    def embed_batch(
        self,
        model: str,
        texts: list[str],
        *,
        encoding_format: str = "float",
        dimensions: Optional[int] = None,
        **kwargs,
    ) -> list[list[float]]:
        """发送批量 embedding 请求，返回 embedding 向量列表"""
        response = self.embed(
            model,
            texts,
            encoding_format=encoding_format,
            dimensions=dimensions,
            **kwargs,
        )
        # 按 index 排序保证顺序
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [d.embedding for d in sorted_data]

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> OpenAIEmbeddingProvider:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
