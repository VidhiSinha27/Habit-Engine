from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from src.domain.schemas import DailyBehavior

class RecommendationType(str, Enum):
    MAINTAIN = "maintain"             # Keep doing what you're doing
    SCALE_DOWN = "scale_down"         # Reduce difficulty (pre-burnout)
    RECOVERY = "recovery"             # Active recovery day
    ANCHORING = "anchoring"           # Focus on timing, not intensity
    CELEBRATION = "celebration"       # Milestone or identity reinforcement

class EngineResponse(BaseModel):
    user_id: str
    date: str
    
    # ML Outputs
    adherence_probability: float
    burnout_risk_score: float
    is_anomaly: bool
    
    # Decision
    recommendation_type: RecommendationType
    message_title: str
    message_body: str
    suggested_action: str
    
    # Explainability
    why_this_recommendation: List[str]

class SimulationParams(BaseModel):
    history_days: int = 90
    avg_steps: int = 8000
    steps_volatility: float = 0.3
    exercise_freq: int = 3
    avg_sleep_hours: float = 7.5
    sleep_volatility: float = 0.2

class TrainingResponse(BaseModel):
    message: str
    history_points: int
    adherence_accuracy: float
    burnout_c_index: float
    history: List[DailyBehavior]

class HistoryTrainRequest(BaseModel):
    history: List[DailyBehavior]

class DailyInput(BaseModel):
    steps: int
    sleep_hours: float
    exercise_minutes: int
