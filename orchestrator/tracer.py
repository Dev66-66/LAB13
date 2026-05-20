import os
from urllib.parse import urlparse

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_tracer(service_name: str) -> TracerProvider:
    """
    Инициализирует глобальный OpenTelemetry TracerProvider с OTLP HTTP-экспортёром.
    Извлекает хост из JAEGER_ENDPOINT и использует OTLP-порт 4318.
    Вызывать один раз при старте сервиса.
    """
    raw = os.getenv("JAEGER_ENDPOINT", "http://jaeger:4318")
    parsed = urlparse(raw)
    otlp_url = f"http://{parsed.hostname}:4318/v1/traces"

    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
    })
    exporter = OTLPSpanExporter(endpoint=otlp_url)
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider
