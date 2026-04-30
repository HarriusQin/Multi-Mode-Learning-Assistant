from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx


class RerankerError(Exception):
    """Reranker 相关基础异常"""
    pass


class RerankerTimeoutException(RerankerError):
    """请求超时异常"""
    pass


class RerankerAPIError(RerankerError):
    """API 返回错误"""
    pass


@dataclass
class RerankResult:
    index: int
    relevance_score: float
    text: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RerankResult:
        return cls(
            index=data.get("index", 0),
            relevance_score=data.get("relevance_score", 0.0),
            text=data.get("text", ""),
        )


@dataclass
class RerankResponse:
    results: list[RerankResult]
    model: str
    usage: Optional[dict[str, int]] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RerankResponse:
        return cls(
            results=[RerankResult.from_dict(r) for r in data.get("results", [])],
            model=data.get("model", ""),
            usage=data.get("usage"),
        )


class VLLMRerankerProvider:
    """vLLM Reranker API 封装

    vLLM reranker 通常使用 /rerank 端点，接收 query 和 documents，
    返回每个 document 的相关性分数。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 60.0,
        max_retries: int = 10,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key or os.getenv("VLLM_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[httpx.Client] = None

    @property
    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout, headers=self._headers)
        return self._client

    def rerank(
        self,
        model: str,
        query: str,
        documents: list[str],
        *,
        top_n: Optional[int] = None,
        return_documents: bool = True,
        **kwargs,
    ) -> RerankResponse:
        """发送 rerank 请求

        Args:
            model: 模型名称
            query: 查询文本
            documents: 文档列表
            top_n: 返回前 N 个结果，None 则返回全部
            return_documents: 是否在结果中返回文档内容
            **kwargs: 其他参数
        """
        payload: dict[str, Any] = {
            "model": model,
            "query": query,
            "documents": documents,
            "return_documents": return_documents,
        }
        if top_n is not None:
            payload["top_n"] = top_n
        payload.update(kwargs)

        url = f"{self.base_url}/rerank"

        for attempt in range(self.max_retries):
            try:
                response = self.client.post(url, json=payload)
                response.raise_for_status()
                return RerankResponse.from_dict(response.json())
            except httpx.TimeoutException as e:
                if attempt == self.max_retries - 1:
                    raise RerankerTimeoutException(
                        f"请求超时（已重试{self.max_retries}次）: {e}"
                    )
                time.sleep(self.retry_delay * (2 ** attempt))
            except httpx.HTTPStatusError as e:
                raise RerankerAPIError(f"API 错误: {e.response.status_code} - {e}")

    def rerank_with_scores(
        self,
        model: str,
        query: str,
        documents: list[str],
        *,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        **kwargs,
    ) -> list[tuple[str, float]]:
        """发送 rerank 请求，返回 (文档, 分数) 列表

        Args:
            model: 模型名称
            query: 查询文本
            documents: 文档列表
            top_k: 只返回分数最高的前 K 个
            score_threshold: 只返回分数高于此阈值的结果
            **kwargs: 其他参数
        """
        response = self.rerank(model, query, documents, **kwargs)

        results = [
            (r.text, r.relevance_score)
            for r in sorted(response.results, key=lambda x: x.relevance_score, reverse=True)
        ]

        if top_k is not None:
            results = results[:top_k]

        if score_threshold is not None:
            results = [(doc, score) for doc, score in results if score >= score_threshold]

        return results

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> VLLMRerankerProvider:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
