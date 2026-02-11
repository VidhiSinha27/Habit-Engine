import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.domain.schemas import DailyBehavior
from src.processing.features import FeatureEngineer
from src.models.adherence import AdherenceModel

np.random.seed(42) # Fix seed for reproducibility

def generate_history(days):
    data = []
    start = datetime.now() - timedelta(days=days)
    
    # App defaults
    avg_steps = 8000
    ex_freq = 3 # 3 days a week
    ex_prob = ex_freq / 7.0
    
    for i in range(days):
        d = start + timedelta(days=i)
        
        # Steps lognormal as in app
        steps = int(np.random.normal(avg_steps, avg_steps * 0.3))
        steps = max(0, steps)
        
        # Exercise
        if np.random.random() < ex_prob:
            ex_done = True
            ex_mins = 45
        else:
            ex_done = False
            ex_mins = 0
            
        sleep = 450 + np.random.normal(0, 30)
        
        data.append(DailyBehavior(
            date=d.date(),
            total_steps=steps,
            exercise_minutes=ex_mins,
            exercise_done=ex_done,
            sleep_duration_minutes=sleep, # Fix: removed time fields to match DailyBehavior or let defaults handle
            sleep_start_time=None,
            sleep_end_time=None,
            exercise_start_time=None
        ))
    return data

# History
history = generate_history(90)
# Gap
for i in range(1, 15):
    history[-i].total_steps = 500
    history[-i].exercise_done = False
    history[-i].exercise_minutes = 0

engineer = FeatureEngineer()
df = engineer.enhance(history)

model = AdherenceModel()
metrics = model.train(df)

last_row = df.iloc[[-1]]
prob = model.predict_next_day_proba(last_row)

print("Coefficients:")
for k, v in metrics['feature_importance'].items():
    print(f"  {k}: {v:.4f}")

print(f"\nProbability: {prob:.1%}")
