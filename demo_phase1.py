from datetime import datetime, timedelta
import pandas as pd
from src.ingestion.mock_provider import MockHealthProvider
from src.processing.aggregator import DailyAggregator

def main():
    print("--- Habit Engine: Phase 1 Demo ---")
    
    # 1. Setup Provider
    provider = MockHealthProvider(seed=42)
    
    # 2. Fetch Data (Last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    print(f"Fetching data from {start_date.date()} to {end_date.date()}...")
    
    events = provider.fetch_all_events(start_date, end_date)
    print(f"Fetched {len(events)} raw events.")
    
    # 3. Aggregate to Daily Canonical
    aggregator = DailyAggregator()
    daily_records = aggregator.aggregate(events)
    print(f"Aggregated into {len(daily_records)} daily records.")
    
    # 4. Display as DataFrame (Production-like view)
    df = pd.DataFrame([r.model_dump() for r in daily_records])
    
    # Clean up display
    cols = ['date', 'total_steps', 'sleep_duration_minutes', 'exercise_minutes', 'exercise_done', 'data_missing_flag']
    print("\nSample Daily Canonical Table:")
    print(df[cols].head(10))
    
    print("\nPhase 1 Complete: Architecture, Ingestion, and Aggregation layers are functional.")

if __name__ == "__main__":
    print("NOTE: For the interactive version with manual input, run:")
    print("      streamlit run app.py")
    print("---------------------------------------------------------")
    main()
