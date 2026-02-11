from typing import Any, Dict, List
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyDetector:
    """
    Detects behavioral anomalies (Drift / Relapse Triggers).
    Examples:
    - Sudden spike in sleep variance (All-nighter?)
    - Dramatic drop in steps (Illness? Depressive episode?)
    """
    
    def __init__(self):
        # Contamination = expected proportion of outliers (e.g. 5%)
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.scaler = StandardScaler()
        self.feature_cols = ['total_steps', 'sleep_duration_minutes', 'sleep_variance_7d']
        self.is_trained = False
        
    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Trains the unsupervised anomaly detector on historical behavior.
        """
        if len(df) < 14:
            return {"status": "error", "message": "Need 2 weeks data"}
            
        X = df[self.feature_cols].dropna()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Count anomalies in training set
        preds = self.model.predict(X_scaled)
        n_anomalies = list(preds).count(-1)
        
        return {
            "status": "success",
            "anomalies_detected_history": n_anomalies
        }
        
    def check_anomaly(self, day_row: pd.Series) -> Dict[str, Any]:
        """
        Checks if a specific day is an outlier.
        Returns:
            is_anomaly: bool
            score: float (lower is more anomalous)
        """
        if not self.is_trained:
             return {"is_anomaly": False, "score": 0.0}
             
        # Extract features
        try:
            X = pd.DataFrame([day_row[self.feature_cols]])
            X_scaled = self.scaler.transform(X)
            
            # Predict
            pred = self.model.predict(X_scaled)[0] # 1 for normal, -1 for outlier
            score = self.model.decision_function(X_scaled)[0] 
            
            return {
                "is_anomaly": bool(pred == -1),
                "severity_score": float(score) # Lower score = More abnormal
            }
        except KeyError as e:
            return {"error": f"Missing columns: {e}"}
