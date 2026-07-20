from backend.domain.ports import IMLService
from backend.ml.model import MLService, ml_service


def get_ml_service() -> IMLService:
    return ml_service
