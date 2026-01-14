import structlog
from core.config import settings
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = structlog.get_logger()


class OpenTelemetrySetup:
    def __init__(self):
        self.tracer_provider = None
        self.meter_provider = None

    def setup(self):
        if not settings.TELEMETRY.otel_enabled:
            logger.info("otel_disabled")
            return

        resource = Resource(
            attributes={
                SERVICE_NAME: settings.TELEMETRY.otel_service_name,
                SERVICE_VERSION: settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
            }
        )

        self.tracer_provider = TracerProvider(resource=resource)

        if settings.TELEMETRY.otel_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=settings.TELEMETRY.otel_endpoint, insecure=True
            )
            self.tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        trace.set_tracer_provider(self.tracer_provider)

        prometheus_reader = PrometheusMetricReader()
        self.meter_provider = MeterProvider(
            resource=resource, metric_readers=[prometheus_reader]
        )
        metrics.set_meter_provider(self.meter_provider)

        logger.info("otel_configured")

    def instrument_app(self, app):
        FastAPIInstrumentor.instrument_app(app)
        logger.info("fastapi_instrumented")

    def instrument_db(self, engine):
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        logger.info("sqlalchemy_instrumented")


otel_setup = OpenTelemetrySetup()
