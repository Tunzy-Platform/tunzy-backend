import logging.config
import logging
from app.core import config


class ServiceNameFilter(logging.Filterer):
    """Read service name from `setting.service_name`"""

    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service
        return True


def setup_logging(service_name: str) -> None:
    logging.config.dictConfig(config.LOGGING)
    logger = logging.getLogger(__name__)
    logger.info("Logging Start")

def get_logger(service_name:str) -> logging.Logger:
    return logging.getLogger(service_name)