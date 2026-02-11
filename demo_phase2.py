from datetime import datetime, timedelta
import pandas as pd
from src.ingestion.mock_provider import MockHealthProvider
from src.processing.aggregator import DailyAggregator
from src.processing.features import FeatureEngineer
from src.models.adherence import AdherenceModel

def main():
    print("--- Habit Engine: Phase 2 Demo ---")
    
    # 1. Pipeline Setup (Same as Phase 1)
    provider = MockHealthProvider(seed=101) # New seed for variety
    
    # Fetch LONGER history for better training (90 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    print(f"1. Ingestion: Fetching history {start_date.date()} -> {end_date.date()}")
    
    events = provider.fetch_all_events(start_date, end_date)
    aggregator = DailyAggregator()
    daily_records = aggregator.aggregate(events)
    
    print(f"   Fetched {len(events)} raw events.")
    print(f"   Aggregated {len(daily_records)} daily states.")
    
    # 2. Feature Engineering
    print("\n2. Feature Engineering: Calculating behavioral signals...")
    engineer = FeatureEngineer()
    df_features = engineer.enhance(daily_records)
    
    print("   Generated Features:")
    print(f"   {df_features.columns.tolist()}")
    
    # Show a snippet of behavioral features
    cols = ['sleep_variance_7d', 'sleep_consistency_score', 'effort_ratio', 'exercise_done']
    print("\n   Sample Feature Rows:")
    print(df_features[cols].tail(5))

    # 3. Model Training
    print("\n3. Adherence Prediction Model (Logistic Regression)...")
    model = AdherenceModel()
    metrics = model.train(df_features)
    
    print("\n   Training Results:")
    print(f"   Accuracy: {metrics['accuracy']:.2f}")
    print(f"   AUC Score: {metrics['auc']:.2f}")
    
    print("\n   Behavioral Feature Global Importance (Weights):")
    # Sort importances
    imps = metrics['feature_importance']
    sorted_imps = sorted(imps.items(), key=lambda x: abs(x[1]), reverse=True)
    for feature, weight in sorted_imps:
        print(f"   - {feature}: {weight:.4f}")
        
    # 4. Inference (Predict Tomorrow)
    print("\n4. Live Inference:")
    last_day = df_features.iloc[[-1]] # The most recent day
    prob = model.predict_next_day_proba(last_day)
    
    print(f"   Based on data from {last_day.index[0].date()},")
    print(f"   Probability of exercising tomorrow: {prob:.1%}")
    
    if prob > 0.7:
        print("   -> Prediction: High likelihood. Suggest challenging workout.")
    elif prob < 0.3:
        print("   -> Prediction: High dropout risk. Suggest 'Minimum Viable Habit' (e.g. 5 min walk).")
    else:
        print("   -> Prediction: Uncertain. Suggest standard reminder.")

    print("\nPhase 2 Complete: Features & Prediction Model are functional.")

if __name__ == "__main__":
    main()

# %%
