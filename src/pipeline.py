import logging
from db import get_engine
from ingest import run_ingestion
from quality import run_quality_checks
from transform import run_transforms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("=" * 50)
    logger.info("Pipeline started.")

    engine = get_engine()

    logger.info("Step 1/3: Ingestion")
    run_ingestion()

    logger.info("Step 2/3: Quality checks")
    run_quality_checks(engine)

    logger.info("Step 3/3: Transforms")
    run_transforms(engine)

    logger.info("Pipeline complete.")
    logger.info("=" * 50)


if __name__ == "__main__":
    run_pipeline()