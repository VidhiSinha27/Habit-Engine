# Habit Engine - Interactive Interface

This new Streamlit interface replaces the CLI demos (`demo_phase1.py` etc) and allows you to simulate user behavior and interact with the Habit Engine models directly.

## Usage

1. **Install Requirements**
   Ensure you have Streamlit installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**
   Execute the following command in the terminal:
   ```bash
   streamlit run app.py
   ```

## Features

- **No External APIs**: All data is generated locally based on your parameters.
- **Data Simulation**: Configure "History" parameters (Avg Steps, Sleep, etc.) to train the personalized models.
- **Interactive Prediction**: Input "Today's" stats manually to see real-time Adherence probabilities and Burnout risk.
