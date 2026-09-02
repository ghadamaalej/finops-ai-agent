import logging
import time
from concurrent.futures import ThreadPoolExecutor

from langchain_core.messages import AIMessage
from langchain_openai import AzureChatOpenAI

logger = logging.getLogger(__name__)

from config.settings import settings

AZURE_OPENAI_ENDPOINT = settings.AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY = settings.AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT = settings.AZURE_OPENAI_DEPLOYMENT
LLM_TIMEOUT_SECONDS = settings.AZURE_OPENAI_TIMEOUT_SECONDS

_invocation_counts: dict[str, int] = {}


class LLMTimeoutError(RuntimeError):
    pass

llm = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT,
    api_version="2024-12-01-preview",
    timeout=LLM_TIMEOUT_SECONDS,
    max_retries=2,
)


def ask_llm(prompt: str, request_id: str | None = None) -> str:
    started_at = time.perf_counter()

    if request_id:
        _invocation_counts[request_id] = (
            _invocation_counts.get(request_id, 0) + 1
        )

    invocation_count = _invocation_counts.get(request_id, 1)

    logger.info(
        "LLM request start: request_id=%s invocation_count=%s "
        "node=chat provider=%s model=%s prompt_chars=%s "
        "timeout_seconds=%.2f",
        request_id,
        invocation_count,
        "azure_openai",
        AZURE_OPENAI_DEPLOYMENT,
        len(prompt),
        LLM_TIMEOUT_SECONDS,
    )

    print("\n===== LLM REQUEST =====")
    print(
        f"request_id={request_id} "
        f"invocation_count={invocation_count} "
        f"provider=azure_openai "
        f"model={AZURE_OPENAI_DEPLOYMENT} "
        f"prompt_length={len(prompt)} chars "
        f"timeout={LLM_TIMEOUT_SECONDS}s"
    )

    response = None

    try:
        executor = ThreadPoolExecutor(max_workers=1)

        future = executor.submit(
            llm.invoke,
            prompt,
        )

        try:
            response = future.result(
                timeout=LLM_TIMEOUT_SECONDS
            )
        finally:
            executor.shutdown(
                wait=False,
                cancel_futures=True,
            )

    except TimeoutError as exc:
        duration = time.perf_counter() - started_at

        logger.exception(
            "LLM request timed out: request_id=%s "
            "provider=%s model=%s duration_seconds=%.2f",
            request_id,
            "azure_openai",
            AZURE_OPENAI_DEPLOYMENT,
            duration,
        )

        raise LLMTimeoutError(
            f"LLM request timed out after "
            f"{LLM_TIMEOUT_SECONDS:.1f}s "
            f"for model={AZURE_OPENAI_DEPLOYMENT}"
        ) from exc

    except Exception:
        duration = time.perf_counter() - started_at

        logger.exception(
            "LLM request failed: request_id=%s "
            "provider=%s model=%s duration_seconds=%.2f",
            request_id,
            "azure_openai",
            AZURE_OPENAI_DEPLOYMENT,
            duration,
        )

        raise

    duration = time.perf_counter() - started_at

    logger.info(
        "LLM response received: request_id=%s "
        "provider=%s model=%s duration_seconds=%.2f type=%s",
        request_id,
        "azure_openai",
        AZURE_OPENAI_DEPLOYMENT,
        duration,
        type(response).__name__,
    )

    print("\n===== LLM RAW OBJECT =====")
    print(response)

    print(
        f"request_id={request_id} "
        f"llm_provider=azure_openai "
        f"model={AZURE_OPENAI_DEPLOYMENT} "
        f"duration_seconds={duration:.2f}"
    )

    if isinstance(response, AIMessage):

        content = (
            response.content or ""
        ).strip()

        metadata = (
            response.response_metadata or {}
        )

        logger.info(
            "LLM response metadata: request_id=%s "
            "provider=%s model=%s metadata=%s",
            request_id,
            "azure_openai",
            AZURE_OPENAI_DEPLOYMENT,
            metadata,
        )

        if not content:
            raise RuntimeError(
                "LLM returned an empty response"
            )

        return content

    content = str(
        response or ""
    ).strip()

    if not content:
        raise RuntimeError(
            "LLM returned an empty response"
        )

    return content