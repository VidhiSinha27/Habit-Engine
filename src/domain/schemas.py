from enum import Enum
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class EventType(str, Enum):
    STEPS = "steps"
    SLEEP = "sleep"
    EXERCISE = "exercise"
    HEART_RATE = "heart_rate"

class HealthSource(str, Enum):
    GOOGLE_FIT = "google_fit"
    HEALTH_CONNECT = "health_connect"
    APPLE_HEALTH = "apple_health"
    SAMSUNG_HEALTH = "samsung_health"
    MOCK = "mock"

class RawHealthEvent(BaseModel):
    """
    Represents a raw atomic event from a health provider.
    Do NOT aggregate here. Store raw start/end times.
    """
    event_id: str
    event_type: EventType
    source: HealthSource
    start_time: datetime
    end_time: datetime
    value: float  # For steps, this is count. For others, maybe specific metric.
    metadata: Dict[str, Any] = {}
    
    # Validation config
    model_config = ConfigDict(from_attributes=True)

class DailyBehavior(BaseModel):
    """
    Canonical Daily State.
    One row per user per day.
    """
    date: date
    
    # Physical Signals
    total_steps: int
    exercise_minutes: float
    exercise_done: bool
    exercise_start_time: Optional[datetime] = None  # First session of day
    
    sleep_start_time: Optional[datetime] = None
    sleep_end_time: Optional[datetime] = None
    sleep_duration_minutes: float = 0.0
    
    sedentary_minutes: float = 0.0 # Proxy derived from lack of steps/movement
    data_quality_score: float = 1.0 # 1.0 = perfect, 0.0 = missing
    data_missing_flag: bool = False

    # Cognitive Context (Optional / Derived later)
    mental_load_score: Optional[int] = None # 1-5
    energy_level: Optional[str] = None # low, medium, high
    stress_detected: bool = False
    
    # Behavioral Signals (Derived)
    streak_active: bool = False
    days_since_last_miss: int = 0
    
    model_config = ConfigDict(from_attributes=True)
