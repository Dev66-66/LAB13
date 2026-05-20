import asyncio
import json
import logging

from opentelemetry import trace

from orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class LegalPipeline:
    """Выполняет четырёхшаговый pipeline юридической консультации."""

    def __init__(self, orchestrator: AgentOrchestrator) -> None:
        self.orchestrator = orchestrator

    async def execute(self, query: str) -> dict:
        """
        Последовательно запускает 4 агента pipeline.
        При TimeoutError повторяет весь pipeline до 3 раз с задержкой 2s.
        Все шаги покрываются одним OTel span.
        """
        tracer = trace.get_tracer("orchestrator")
        last_error: Exception | None = None

        for attempt in range(4):  # 1 начальная + 3 retry
            if attempt > 0:
                logger.warning("Pipeline retry %d/3 after timeout", attempt)
                await asyncio.sleep(2)
            try:
                with tracer.start_as_current_span("legal_pipeline.execute") as span:
                    span.set_attribute("query", query[:200])
                    span.set_attribute("attempt", attempt)

                    result1 = await self.orchestrator.send_task(
                        "analyze", {"query": query}, "legal.query.raw", timeout=30
                    )
                    result2 = await self.orchestrator.send_task(
                        "search",
                        json.loads(result1["output"]),
                        "legal.query.analyzed",
                        timeout=30,
                    )
                    result3 = await self.orchestrator.send_task(
                        "generate",
                        json.loads(result2["output"]),
                        "legal.docs.found",
                        timeout=60,
                    )
                    result4 = await self.orchestrator.send_task(
                        "check",
                        json.loads(result3["output"]),
                        "legal.answer.raw",
                        timeout=30,
                    )
                    return result4

            except asyncio.TimeoutError as exc:
                last_error = exc
                logger.error("Pipeline attempt %d timed out", attempt + 1)

        raise last_error  # type: ignore[misc]
