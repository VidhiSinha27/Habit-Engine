from typing import Any, Dict, Tuple
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix

class AdherenceModel:
    """
    Predicts probability of adhering to habit (exercise) TOMORROW.
    Uses Logistic Regression for interpretability (Feature Importance).
    """

    def __init__(self):
        self.model = LogisticRegression(class_weight='balanced', random_state=42)
        self.scaler = StandardScaler()
        # Added 'exercise_done' (current day) to make the model sensitive to today's input
        # Added 'exercise_minutes' so duration impacts prediction
        self.feature_columns = [
            'exercise_done', 'exercise_minutes', 'total_steps', 
            'prev_steps', 'prev_sleep_dur', 'prev_exercise_done',
            'steps_7d_avg', 'sleep_7d_avg',
            'sleep_variance_7d', 'sleep_consistency_score',
            'rolling_misses_3d', 'is_weekend', 'effort_ratio',
            'is_recovery_period', 'is_streak_break', 'days_since_workout'
        ]
        self.is_trained = False

    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare X (Features) and y (Target).
        Target: Will they exercise tomorrow?
        """
        data = df.copy()
        
        # Shift target: We want to predict 'exercise_done' for t+1 using info from t
        data['target_next_day'] = data['exercise_done'].shift(-1)
        
        # Drop the last row because it implies a target in the future we don't know
        data = data.dropna(subset=['target_next_day'])
        
        X = data[self.feature_columns]
        y = data['target_next_day'].astype(int)
        
        return X, y

    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Trains the model and returns metrics.
        Uses time-series split (first 80% train, last 20% test).
        """
        X, y = self.prepare_data(df)
        
        if len(X) < 10:
             return {"status": "error", "message": "Not enough data to train"}

        # Time-based split
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Scaling
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Training
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluation
        y_pred = self.model.predict(X_test_scaled)
        y_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        try:
            auc = roc_auc_score(y_test, y_proba)
        except ValueError:
            auc = 0.5 # Handle single class in test set
            
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "auc": auc,
            "feature_importance": dict(zip(self.feature_columns, self.model.coef_[0]))
        }
        
        return metrics

    def predict_next_day_proba(self, recent_feature_row: pd.DataFrame) -> float:
        """
        Inference: Predict for tomorrow based on today's row.
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
            
        # Ensure input has correct cols
        X = recent_feature_row[self.feature_columns]
        X_scaled = self.scaler.transform(X)
        
        proba = self.model.predict_proba(X_scaled)[0, 1]
        return proba
