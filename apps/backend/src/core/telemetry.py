"""OpenTelemetry configuration — Phase 4 observability layer.

Provides distributed tracing across FastAPI, Celery, and Redis.
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "ecodream-backend")
_OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")


def init_tracing() -> trace.Tracer:
    """Initialize OpenTelemetry tracing. Returns a tracer instance."""
    resource = Resource(
        attributes={
            SERVICE_NAME: _SERVICE_NAME,
            SERVICE_VERSION: "0.1.0",
        }
    )
    provider = TracerProvider(resource=resource)

    if _OTEL_ENDPOINT:
        exporter = OTLPSpanExporter(endpoint=_OTEL_ENDPOINT)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return trace.get_tracer(_SERVICE_NAME)


def instrument_fastapi(app):
    """Auto-instrument FastAPI app with OpenTelemetry."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass  # Graceful degradation if instrumentation fails


def instrument_celery():
    """Auto-instrument Celery with OpenTelemetry."""
    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        CeleryInstrumentor().instrument()
    except Exception:
        pass


def instrument_redis():
    """Auto-instrument Redis with OpenTelemetry."""
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
    except Exception:
        pass
