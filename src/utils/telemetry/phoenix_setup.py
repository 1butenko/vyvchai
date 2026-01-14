import phoenix as px
import structlog
from core.config import settings
from openinference.instrumentation.langchain import LangChainInstrumentor

logger = structlog.get_logger()


class PhoenixTelemetry:
    def __init__(self):
        self.session = None
        self.instrumentors = []

    def setup(self):
        if not settings.TELEMETRY.phoenix_enabled:
            logger.info("phoenix_disabled")
            return

        try:
            self.session = px.launch_app(
                host="0.0.0.0",
                port=6006,
                project_name=settings.telemetry.phoenix_project_name,
            )

            langchain_instrumentor = LangChainInstrumentor()
            langchain_instrumentor.instrument()
            self.instrumentors.append(langchain_instrumentor)

            logger.info(
                "phoenix_started",
                url="http://localhost:6006",
                project=settings.telemetry.phoenix_project_name,
            )

        except Exception as e:
            logger.error("phoenix_setup_failed", error=str(e))

    def shutdown(self):
        for instrumentor in self.instrumentors:
            instrumentor.uninstrument()

        if self.session:
            px.close_app()

        logger.info("phoenix_shutdown")


phoenix_telemetry = PhoenixTelemetry()
