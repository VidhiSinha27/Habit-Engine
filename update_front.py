
import os

base = r"c:\Users\27vid\Downloads\Habit Engine\web-client\src"

css = r'''
:root {
  --primary: #6366f1;
  --primary-hover: #4f46e5;
  --bg: #f8fafc;
  --card-bg: #ffffff;
  --text: #1e293b;
  --text-light: #64748b;
  --border: #e2e8f0;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
}

body {
  margin: 0;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background-color: var(--bg);
  color: var(--text);
  line-height: 1.5;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 3rem;
  text-align: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--primary);
  margin-bottom: 0.5rem;
}
.header h1 { margin: 0; font-size: 2rem; }
.header p { color: var(--text-light); margin: 0; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

/* CARDS */
.card {
  background: var(--card-bg);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  border: 1px solid var(--border);
  transition: transform 0.2s;
}

.card h2 { margin-top: 0; font-size: 1.25rem; }
.card-header p { font-size: 0.875rem; color: var(--text-light); margin-bottom: 1.5rem; }

.form-grid {
  display: list-item; /* Stack them */
  list-style: none;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

input {
  padding: 0.625rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.2s;
}
input:focus { outline: none; border-color: var(--primary); }

button {
  width: 100%;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 1rem;
  transition: opacity 0.2s;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }

.primary-btn { background: var(--primary); color: white; }
.primary-btn:hover:not(:disabled) { background: var(--primary-hover); }

.secondary-btn { background: var(--text); color: white; }
.secondary-btn:hover:not(:disabled) { background: #334155; }

/* RESULTS */
.result-card {
  border-top: 4px solid var(--primary);
  grid-column: 1 / -1;
}

.results-box {
  margin-top: 1rem;
  padding: 1rem;
  background: #f0fdf4;
  border-radius: 0.5rem;
  display: flex;
  gap: 1rem;
  align-items: center;
  color: #166534;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  background: var(--border);
  font-weight: 700;
}
.badge.maintain { background: #dcfce7; color: #15803d; }
.badge.scale_down { background: #fef9c3; color: #a16207; }
.badge.recovery { background: #fee2e2; color: #b91c1c; }

.rec-body { font-size: 1.125rem; margin-bottom: 1.5rem; }

.action-box {
  background: linear-gradient(to right, #eef2ff, #f8fafc);
  padding: 1rem;
  border-left: 4px solid var(--primary);
  border-radius: 0.25rem;
  margin-bottom: 2rem;
}

.metrics-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.bar-bg {
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  margin-top: 0.5rem;
  overflow: hidden;
}
.bar-fill { height: 100%; background: var(--primary); }

.details { border-top: 1px solid var(--border); padding-top: 1rem; }
.details ul { padding-left: 1.5rem; color: var(--text-light); }

.disabled { opacity: 0.6; pointer-events: none; }
.error-banner { 
  background: #fee2e2; color: #991b1b; padding: 1rem; 
  border-radius: 0.5rem; margin-bottom: 2rem; display: flex; gap: 0.5rem; 
}
'''

jsx = r"""import { useState } from 'react'
import axios from 'axios'
import { Activity, Moon, Zap, Brain, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'
import './App.css'

const API_URL = "http://localhost:8000";

function App() {
  // Phase 1: Training State
  const [trainParams, setTrainParams] = useState({
    history_days: 90,
    avg_steps: 8000,
    steps_volatility: 0.3,
    avg_sleep_hours: 7.5,
    sleep_volatility: 0.2,
    exercise_freq: 3
  });
  const [trainLoading, setTrainLoading] = useState(false);
  const [trainResult, setTrainResult] = useState(null);

  // Phase 2: Prediction State
  const [dailyInput, setDailyInput] = useState({
    steps: 5000,
    sleep_hours: 7.0,
    exercise_minutes: 0
  });
  const [predLoading, setPredLoading] = useState(false);
  const [predResult, setPredResult] = useState(null);
  const [error, setError] = useState(null);

  const handleTrainChange = (e) => {
    setTrainParams({ ...trainParams, [e.target.name]: parseFloat(e.target.value) });
  };

  const handleDailyChange = (e) => {
    setDailyInput({ ...dailyInput, [e.target.name]: parseFloat(e.target.value) });
  };

  const trainModel = async () => {
    setTrainLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API_URL}/simulate-train`, trainParams);
      setTrainResult(res.data);
      // Reset prediction when re-trained
      setPredResult(null);
    } catch (err) {
      setError("Training Failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setTrainLoading(false);
    }
  };

  const predict = async () => {
    setPredLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API_URL}/predict`, dailyInput);
      setPredResult(res.data);
    } catch (err) {
      setError("Prediction Failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setPredLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <div className="logo">
          <Brain size={32} />
          <h1>Habit Engine</h1>
        </div>
        <p>Interactive Behavioral Intelligence Demo</p>
      </header>

      {error && <div className="error-banner"><AlertTriangle size={20} /> {error}</div>}

      <main className="grid">
        {/* SECTION 1: CONFIGURATION */}
        <section className="card config-card">
          <div className="card-header">
            <h2>1. User History Simulation</h2>
            <p>Generate synthetic history to train your personalized model.</p>
          </div>
          
          <div className="form-grid">
            <label>
              <span>History Length (Days)</span>
              <input type="number" name="history_days" value={trainParams.history_days} onChange={handleTrainChange} />
            </label>
            <label>
              <span>Avg Steps / Day</span>
              <input type="number" name="avg_steps" value={trainParams.avg_steps} onChange={handleTrainChange} />
            </label>
            <label>
              <span>Steps Volatility (0-1)</span>
              <input type="number" step="0.1" name="steps_volatility" value={trainParams.steps_volatility} onChange={handleTrainChange} />
            </label>
            <label>
              <span>Avg Sleep (Hours)</span>
              <input type="number" step="0.5" name="avg_sleep_hours" value={trainParams.avg_sleep_hours} onChange={handleTrainChange} />
            </label>
            <label>
              <span>Exercise Freq (Days/Week)</span>
              <input type="number" name="exercise_freq" value={trainParams.exercise_freq} onChange={handleTrainChange} />
            </label>
          </div>

          <button className="primary-btn" onClick={trainModel} disabled={trainLoading}>
            {trainLoading ? "Training Models..." : "Generate & Train"}
          </button>

          {trainResult && (
            <div className="results-box success">
              <CheckCircle size={20} />
              <div>
                <strong>Models Ready!</strong>
                <div className="stats">
                  <span>Datapoints: {trainResult.history_points}</span>
                  <span>Adherence Acc: {(trainResult.adherence_accuracy * 100).toFixed(0)}%</span>
                  <span>Burnout C-Index: {trainResult.burnout_c_index.toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* SECTION 2: INTERACTION */}
        <section className={`card interact-card ${!trainResult ? 'disabled' : ''}`}>
          <div className="card-header">
            <h2>2. Daily Context</h2>
            <p>Input today's signals to get an AI recommendation.</p>
          </div>

          <div className="form-grid">
            <label>
              <Activity size={18} />
              <span>Today's Steps</span>
              <input type="number" name="steps" value={dailyInput.steps} onChange={handleDailyChange} disabled={!trainResult} />
            </label>
            <label>
              <Moon size={18} />
              <span>Last Night Sleep (h)</span>
              <input type="number" step="0.5" name="sleep_hours" value={dailyInput.sleep_hours} onChange={handleDailyChange} disabled={!trainResult} />
            </label>
            <label>
              <Zap size={18} />
              <span>Exercise (mins)</span>
              <input type="number" name="exercise_minutes" value={dailyInput.exercise_minutes} onChange={handleDailyChange} disabled={!trainResult} />
            </label>
          </div>

          <button className="secondary-btn" onClick={predict} disabled={!trainResult || predLoading}>
            {predLoading ? "Analyzing..." : "Analyze Day"}
          </button>
        </section>

        {/* SECTION 3: RESULTS */}
        {predResult && (
          <section className="card result-card">
            <div className="recommendation-header">
              <span className={`badge ${predResult.recommendation_type}`}>
                {predResult.recommendation_type.replace('_', ' ').toUpperCase()}
              </span>
              <h3>{predResult.message_title}</h3>
            </div>
            
            <p className="rec-body">{predResult.message_body}</p>
            
            <div className="action-box">
              <strong>Suggestion:</strong> {predResult.suggested_action}
            </div>

            <div className="metrics-row">
              <div className="metric">
                <small>Adherence Prob</small>
                <strong>{(predResult.adherence_probability * 100).toFixed(1)}%</strong>
                <div className="bar-bg"><div className="bar-fill" style={{width: `${predResult.adherence_probability * 100}%`}}></div></div>
              </div>
              <div className="metric">
                <small>Burnout Risk</small>
                <strong className={predResult.burnout_risk_score > 1.2 ? 'danger-text' : ''}>
                  {predResult.burnout_risk_score.toFixed(2)}x
                </strong>
                <span>Hazard</span>
              </div>
            </div>

            <div className="details">
              <h4>Reasoning:</h4>
              <ul>
                {predResult.why_this_recommendation.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
"""

with open(os.path.join(base, "App.jsx"), "w", encoding="utf-8") as f:
    f.write(jsx)

with open(os.path.join(base, "App.css"), "w", encoding="utf-8") as f:
    f.write(css)

print("Frontend Updated")
