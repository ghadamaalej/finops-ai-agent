import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from config.settings import settings
logger = logging.getLogger(__name__)

# Ollama is optional for interactive chat.  A provider stall must not hold an API
# request open while the deterministic evidence path is already available.
LLM_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "250"))

# Request-level diagnostics are deliberately emitted here rather than in the UI:
# one request should have one explicit invocation and a bounded lifetime.
_invocation_counts: dict[str, int] = {}

class LLMTimeoutError(RuntimeError):
    pass
llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    reasoning=False,
    temperature=0,
    num_ctx=8192,
    # Reasoning responses are intentionally compact; this is only a safeguard
    # against truncating otherwise-valid JSON, not a substitute for bounded prompts.
    num_predict=1024,
    format="json",
    client_kwargs={"timeout": LLM_TIMEOUT_SECONDS},
)


def ask_llm(prompt: str, request_id: str | None = None) -> str:
    started_at = time.perf_counter()
    timeout_seconds = LLM_TIMEOUT_SECONDS
    if request_id:
        _invocation_counts[request_id] = _invocation_counts.get(request_id, 0) + 1
    invocation_count = _invocation_counts.get(request_id, 1)

    logger.info(
        "LLM request start: request_id=%s invocation_count=%s node=chat provider=%s model=%s prompt_chars=%s stream=%s format=%s timeout_seconds=%.2f",
        request_id,
        invocation_count,
        "ollama",
        llm.model,
        len(prompt),
        False,
        llm.format,
        timeout_seconds,
    )
    logger.info(
        request_id,
        "ollama",
        llm.model,
        len(prompt),
        False,
        llm.format,
    )
    print("\n===== LLM REQUEST =====")
    print(f"request_id={request_id} invocation_count={invocation_count} provider=ollama model={llm.model} prompt_length={len(prompt)} chars timeout={timeout_seconds}s")

    response = None
    try:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(llm.invoke, prompt, stream=False, format="json")
        try:
            response = future.result(timeout=timeout_seconds)
        finally:
            # Do not wait for a blocked provider thread after the timeout fires.
            executor.shutdown(wait=False, cancel_futures=True)
    except TimeoutError as exc:
        duration = time.perf_counter() - started_at
        logger.exception(
            "LLM request timed out: request_id=%s provider=%s model=%s duration_seconds=%.2f timeout_seconds=%.2f",
            request_id,
            "ollama",
            llm.model,
            duration,
            timeout_seconds,
        )
        raise LLMTimeoutError(
            f"LLM request timed out after {timeout_seconds:.1f}s for model={llm.model}"
        ) from exc
    except Exception as exc:
        duration = time.perf_counter() - started_at
        logger.exception(
            "LLM request failed: request_id=%s provider=%s model=%s duration_seconds=%.2f",
            request_id,
            "ollama",
            llm.model,
            duration,
        )
        raise

    duration = time.perf_counter() - started_at
    logger.info(
        "LLM response received: request_id=%s provider=%s model=%s duration_seconds=%.2f type=%s",
        request_id,
        "ollama",
        llm.model,
        duration,
        type(response).__name__,
    )
    print("\n===== LLM RAW OBJECT =====")
    print(response)
    print(f"request_id={request_id} llm_provider=ollama model={llm.model} duration_seconds={duration:.2f}")

    # --------------------------------------------------------
    # Detect LangChain AIMessage
    # --------------------------------------------------------

    if isinstance(
        response,
        AIMessage,
    ):

        content = (
            response.content
            or ""
        ).strip()

        metadata = (
            response.response_metadata
            or {}
        )
        logger.info(
            "LLM response metadata: request_id=%s provider=%s model=%s metadata=%s",
            request_id,
            "ollama",
            llm.model,
            metadata,
        )

        done_reason = metadata.get(
            "done_reason"
        )

        if not content:

            if done_reason == "length":

                raise RuntimeError(
                    "LLM reached output token limit "
                    "before producing JSON"
                )

            raise RuntimeError(
                "LLM returned an empty response"
            )

        return content

    # --------------------------------------------------------
    # Generic response
    # --------------------------------------------------------

    content = str(
        response or ""
    ).strip()

    if not content:

        raise RuntimeError(
            "LLM returned an empty response"
        )

    return content