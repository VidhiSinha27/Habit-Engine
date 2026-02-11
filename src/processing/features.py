import pandas as pd
import numpy as np
from typing import List
from src.domain.schemas import DailyBehavior

class FeatureEngineer:
    """
    Transforms canonical daily data into ML-ready feature vectors.
    Focuses on behavioral signals (consistency, trends) rather than just raw totals.
    """
    
    def __init__(self):
        pass

    def enhance(self, daily_data: List[DailyBehavior]) -> pd.DataFrame:
        """
        Takes a list of DailyBehavior objects and returns a DataFrame 
        enriched with rolling features, lag features, and behavioral signals.
        """
        # Convert to DataFrame
        df = pd.DataFrame([d.model_dump() for d in daily_data])
        
        if df.empty:
            return df
            
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').set_index('date')
        
        # 1. Basic Shift/Lag Features (What happened yesterday matters for today)
        df['prev_steps'] = df['total_steps'].shift(1)
        df['prev_sleep_dur'] = df['sleep_duration_minutes'].shift(1)
        df['prev_exercise_done'] = df['exercise_done'].shift(1).astype(float)
        
        # 2. Rolling Trends (7-day windows)
        # 7d mean
        df['steps_7d_avg'] = df['total_steps'].rolling(window=7, min_periods=1).mean()
        df['sleep_7d_avg'] = df['sleep_duration_minutes'].rolling(window=7, min_periods=1).mean()
        
        # 3. Behavioral Consistency (Variance)
        # ADHD/Burnout signal: High sleep variance often precedes burnout/drop-off.
        df['sleep_variance_7d'] = df['sleep_duration_minutes'].rolling(window=7, min_periods=3).std()
        df['steps_variance_7d'] = df['total_steps'].rolling(window=7, min_periods=3).std()
        
        # 4. "Consistency Score" (Inverse of Coefficient of Variation)
        # Higher is better. If mean is 0, handle gracefully.
        # CV = StdDev / Mean. Score = 1 / (1 + CV) to bound it roughly 0-1
        # We add epsilon to avoid div by zero.
        epsilon = 1e-6
        df['sleep_consistency_score'] = 1 / (1 + (df['sleep_variance_7d'] / (df['sleep_7d_avg'] + epsilon)))
        
        # 5. Recovery / Resilience Signal
        # Did they bounce back? 
        # Feature: logic check if 2 days ago was a miss (0 steps/exercise) and yesterday was a hit.
        # Simplification: Rolling sum of "misses" in last 3 days
        df['rolling_misses_3d'] = (df['data_missing_flag'] | (df['exercise_done'] == False)).rolling(window=3).sum()

        # Custom Logic: "Streak Break" vs "Recovery"
        # Calculate consecutive days without exercise (0 or False)
        # We invert boolean to count 'misses'
        is_miss = (~df['exercise_done']).astype(int)
        # Group by change in value, then cumsum to get run lengths of 1s (misses)
        # 1. Detect changes: is_miss != shift
        # 2. Cumsum identifies groups
        # 3. Cumsum of values within groups gives counter
        group_id = (is_miss != is_miss.shift()).cumsum()
        df['consecutive_misses'] = is_miss.groupby(group_id).cumsum()
        
        # User Rule: < 3 days miss -> Recovery (Bonus)
        # User Rule: > 4 days miss -> Break (Penalty)
        df['is_recovery_period'] = ((df['consecutive_misses'] > 0) & (df['consecutive_misses'] < 3)).astype(int)
        df['is_streak_break'] = (df['consecutive_misses'] > 4).astype(int)
        # We also pass the raw count for the break to indicate magnitude (14 days worse than 5)
        df['days_since_workout'] = df['consecutive_misses'] * df['is_streak_break']

        # 6. Temporal Context
        df['day_of_week'] = df.index.dayofweek # 0=Mon, 6=Sun
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # 7. Intensity/Load Features
        # "Effort Overload": Recent activity significantly higher than monthly baseline
        df['steps_30d_avg'] = df['total_steps'].rolling(window=30, min_periods=7).mean()
        df['effort_ratio'] = df['steps_7d_avg'] / (df['steps_30d_avg'] + epsilon)
        # If effort ratio > 1.3, they might be pushing too hard (Burnout risk)
        
        # Drop initial rows where lags create NaNs (optional, or handle in model)
        # For this phase, we keep them but fillna(0) for simple models might be needed
        df = df.fillna(0)
        
        return df
