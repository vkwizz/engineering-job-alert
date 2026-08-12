from abc import ABC, abstractmethod
from typing import List
from src.job_alert.normalization.schemas import NormalizedJob

class JobSource(ABC):
    @abstractmethod
    def fetch_jobs(self, query: str, location: str) -> List[NormalizedJob]:
        pass
