import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List

# Import Habit Engine components
# Assumes src is in the python path
from src.domain.schemas import DailyBehavior
from src.processing.features import FeatureEngineer
from src.models.adherence import AdherenceModel
from src.models.burnout import BurnoutRiskModel
from src.processing.recommender import RecommendationEngine

st.set_page_config(page_title="Habit Engine Interactive", layout="wide")

st.title("Habit Engine: Interactive Demo")
st.markdown("""
This application allows you to simulate user data and interact with the Habit Engine's
processing and modeling layers directly, without connecting to external APIs.
""")

# --- SIDEBAR: DATA GENERATION SETTINGS ---
st.sidebar.header("1. History Generation")
st.sidebar.markdown("Configure the synthetic history used to train the models.")

history_days = st.sidebar.slider("History Length (Days)", 30, 365, 90)

st.sidebar.subheader("Steps Behavior")
mean_steps = st.sidebar.slider("Avg Daily Steps", 1000, 20000, 8000)
steps_volatility = st.sidebar.slider("Steps Volatility", 0.1, 1.0, 0.3, help="Higher means more erratic behavior")

st.sidebar.subheader("Exercise Behavior")
exercise_freq = st.sidebar.slider("Exercise Frequency (Days/Week)", 0, 7, 3)
mean_exercise_duration = st.sidebar.slider("Avg Exercise Duration (mins)", 15, 120, 45)

st.sidebar.subheader("Sleep Behavior")
mean_sleep = st.sidebar.slider("Avg Sleep (Hours)", 4.0, 10.0, 7.5)
sleep_volatility = st.sidebar.slider("Sleep Volatility", 0.1, 1.0, 0.2)

# --- DATA GENERATION FUNCTION ---
def generate_history(
    days: int, 
    avg_steps: int, steps_vol: float,
    ex_freq: int, ex_dur: int,
    avg_sleep_h: float, sleep_vol: float
) -> List[DailyBehavior]:
    
    data = []
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Probabilities
    ex_prob = ex_freq / 7.0
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Steps
        # Use lognormal to avoid negative steps and simulate real distribution
        steps = int(np.random.normal(avg_steps, avg_steps * steps_vol))
        steps = max(0, steps)
        
        # Exercise
        if np.random.random() < ex_prob:
            ex_done = True
            ex_mins = max(10, int(np.random.normal(ex_dur, ex_dur * 0.2)))
        else:
            ex_done = False
            ex_mins = 0
            
        # Sleep
        sleep_mins = max(0, int(np.random.normal(avg_sleep_h * 60, avg_sleep_h * 60 * sleep_vol)))
        
        # Create Object
        # Note: We are mocking the "Aggregated" state directly, skipping raw events
        record = DailyBehavior(
            date=current_date,
            total_steps=steps,
            exercise_minutes=ex_mins,
            exercise_done=ex_done,
            sleep_duration_minutes=sleep_mins,
            # Timestamps are optional in aggregations if we just analyze totals
            sleep_start_time=None,
            sleep_end_time=None,
            exercise_start_time=None
        )
        data.append(record)
        
    return data

# --- MAIN APP FLOW ---

# 1. Generate Data
st.header("1. Data Ingestion (Simulated)")

# Session state for data persistence
if 'history_df' not in st.session_state:
    st.session_state.history_df = None

# Manual Regeneration Trigger
if st.button("Regenerate Data from Settings") or st.session_state.history_df is None:
    with st.spinner("Generating synthetic user history..."):
        _generated_data = generate_history(
            history_days, mean_steps, steps_volatility, 
            exercise_freq, mean_exercise_duration, 
            mean_sleep, sleep_volatility
        )
        st.session_state.history_df = pd.DataFrame([d.model_dump() for d in _generated_data])

st.markdown("### User History (Editable)")
st.info("You can edit the values below directly to test different scenarios (e.g., adding a 14-day gap).")

def clean_nan(val):
    if pd.isna(val): return None
    return val

# Interactive Editor
edited_df = st.data_editor(
    st.session_state.history_df,
    column_config={
        "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD", required=True),
        "total_steps": st.column_config.NumberColumn("Steps", min_value=0),
        "exercise_minutes": st.column_config.NumberColumn("Ex. Mins", min_value=0),
        "exercise_done": st.column_config.CheckboxColumn("Exercise Done?"),
        "sleep_duration_minutes": st.column_config.NumberColumn("Sleep (min)", min_value=0)
    },
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True
)

# Convert edited DF back to objects for the pipeline
history_data = []

# Sort by date to ensure features calculate correctly
if not edited_df.empty:
    if 'date' in edited_df.columns:
        edited_df['date'] = pd.to_datetime(edited_df['date'])
        edited_df = edited_df.sort_values('date')

for _, row in edited_df.iterrows():
    # Date handling
    d_val = row['date']
    if isinstance(d_val, pd.Timestamp):
        d_val = d_val.date()
    elif isinstance(d_val, str):
        try:
            d_val = datetime.strptime(d_val, "%Y-%m-%d").date()
        except:
            d_val = datetime.now().date() # Fallback

    record = DailyBehavior(
        date=d_val,
        total_steps=int(row['total_steps']),
        exercise_minutes=int(row['exercise_minutes']),
        exercise_done=bool(row['exercise_done']),
        sleep_duration_minutes=int(row['sleep_duration_minutes']),
        sleep_start_time=clean_nan(row.get('sleep_start_time')),
        sleep_end_time=clean_nan(row.get('sleep_end_time')),
        exercise_start_time=clean_nan(row.get('exercise_start_time'))
    )
    history_data.append(record)

st.caption(f"Processing {len(history_data)} days of history.")

# 2. Feature Engineering
st.header("2. Feature Engineering")
engineer = FeatureEngineer()
with st.spinner("Calculating behavioral signals (rolling averages, trends, consistency)..."):
    df_features = engineer.enhance(history_data)
    
    # Display some interesting features
    cols = ['total_steps', 'sleep_duration_minutes', 'exercise_done']
    # Add generated cols if they exist
    generated_cols = [c for c in df_features.columns if c not in cols and c != 'date']
    display_cols = cols + generated_cols[:3] # Show a few generated ones
    
    st.dataframe(df_features[display_cols].tail(5))
    
    # Simple Chart
    st.line_chart(df_features[['total_steps', 'sleep_duration_minutes']])

# 3. Model Training
st.header("3. Model Training")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Adherence Model")
    adherence_model = AdherenceModel()
    try:
        metrics_adh = adherence_model.train(df_features)
        
        st.metric("Model Accuracy", f"{metrics_adh.get('accuracy', 0):.2f}")
        st.metric("AUC Score", f"{metrics_adh.get('auc', 0):.2f}")
        
        # Feature Importance
        if 'feature_importance' in metrics_adh:
            st.write("Top Factors:")
            fi = pd.DataFrame(list(metrics_adh['feature_importance'].items()), columns=['Feature', 'Weight'])
            st.dataframe(fi.sort_values('Weight', ascending=False).head(5), hide_index=True)
            
    except Exception as e:
        metrics_adh = {}
        st.warning(f"Adherence Model Training Failed: {e}")
        st.caption("Ensure your history has both exercise days and rest days (variation needed for Logistic Regression).")

with col2:
    st.subheader("Burnout Risk Model")
    burnout_model = BurnoutRiskModel(dropout_threshold_days=7)
    try:
        metrics_burn = burnout_model.train(df_features)
        
        status = metrics_burn.get('status')
        if status == 'success':
            st.success("Training Successful")
            st.metric("C-Index", f"{metrics_burn.get('concordance', 0):.2f}")
            
            if 'coefficients' in metrics_burn:
                st.write("Risk Factors:")
                coefs = pd.DataFrame(list(metrics_burn['coefficients'].items()), columns=['Feature', 'Risk Coef'])
                st.dataframe(coefs, hide_index=True)
        else:
            st.warning(f"Training Issue: {metrics_burn.get('message')}")
            st.caption("Try increasing history length or volatility to generate more 'dropout' events.")
            
    except Exception as e:
        metrics_burn = {"status": "error"}
        st.error(f"Burnout Model Critical Fail: {e}")

# 4. Interactive Calculator
st.header("4. Interactive Prediction")
st.markdown("Enter values for **Today** to see what the models predict.")

input_col1, input_col2, input_col3 = st.columns(3)

with input_col1:
    today_steps = st.number_input("Today's Steps", 0, 50000, 5000)
with input_col2:
    today_sleep = st.number_input("Last Night's Sleep (hours)", 0.0, 12.0, 7.0)
with input_col3:
    today_ex_mins = st.number_input("Exercise Duration (mins)", 0, 180, 0)
    today_ex_done = today_ex_mins > 0

if st.button("Analyze Today"):
    # Create the "Today" record
    today = datetime.now().date()
    today_record = DailyBehavior(
        date=today,
        total_steps=today_steps,
        exercise_minutes=today_ex_mins,
        exercise_done=today_ex_done,
        sleep_duration_minutes=today_sleep * 60,
    )
    
    # We need to append this to history to calculate features (rolling windows need context)
    # Be careful not to duplicate if we re-run
    full_history = history_data + [today_record]
    
    # Re-run features
    df_full = engineer.enhance(full_history)
    
    # Get the row for today (last row)
    today_features = df_full.iloc[[-1]] 
    
    # Predictions
    
    # 1. Adherence
    try:
        adh_prob_val = adherence_model.predict_next_day_proba(today_features)
    except Exception as e:
        adh_prob_val = 0.0
        st.error(f"Prediction Error: {e}")
    
    # 2. Burnout
    try:
        burnout_risk = burnout_model.predict_current_risk(today_features.iloc[0].to_dict())
    except Exception as e:
        burnout_risk = 0.0
        # st.error(f"Burnout Prediction Error: {e}")
    
    st.subheader("Results")
    
    # Adherence Gauge
    st.metric("Predicted Adherence Probability", f"{adh_prob_val:.1%}")
    if adh_prob_val > 0.7:
        st.success("High likelihood of sticking to habits!")
    elif adh_prob_val > 0.4:
        st.warning("Moderate adherence chance.")
    else:
        st.error("Low adherence - You might fall off the wagon.")
        
    st.metric("Burnout Hazard Score", f"{burnout_risk:.2f}", help="> 1.0 means higher risk than average")

    # Recommendation
    st.subheader("Engine Recommendation")
    
    recommender = RecommendationEngine()
    
    try:
        rec = recommender.generate_recommendation(
            user_id="sim_user",
            date_str=str(today),
            adherence_prob=adh_prob_val,
            burnout_risk=burnout_risk,
            is_anomaly=False, # Anomaly detection not active in interactive mode yet
            recent_features=today_features.iloc[0].to_dict()
        )
        
        # Display the formal engine response
        st.info(f"**{rec.message_title}**")
        st.write(rec.message_body)
        st.success(f"Suggestion: {rec.suggested_action}")
        
    except Exception as e:
        st.error(f"Recommender Error: {e}")
        # Fallback simplistic logic
        if today_steps < mean_steps * 0.5:
             st.info("💡 Fallback: Your activity is low today. Try a 10-minute walk.")
        elif today_sleep < 6.0:
            st.info("💡 Recommendation: Prioritize sleep tonight to recover.")
        else:
            st.info("💡 Recommendation: Great job! Keep maintaining this streak.")

