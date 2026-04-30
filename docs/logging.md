# 日志系统

统一的日志管理，支持控制台输出和文件轮转。

## 初始化

```python
from Assistant.logging_config import init_logging, get_logger

# 初始化日志系统（通常在程序入口调用一次）
init_logging(level=10)  # DEBUG level

# 获取 logger
logger = get_logger("module_name")
```

### 日志级别

| 级别 | 值 | 说明 |
|------|-----|------|
| `DEBUG` | 10 | 调试信息 |
| `INFO` | 20 | 一般信息 |
| `WARNING` | 30 | 警告信息 |
| `ERROR` | 40 | 错误信息 |
| `CRITICAL` | 50 | 严重错误 |

## 日志格式

```
2026-05-01 00:30:15 [   DEBUG] [module] 日志消息
2026-05-01 00:30:15 [    INFO] [module] 日志消息
2026-05-01 00:30:15 [WARNING] [module] 日志消息
2026-05-01 00:30:15 [   ERROR] [module] 日志消息
```

## 日志文件

日志保存在 `logs/` 目录下：

```
logs/
├── app.log       # 主日志文件
├── app.log.1     # 轮转备份
├── app.log.2     # 更旧的备份
└── ...
```

### 轮转配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_bytes` | 10MB | 单个日志文件最大大小 |
| `backup_count` | 5 | 保留的备份文件数量 |

## 使用示例

```python
from Assistant.logging_config import get_logger

# 在模块中获取 logger
logger = get_logger("my_module")

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

## 日志关闭

```python
from Assistant.logging_config import get_logger

logger = get_logger("my_module")
logger.shutdown()
```

## 与标准 logging 的区别

项目使用 `LogManager` 单例模式管理日志：

- **统一配置**: 所有模块共享相同的日志配置
- **自动轮转**: 避免日志文件过大
- **分类输出**: 每个模块有独立的日志文件

## 下一步

- [Agent 核心](agent.md) - 了解 Agent 如何记录日志
- [Provider 封装](providers.md) - 了解 Provider 如何记录日志
