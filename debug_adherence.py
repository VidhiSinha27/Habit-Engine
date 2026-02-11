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

def generate_history(days):
    data = []
    start = datetime.now() - timedelta(days=days)
    for i in range(days):
        d = start + timedelta(days=i)
        # Normal active user
        steps = 8000 + np.random.randint(-1000, 1000)
        sleep = 480 + np.random.randint(-30, 30)
        # Exercise 
        ex_done = (np.random.random() > 0.5)
        ex_mins = 45 if ex_done else 0
        
        data.append(DailyBehavior(
            date=d.date(),
            total_steps=steps,
            exercise_minutes=ex_mins,
            exercise_done=ex_done,
            sleep_duration_minutes=sleep,
            sleep_start_time=None,
            sleep_end_time=None,
            exercise_start_time=None
        ))
    return data

# 1. Generate normal history
history = generate_history(100)

# 2. Modify last 14 days to be inactive
for i in range(1, 15):
    history[-i].total_steps = 1000
    history[-i].exercise_done = False
    history[-i].exercise_minutes = 0

# 3. Features
engineer = FeatureEngineer()
df = engineer.enhance(history)

# 4. Train
model = AdherenceModel()
metrics = model.train(df)

print("Coefficients:")
for k, v in metrics['feature_importance'].items():
    print(f"  {k}: {v:.4f}")

# 5. Predict
last_row = df.iloc[[-1]]
print("\nLast Row Features (relevant):")
cols = ['steps_7d_avg', 'rolling_misses_3d', 'prev_exercise_done', 'sleep_consistency_score']
print(last_row[cols].T)

prob = model.predict_next_day_proba(last_row)
print(f"\nProbability: {prob:.1%}")
