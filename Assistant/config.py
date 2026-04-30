import os


def _getenv(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# LLM 配置
LLM_API_KEY = _getenv("LLM_API_KEY")
LLM_BASE_URL = _getenv("LLM_BASE_URL")
LLM_MODEL = _getenv("LLM_MODEL")
LLM_TIMEOUT = float(_getenv("LLM_TIMEOUT", "60.0"))
LLM_MAX_RETRIES = int(_getenv("LLM_MAX_RETRIES", "10"))

# Embedding 配置
EMBED_API_KEY = _getenv("EMBED_API_KEY")
EMBED_BASE_URL = _getenv("EMBED_BASE_URL")
EMBED_MODEL = _getenv("EMBED_MODEL")
EMBED_TIMEOUT = float(_getenv("EMBED_TIMEOUT", "60.0"))
EMBED_N_DIMS = int(_getenv("EMBED_N_DIMS", "4096"))

# Reranker 配置
RERANK_API_KEY = _getenv("RERANK_API_KEY")
RERANK_BASE_URL = _getenv("RERANK_BASE_URL")
RERANK_MODEL = _getenv("RERANK_MODEL")
RERANK_TIMEOUT = float(_getenv("RERANK_TIMEOUT", "60.0"))

# 向量数据库配置
VECTOR_DB_PATH = _getenv("VECTOR_DB_PATH", "knowledge.db")

# Agent 配置
AGENT_MAX_LOOP = int(_getenv("AGENT_MAX_LOOP", "10"))
AGENT_MAX_MESSAGES = int(_getenv("AGENT_MAX_MESSAGES", "20"))

# 日志配置
LOG_LEVEL = int(_getenv("LOG_LEVEL", "10"))
