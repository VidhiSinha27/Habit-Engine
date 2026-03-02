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
            
            result = {
                "is_anomaly": bool(pred == -1),
                "severity_score": float(score), # Lower score = More abnormal
                "context": None
            }

            if result["is_anomaly"]:
                # Explainability: Which feature deviated the most?
                # X_scaled contains z-scores relative to training mean
                import numpy as np
                z_scores = X_scaled[0] 
                max_idx = np.argmax(np.abs(z_scores))
                feature_key = self.feature_cols[max_idx]
                z_val = z_scores[max_idx]

                # Map to human readable
                name_map = {
                    'total_steps': 'Step Count',
                    'sleep_duration_minutes': 'Sleep Duration',
                    'sleep_variance_7d': 'Sleep Stability'
                }
                feat_name = name_map.get(feature_key, feature_key)
                
                # Determine direction
                if feature_key == 'sleep_variance_7d':
                     # High variance is usually the anomaly of interest (instability)
                     direction = "Unstable" if z_val > 0 else "Unusually Stable"
                else:
                     direction = "High" if z_val > 0 else "Low"
                
                result["context"] = f"{direction} {feat_name}"

            return result
        except Exception as e:
            print(f"ANOMALY CHECK ERROR: {e}")
            return {"error": str(e), "is_anomaly": False, "severity_score": 0.0}
