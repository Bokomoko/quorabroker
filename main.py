"""Entry point for the quorabroker service.

Responsibilities implemented in this initial skeleton:
- Load configuration from environment / .env
- Initialize structured logging
- Prepare Kafka consumer (stub if cluster unreachable)
- Provide async fetch capability using httpx
- Provide Mongo persistence stub (only if MONGO_URI provided)
- Graceful shutdown on SIGINT/SIGTERM

Future enhancements:
- Actual aiokafka consuming with backpressure
- Retry/backoff strategies for fetch and persistence
- Metrics and tracing
- Dead-letter handling
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
from typing import Any, Optional, Protocol, runtime_checkable, TypedDict, AsyncGenerator, Dict

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional dependency safety
    load_dotenv = None  # type: ignore

try:
    import structlog  # type: ignore
except ImportError:  # pragma: no cover
    structlog = None  # type: ignore

try:
    import httpx  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("httpx dependency missing; ensure 'httpx' is in project dependencies") from exc

try:
    from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
except ImportError:
    AsyncIOMotorClient = None  # type: ignore

try:
    from aiokafka import AIOKafkaConsumer  # type: ignore
except ImportError:
    AIOKafkaConsumer = None  # type: ignore

try:
    from pydantic import BaseModel, Field, HttpUrl  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("pydantic dependency missing; ensure 'pydantic' is in project dependencies") from exc


# Selenium (optional heavy dependency, only used when dynamic rendering required)
try:  # pragma: no cover - optional runtime
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.chrome.options import Options as ChromeOptions  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
except Exception:  # pragma: no cover
    webdriver = None  # type: ignore
    ChromeOptions = None  # type: ignore
    By = None  # type: ignore
    ChromeDriverManager = None  # type: ignore


class Config(BaseModel):  # type: ignore[misc]
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "quora.fetch.requests"
    mongo_uri: Optional[str] = None
    mongo_db: str = "quorabroker"
    mongo_collection: str = "pages"
    http_timeout_seconds: float = 15.0
    max_concurrent_fetches: int = 10
    user_agent: str = "quorabroker/0.1"
    log_level: str = "INFO"

    @classmethod
    def load(cls) -> "Config":
        if load_dotenv:  # pragma: no cover - simple IO
            load_dotenv(override=False)
        # Pull env with fallbacks to defined defaults.
        values = {
            "kafka_bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS") or cls.kafka_bootstrap_servers,
            "kafka_topic": os.getenv("KAFKA_TOPIC") or cls.kafka_topic,
            "mongo_uri": os.getenv("MONGO_URI") or None,
            "mongo_db": os.getenv("MONGO_DB") or cls.mongo_db,
            "mongo_collection": os.getenv("MONGO_COLLECTION") or cls.mongo_collection,
            "http_timeout_seconds": float(os.getenv("HTTP_TIMEOUT_SECONDS") or cls.http_timeout_seconds),
            "max_concurrent_fetches": int(os.getenv("MAX_CONCURRENT_FETCHES") or cls.max_concurrent_fetches),
            "user_agent": os.getenv("USER_AGENT") or cls.user_agent,
            "log_level": (os.getenv("LOG_LEVEL") or cls.log_level).upper(),
        }
        return cls(**values)


class FetchTask(BaseModel):  # type: ignore[misc]
    url: HttpUrl
    id: Optional[str] = Field(default=None, description="Optional external identifier")
    priority: Optional[int] = Field(default=None, ge=0, le=100)


@runtime_checkable
class LoggerLike(Protocol):
    def info(self, msg: str, *args: Any, **kw: Any) -> None: ...  # noqa: D401,E701
    def warning(self, msg: str, *args: Any, **kw: Any) -> None: ...  # noqa: E701
    def error(self, msg: str, *args: Any, **kw: Any) -> None: ...  # noqa: E701


def configure_logging(level: str) -> LoggerLike:  # type: ignore[override]
    if structlog is None:  # fallback
        import logging

        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        return logging.getLogger("quorabroker")
    structlog.configure(  # type: ignore[attr-defined]
        processors=[
            structlog.processors.add_log_level,  # type: ignore[attr-defined]
            structlog.processors.TimeStamper(fmt="iso"),  # type: ignore[attr-defined]
            structlog.processors.JSONRenderer(),  # type: ignore[attr-defined]
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog, level, structlog.INFO)
        ),  # type: ignore[attr-defined]
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger()  # type: ignore[attr-defined]


class PageDocument(TypedDict, total=False):
    _id: str
    url: str
    status_code: Optional[int]
    fetched_at: str
    latency_ms: float
    content_length: int
    html: Optional[str]
    error: Optional[str]
    meta: Dict[str, Any]
    question: Optional[str]
    answer: Optional[str]


class BrowserWorker:
    """Synchronous Selenium worker for extracting Quora question + answer text.

    Designed to be called sparingly because it blocks the event loop. A production
    system should offload this to a thread or separate process. For this skeleton
    we keep it simple and document the trade‑off.
    """

    QUESTION_SELECTOR = "div.puppeteer_test_question_title"
    ANSWER_P_SELECTOR = "p.q-text.qu-display--block.qu-wordBreak--break-word.qu-textAlign--start"

    def __init__(self, logger: LoggerLike):
        self._logger = logger
        if webdriver is None or ChromeOptions is None:
            raise RuntimeError("Selenium not available")
        opts = ChromeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        self._driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)  # type: ignore[arg-type]

    def extract(self, url: str) -> Dict[str, Optional[str]]:
        start = time.perf_counter()
        self._driver.get(url)
        # Basic waiting loop without explicit waits for simplicity
        question_text = None
        answer_text = None
        try:
            q_el = self._safe_find_css(self.QUESTION_SELECTOR)
            if q_el:
                question_text = q_el.text.strip()
            a_el = self._safe_find_css(self.ANSWER_P_SELECTOR)
            if a_el:
                answer_text = a_el.text.strip()
        except Exception as exc:  # pragma: no cover
            self._logger.warning("selenium_extract_issue", error=str(exc))
        finally:
            self._logger.info(
                "selenium_extracted",
                url=url,
                latency_ms=int((time.perf_counter() - start) * 1000),
                have_question=bool(question_text),
                have_answer=bool(answer_text),
            )
        return {"question": question_text, "answer": answer_text}

    def _safe_find_css(self, selector: str):  # type: ignore[no-untyped-def]
        try:
            return self._driver.find_element(By.CSS_SELECTOR, selector)  # type: ignore[arg-type]
        except Exception:
            return None

    def close(self) -> None:  # pragma: no cover
        try:
            self._driver.quit()
        except Exception:
            pass
class MongoStore:
    def __init__(self, cfg: Config, logger: LoggerLike):
        self._cfg: Config = cfg
        self._logger: LoggerLike = logger
        self._client: Any = None
        self._collection: Any = None
        if cfg.mongo_uri and AsyncIOMotorClient:
            self._client = AsyncIOMotorClient(cfg.mongo_uri)
            self._collection = self._client[cfg.mongo_db][cfg.mongo_collection]
        else:
            self._logger.warning("Mongo not configured or motor missing; persistence disabled")

    async def save_page(self, doc: PageDocument) -> None:
        if not self._collection:
            return
        await self._collection.insert_one(doc)

    async def close(self):  # pragma: no cover
        if self._client:
            self._client.close()


class Fetcher:
    def __init__(self, cfg: Config, logger: LoggerLike):
        self._cfg: Config = cfg
        self._logger: LoggerLike = logger
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=cfg.http_timeout_seconds, headers={"User-Agent": cfg.user_agent})

    async def fetch(self, task: FetchTask) -> PageDocument:
        started = time.perf_counter()
        try:
            resp = await self._client.get(str(task.url))
            latency_ms = (time.perf_counter() - started) * 1000
            return {
                "_id": task.id or os.urandom(8).hex(),
                "url": str(task.url),
                "status_code": resp.status_code,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "latency_ms": round(latency_ms, 2),
                "content_length": len(resp.content),
                "html": resp.text,
                "error": None,
                "meta": {"priority": task.priority},
            }
        except Exception as exc:  # pragma: no cover - general catch for skeleton
            latency_ms = (time.perf_counter() - started) * 1000
            self._logger.error("fetch_failed", url=str(task.url), error=str(exc))
            return {
                "_id": task.id or os.urandom(8).hex(),
                "url": str(task.url),
                "status_code": None,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "latency_ms": round(latency_ms, 2),
                "content_length": 0,
                "html": None,
                "error": str(exc),
                "meta": {"priority": task.priority},
            }

    async def close(self):  # pragma: no cover
        await self._client.aclose()


class KafkaConsumerWrapper:
    def __init__(self, cfg: Config, logger: LoggerLike):
        self._cfg: Config = cfg
        self._logger: LoggerLike = logger
        self._consumer: Optional[Any] = None
        self._running: bool = False

    async def start(self) -> None:
        if AIOKafkaConsumer is None:
            self._logger.warning("aiokafka not installed; using synthetic tasks")
            return
        self._consumer = AIOKafkaConsumer(
            self._cfg.kafka_topic,
            bootstrap_servers=self._cfg.kafka_bootstrap_servers,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._running = True
        self._logger.info("kafka_consumer_started", topic=self._cfg.kafka_topic)

    async def get_tasks(self) -> AsyncGenerator[FetchTask, None]:
        if self._consumer is None:
            # Synthetic generator for initial skeleton
            sample_urls = [
                "https://example.org",
                "https://www.python.org",
            ]
            for u in sample_urls:
                yield FetchTask(url=u)
            await asyncio.sleep(0.5)
            return
        try:
            while True:
                msg = await self._consumer.getone()
                try:
                    payload = json.loads(msg.value.decode("utf-8"))
                    task = FetchTask(**payload)
                    yield task
                except Exception as exc:
                    self._logger.error("invalid_message", error=str(exc))
        except asyncio.CancelledError:  # pragma: no cover
            pass

    async def stop(self) -> None:  # pragma: no cover
        if self._consumer:
            await self._consumer.stop()
            self._logger.info("kafka_consumer_stopped")


async def run() -> int:
    cfg = Config.load()
    logger = configure_logging(cfg.log_level)
    cfg_dump = cfg.model_dump() if hasattr(cfg, "model_dump") else cfg.dict()  # pydantic v1/v2 compatibility
    logger.info("service_starting", config={k: v for k, v in cfg_dump.items() if k != "mongo_uri"})

    consumer = KafkaConsumerWrapper(cfg, logger)
    browser_worker = BrowserWorker(logger) if webdriver else None
    fetcher = Fetcher(cfg, logger)
    store = MongoStore(cfg, logger)

    shutdown_event = asyncio.Event()

    def _signal_handler(sig: signal.Signals) -> None:  # pragma: no cover
        logger.info("signal_received", signal=sig.name)
        shutdown_event.set()

    for s in (signal.SIGINT, signal.SIGTERM):  # pragma: no cover
        try:
            asyncio.get_running_loop().add_signal_handler(s, lambda s=s: _signal_handler(s))
        except NotImplementedError:
            # Windows fallback (signals limited)
            pass

    await consumer.start()

    async def worker() -> None:
        async for task in consumer.get_tasks():
            page_doc = await fetcher.fetch(task)
            if browser_worker and page_doc.get("html") and "quora.com" in page_doc["url"]:
                try:
                    extracted = browser_worker.extract(page_doc["url"])  # blocking
                    page_doc.update(extracted)
                except Exception as exc:  # pragma: no cover
                    logger.warning("browser_extract_failed", error=str(exc))
            await store.save_page(page_doc)
            logger.info(
                "task_processed", url=page_doc["url"], status_code=page_doc["status_code"]
            )
            if shutdown_event.is_set():
                break

    try:
        await worker()
    finally:  # Cleanup
        await consumer.stop()
        await fetcher.close()
        await store.close()
        if browser_worker:
            try:
                browser_worker.close()
            except Exception:  # pragma: no cover
                pass
        logger.info("service_stopped")
    return 0


def main():  # pragma: no cover - thin wrapper
    try:
        exit_code = asyncio.run(run())
    except KeyboardInterrupt:  # pragma: no cover
        exit_code = 130
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
