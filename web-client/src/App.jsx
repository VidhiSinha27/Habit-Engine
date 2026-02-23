import { useState, useEffect } from 'react'
import axios from 'axios'
import { Activity, Moon, Zap, Brain, TrendingUp, AlertTriangle, CheckCircle, Save, Edit3 } from 'lucide-react'
import CalendarWidget from './CalendarWidget'
import './App.css'
import './TableEditor.css'

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
  
  // Custom Data Editor State
  const [historyData, setHistoryData] = useState([]);
  const [isEditing, setIsEditing] = useState(false);

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
      if (res.data.history) {
        setHistoryData(res.data.history);
      }
      // Reset prediction when re-trained
      setPredResult(null);
    } catch (err) {
      setError("Training Failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setTrainLoading(false);
    }
  };

  const retrainWithCustomData = async () => {
    setTrainLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API_URL}/train-custom`, { history: historyData });
      setTrainResult(res.data);
      if (res.data.history) {
        setHistoryData(res.data.history);
      }
      setPredResult(null);
      setIsEditing(false);
    } catch (err) {
       setError("Retraining Failed: " + (err.response?.data?.detail || err.message));
    } finally {
       setTrainLoading(false);
    }
  };

  const handleHistoryChange = (index, field, value) => {
    const newData = [...historyData];
    // Special handling for numbers and checkboxes
    if (field === 'exercise_done') {
        newData[index][field] = value;
        // Auto-update mins if toggled
        if (value && newData[index].exercise_minutes === 0) newData[index].exercise_minutes = 45;
        if (!value) newData[index].exercise_minutes = 0;
    } else {
        newData[index][field] = field === 'date' ? value : Number(value);
    }
    setHistoryData(newData);
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

  // Auto-predict when inputs change
  useEffect(() => {
    if (trainResult) {
      const timer = setTimeout(() => {
        predict();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [dailyInput, trainResult]);

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

      {error && <div className="error-banner"><AlertTriangle size={20} /> {error}</div>}

      <div className="dashboard-layout">
        
        {/* LEFT COLUMN: Main Controls */}
        <div className="main-column">
          
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

            {/* DATA EDITOR */}
            {historyData.length > 0 && (
                <div className="data-editor-section">
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem'}}>
                        <h3>Data Inspector</h3>
                        <button className="btn btn-outline" onClick={() => setIsEditing(!isEditing)}>
                             {isEditing ? 'Close Editor' : <><Edit3 size={16}/> Edit Data</>}
                        </button>
                    </div>

                    {isEditing && (
                        <div className="data-editor-container">
                             <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Steps</th>
                                        <th>Sleep (min)</th>
                                        <th>Exercise Mins</th>
                                        <th>Done?</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {historyData.slice().reverse().map((row, i) => {
                                        // array is reversed for display so we need real index
                                        const realIndex = historyData.length - 1 - i; 
                                        return (
                                        <tr key={i}>
                                            <td>{row.date}</td>
                                            <td>
                                                <input 
                                                    type="number" 
                                                    value={row.total_steps} 
                                                    onChange={(e) => handleHistoryChange(realIndex, 'total_steps', e.target.value)}
                                                />
                                            </td>
                                            <td>
                                                <input 
                                                    type="number" 
                                                    value={row.sleep_duration_minutes} 
                                                    onChange={(e) => handleHistoryChange(realIndex, 'sleep_duration_minutes', e.target.value)}
                                                />
                                            </td>
                                            <td>
                                                <input 
                                                    type="number" 
                                                    value={row.exercise_minutes} 
                                                    onChange={(e) => handleHistoryChange(realIndex, 'exercise_minutes', e.target.value)}
                                                />
                                            </td>
                                            <td>
                                                <input 
                                                    type="checkbox" 
                                                    checked={row.exercise_done} 
                                                    onChange={(e) => handleHistoryChange(realIndex, 'exercise_done', e.target.checked)}
                                                />
                                            </td>
                                        </tr>
                                    )})}
                                </tbody>
                             </table>
                        </div>
                    )}
                    
                    {isEditing && (
                        <div className="edit-actions">
                            <button className="btn btn-primary" onClick={retrainWithCustomData} disabled={trainLoading}>
                                <Save size={16} /> Save & Retrain
                            </button>
                        </div>
                    )}
                </div>
            )}
          </section>

          {/* SECTION 3: RESULTS (Inside Main Column) */}
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

        </div>

        {/* RIGHT COLUMN: Calendar (Sidebar) */}
        <div className="side-column">
          {trainResult && trainResult.history && (
              <CalendarWidget history={trainResult.history} />
          )}
        </div>

      </div>
    </div>
  )
}

export default App
