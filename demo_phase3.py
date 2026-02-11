from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.ingestion.mock_provider import MockHealthProvider
from src.processing.aggregator import DailyAggregator
from src.processing.features import FeatureEngineer
from src.models.burnout import BurnoutRiskModel
from src.models.anomaly import AnomalyDetector

def main():
    print("--- Habit Engine: Phase 3 Demo ---")
    
    # 1. Pipeline Setup (Long History)
    provider = MockHealthProvider(seed=555) 
    
    # Fetch 1 year of data to ensure multiple "Streaks" occur
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    print(f"1. Ingestion: Fetching 1 year history ({start_date.date()} -> {end_date.date()})")
    
    events = provider.fetch_all_events(start_date, end_date)
    aggregator = DailyAggregator()
    daily_records = aggregator.aggregate(events)
    print(f"   Fetched {len(events)} events -> {len(daily_records)} days.")
    
    # 2. Features
    print("\n2. Feature Engineering...")
    engineer = FeatureEngineer()
    df_features = engineer.enhance(daily_records)
    
    # 3. Burnout Risk Model (Survival Analysis)
    print("\n3. Training Burnout Risk Model (Cox Survival Analysis)...")
    # Define "Dropout" as 7 days of no exercise
    survival_model = BurnoutRiskModel(dropout_threshold_days=7)
    
    # Show how many 'lives' we found
    survival_data = survival_model.prepare_data(df_features)
    print(f"   Detected {len(survival_data)} distinct 'Habit Streaks' in history.")
    if not survival_data.empty:
        print(survival_data.head())
    
    metrics_surv = survival_model.train(df_features)
    print(f"   Training Result: {metrics_surv.get('status')}")
    if metrics_surv.get('status') == 'success':
        print(f"   Concordance Index: {metrics_surv['concordance']:.2f} (0.5=Random, 1.0=Perfect)")
        print("   Risk Factors (Coefficients):")
        for k,v in metrics_surv['coefficients'].items():
            print(f"     - {k}: {v:.4f}")
            
    # Estimate risk for CURRENT streak
    if not survival_data.empty:
        # Fake a "current streak" aggregate for demo using last week stats
        last_7_days = df_features.iloc[-7:]
        current_streak_stats = {
            'avg_sleep_consistency': last_7_days['sleep_consistency_score'].mean(),
            'avg_effort_ratio': last_7_days['effort_ratio'].mean(),
            'avg_sleep_var': last_7_days['sleep_variance_7d'].mean(),
            'initial_motivation': 30.0 # hypothetical
        }
        risk_score = survival_model.predict_current_risk(current_streak_stats)
        print(f"\n   Current Streak Hazard Score: {risk_score:.3f}")
        
    # 4. Anomaly Detection
    print("\n4. Training Anomaly Detector (Isolation Forest)...")
    anomaly_detector = AnomalyDetector()
    metrics_anom = anomaly_detector.train(df_features)
    print(f"   Detected {metrics_anom.get('anomalies_detected_history')} historical days as 'Anomalies'.")
    
    # Check last few days for anomalies
    print("   Checking recent days for behavioral anomalies:")
    recent_days = df_features.tail(5)
    for date, row in recent_days.iterrows():
        result = anomaly_detector.check_anomaly(row)
        status = "ALERT" if result['is_anomaly'] else "Normal"
        print(f"     - {date.date()}: {status} (Score: {result['severity_score']:.2f})")
        if result['is_anomaly']:
            # Explain why (simplistic check)
            if row['sleep_duration_minutes'] < 300: print("       -> Low sleep detected")
            if row['total_steps'] < 1000: print("       -> Extremely low activity")

    print("\nPhase 3 Complete: Survival Analysis & Anomaly Detection operational.")

if __name__ == "__main__":
    main()
