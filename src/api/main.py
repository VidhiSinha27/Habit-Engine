import sys
import os

# Add project root to python path to allow imports from 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import uvicorn

from src.processing.features import FeatureEngineer
from src.models.adherence import AdherenceModel
from src.models.burnout import BurnoutRiskModel
from src.processing.recommender import RecommendationEngine
from src.domain.schemas import DailyBehavior
from src.domain.api_schemas import (
    EngineResponse, SimulationParams, TrainingResponse, DailyInput, HistoryTrainRequest
)

app = FastAPI(title="Habit Engine API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STATE
class EngineState:
    def __init__(self):
        self.history_data: List[DailyBehavior] = []
        self.df_history: pd.DataFrame = pd.DataFrame()
        self.df_features: pd.DataFrame = pd.DataFrame()
        
        # Components
        self.engineer = FeatureEngineer()
        self.adherence_model = AdherenceModel()
        self.burnout_model = BurnoutRiskModel()
        self.recommender = RecommendationEngine()
        
        self.is_trained = False

state = EngineState()

# HELPER
def generate_history(params: SimulationParams) -> List[DailyBehavior]:
    data = []
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=params.history_days)
    
    # Probabilities
    ex_prob = params.exercise_freq / 7.0
    mean_ex_dur = 45 # hardcoded for simplicity or logic reuse
    
    for i in range(params.history_days):
        current_date = start_date + timedelta(days=i)
        
        # Steps
        steps = int(np.random.normal(params.avg_steps, params.avg_steps * params.steps_volatility))
        steps = max(0, steps)
        
        # Exercise
        if np.random.random() < ex_prob:
            ex_done = True
            ex_mins = max(10, int(np.random.normal(mean_ex_dur, mean_ex_dur * 0.2)))
        else:
            ex_done = False
            ex_mins = 0
            
        # Sleep
        sleep_mins = max(0, int(np.random.normal(params.avg_sleep_hours * 60, params.avg_sleep_hours * 60 * params.sleep_volatility)))
        
        record = DailyBehavior(
            date=current_date,
            total_steps=steps,
            exercise_minutes=ex_mins,
            exercise_done=ex_done,
            sleep_duration_minutes=sleep_mins,
            data_missing_flag=False,
            sleep_start_time=None,
            sleep_end_time=None,
            exercise_start_time=None
        )
        data.append(record)
        
    return data

@app.post("/simulate-train", response_model=TrainingResponse)
def simulate_and_train(params: SimulationParams):
    try:
        # 1. Generate
        state.history_data = generate_history(params)
        state.df_history = pd.DataFrame([d.model_dump() for d in state.history_data])
        
        # 2. Features
        state.df_features = state.engineer.enhance(state.history_data)
        
        # 3. Train
        # Adherence
        try:
            metrics_adh = state.adherence_model.train(state.df_features)
            acc = metrics_adh.get('accuracy', 0.0)
        except:
             acc = 0.0

        # Burnout
        try:
            metrics_burn = state.burnout_model.train(state.df_features)
            c_index = metrics_burn.get('concordance', 0.0)
        except:
             c_index = 0.0
        
        state.is_trained = True
        
        return TrainingResponse(
            message="Training Complete",
            history_points=len(state.history_data),
            adherence_accuracy=acc,
            burnout_c_index=c_index,
            history=state.history_data
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train-custom", response_model=TrainingResponse)
def train_custom(request: HistoryTrainRequest):
    try:
        # 1. Load Provided History
        # Ensure we have date objects, pydantic handles this mostly but pandas needs help
        state.history_data = request.history
        state.df_history = pd.DataFrame([d.model_dump() for d in state.history_data])
        
        # 2. Features
        state.df_features = state.engineer.enhance(state.history_data)
        
        # 3. Train
        metrics_adh = {}
        metrics_burn = {}
        
        # Adherence
        try:
            metrics_adh = state.adherence_model.train(state.df_features)
            acc = metrics_adh.get('accuracy', 0.0)
        except:
             acc = 0.0

        # Burnout
        try:
            metrics_burn = state.burnout_model.train(state.df_features)
            c_index = metrics_burn.get('concordance', 0.0)
        except:
             c_index = 0.0
        
        state.is_trained = True
        
        return TrainingResponse(
            message="Training Complete (Custom Data)",
            history_points=len(state.history_data),
            adherence_accuracy=acc,
            burnout_c_index=c_index,
            history=state.history_data
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict", response_model=EngineResponse)
def predict(input: DailyInput):
    if not state.is_trained:
        raise HTTPException(status_code=400, detail="Models not trained. Call /simulate-train first.")
    
    try:
        # Create Today's Record
        today = datetime.now().date()
        today_record = DailyBehavior(
            date=today,
            total_steps=input.steps,
            exercise_minutes=input.exercise_minutes,
            exercise_done=(input.exercise_minutes > 10),
            sleep_duration_minutes=input.sleep_hours * 60,
            data_missing_flag=False
        )
        
        # Append
        full_list = state.history_data + [today_record]
        df_full = state.engineer.enhance(full_list)
        today_features = df_full.iloc[[-1]]
        feature_row = df_full.iloc[-1].to_dict()
        
        # Calculate Initial Motivation (Streak-based)
        # Find start of current streak: Last time rolling_misses_3d was 3 (i.e., 3 consecutive misses)
        # or simpler: Calculate rolling sum of exercise_done. If 0 over window 3, that's a break.
        
        # 1. Identify breaks
        rolling_activity = df_full['exercise_done'].astype(int).rolling(window=3).sum()
        break_points = rolling_activity[rolling_activity == 0].index
        
        # 2. Slice current streak
        if len(break_points) > 0 and break_points[-1] < df_full.index[-1]:
            last_break_date = break_points[-1]
            # Streak starts strictly after the break
            current_streak_df = df_full.loc[last_break_date:].iloc[1:]
        else:
            current_streak_df = df_full
            
        # 3. Average first 3 days
        if len(current_streak_df) > 0:
            count = min(3, len(current_streak_df))
            init_motivation = current_streak_df['exercise_minutes'].iloc[:count].mean()
        else:
            init_motivation = 30.0 # Default if empty (shim)

        # Predictions
        # Adherence
        try:
            adh_prob = state.adherence_model.predict_next_day_proba(today_features)
        except:
            adh_prob = 0.5
            
        # Burnout
        risk_input = {
            'avg_sleep_consistency': feature_row.get('sleep_consistency_score', 0.5),
            'avg_effort_ratio': feature_row.get('effort_ratio', 1.0),
            'avg_sleep_var': feature_row.get('sleep_variance_7d', 50),
            'initial_motivation': init_motivation
        }
        burnout_risk = state.burnout_model.predict_current_risk(risk_input)
        
        # Recommendation
        rec = state.recommender.generate_recommendation(
            user_id="demo_user",
            date_str=str(today),
            adherence_prob=adh_prob,
            burnout_risk=burnout_risk,
            is_anomaly=False,
            recent_features=feature_row
        )
        
        return rec
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
