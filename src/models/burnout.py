from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index

class BurnoutRiskModel:
    """
    Estimates the risk of 'habit death' (dropout) using Survival Analysis.
    
    Definition of Event (Death): X consecutive missed days (default=5).
    Unit of analysis: A 'Streak' or 'Habit Attempt'.
    """

    def __init__(self, dropout_threshold_days: int = 5):
        self.dropout_threshold = dropout_threshold_days
        self.cph = CoxPHFitter()
        self.is_trained = False
        
    def _identify_streaks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts daily time-series into 'SURVIVAL FORMAT' (duration, event_occurred).
        Returns a DataFrame where each row is a 'period' of consistent behavior 
        leading up to a dropout (or current day).
        """
        data = df.copy().sort_index()
        
        # Define a 'Miss'
        # If exercise_done is False, it's a miss.
        # But we only care about BLOCKS of misses.
        
        data['is_miss'] = (data['exercise_done'] == False).astype(int)
        
        # Identify streaks of misses
        # Group consecutive days with same 'is_miss' value
        data['block_id'] = (data['is_miss'] != data['is_miss'].shift()).cumsum()
        
        # We want to identify 'Active Episodes'.
        # An active episode ends when a 'Death Block' (Miss block >= threshold) starts.
        
        episodes = []
        
        # Simple approach for feature generation: 
        # Break history into weekly chunks or just use sliding window "risk checks"?
        # Standard Survival: One row per "subject". Here "subject" = A Habit Streak.
        
        # Let's iterate and find start/end of active streaks.
        current_streak_start = data.index[0]
        consecutive_misses = 0
        
        # We need to aggregate features for the streak
        # For simplicity in this v1: We will compute instantaneous risk based on rolling features
        # rather than full episode aggregation, as we assume time-varying covariates.
        
        # ALTERNATIVE: Rolling Hazard Prediction
        # If we lack "multiple subjects", fitting CoxPH is hard.
        # Let's pivot: We will treat every DAY as an observation, 
        # and predicted variable is "Will dropout occur within K days?"
        # But User asked for Survival Analysis.
        
        # Let's try to frame "Weekly Summaries" as subjects.
        # Too complex for quick demo.
        
        pass 
        
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepares standard format for Lifelines: T (duration), E (event), covariates.
        Since we are single-user, we treat 'Past Streaks' as the population.
        """
        # 1. Detect Missed Blocks
        df = df.sort_index()
        df['miss_groups'] = (df['exercise_done'] != df['exercise_done'].shift()).cumsum()
        
        # Filter to miss blocks
        miss_blocks = df[df['exercise_done'] == False].groupby('miss_groups')
        
        # Find dates where a "Dropout" (Death) actually happened
        dropout_dates = []
        for _, group in miss_blocks:
            if len(group) >= self.dropout_threshold:
                # The start of this block is the "Death" date
                dropout_dates.append(group.index[0])
                
        # Now segment the entire history into "Lives" (periods between dropouts)
        # Start -> Dropout 1 -> Dropout 2 -> Current (Censored)
        
        lives = []
        current_start = df.index[0]
        
        dates_of_interest = sorted(dropout_dates)
        
        # If no dropouts ever, entire history is one censored life
        if not dates_of_interest:
             # Aggregate whole history
             life_attrs = self._aggregate_period(df, current_start, df.index[-1], event=0)
             if life_attrs: lives.append(life_attrs)
        else:
            for death_date in dates_of_interest:
                if death_date > current_start:
                    # History from current_start to death_date is a "Life" that DIED (Event=1)
                    # We usually say time is (death_date - start)
                    # Exclude the death block itself from the "Active behavior" aggregation statistics?
                    # Maybe include last 7 days of it to capture the decline.
                    
                    life_attrs = self._aggregate_period(df, current_start, death_date, event=1)
                    if life_attrs: lives.append(life_attrs)
                    
                    # New life starts after the death event?
                    # Or does it start immediately? A dropout implies a restart.
                    # Let's assume restart happens when they exercise again.
                    
                    # Find next exercise date
                    future = df[df.index > death_date]
                    next_success = future[future['exercise_done'] == True].first_valid_index()
                    
                    if next_success:
                        current_start = next_success
                    else:
                        current_start = None
                        break
            
            # Remaining time is censored
            if current_start and current_start <= df.index[-1]:
                life_attrs = self._aggregate_period(df, current_start, df.index[-1], event=0)
                if life_attrs: lives.append(life_attrs)
                
        return pd.DataFrame(lives)

    def _aggregate_period(self, df: pd.DataFrame, start, end, event):
        """Aggregate behavioral stats for a specific time window (A 'Life')."""
        subset = df.loc[start:end]
        if len(subset) < 3: return None # Too short to meaningful
        
        duration = (end - start).days
        
        # Covariates: Mean/Variance of behavior during this attempt
        return {
            'duration': duration,
            'event': event, # 1 if died, 0 if still going
            'avg_sleep_consistency': subset['sleep_consistency_score'].mean(),
            'avg_effort_ratio': subset['effort_ratio'].mean(),
            'avg_sleep_var': subset['sleep_variance_7d'].mean(),
            'initial_motivation': subset.iloc[:3]['exercise_minutes'].mean() # First 3 days effort
        }

    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train Cox Proportional Hazards model.
        """
        survival_df = self.prepare_data(df)
        
        if len(survival_df) < 2:
             # Fallback for insufficient data
             return {"status": "warning", "message": "Not enough streaks to train survival model"}
             
        try:
            # Fit Model
            self.cph.fit(survival_df, duration_col='duration', event_col='event')
            self.is_trained = True
            
            return {
                "status": "success",
                "concordance": self.cph.concordance_index_,
                "coefficients": self.cph.params_.to_dict()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def predict_current_risk(self, recent_streak_features: Dict[str, Any]) -> float:
        """
        Predicts the relative 'Hazard' risk score for the current active streak.
        Higher = More likely to drop out soon.
        """
        if not self.is_trained:
            return 0.5 # Default risk
            
        # Create a single-row DF
        df = pd.DataFrame([recent_streak_features])
        
        # Get partial hazard (relative risk)
        return self.cph.predict_partial_hazard(df).iloc[0]
