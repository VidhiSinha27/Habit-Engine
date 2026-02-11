from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from src.domain.schemas import RawHealthEvent

class HealthDataProvider(ABC):
    """
    Abstract Base Class for all Health Data Ingestion sources.
    This allows us to swap Google Fit, Health Connect, or Apple Health
    without changing the downstream ML logic.
    """
    
    @abstractmethod
    def fetch_all_events(self, start_time: datetime, end_time: datetime) -> List[RawHealthEvent]:
        """
        Fetch all relevant health events (sleep, steps, exercise) within the window.
        """
        pass
    
    @abstractmethod
    def fetch_steps(self, start_time: datetime, end_time: datetime) -> List[RawHealthEvent]:
        pass

    @abstractmethod
    def fetch_sleep(self, start_time: datetime, end_time: datetime) -> List[RawHealthEvent]:
        pass
        
    @abstractmethod
    def fetch_exercise(self, start_time: datetime, end_time: datetime) -> List[RawHealthEvent]:
        pass
