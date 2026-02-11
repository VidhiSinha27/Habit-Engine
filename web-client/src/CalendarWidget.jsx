import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const CalendarWidget = ({ history }) => {
  // Parse all dates to ensure we have Date objects
  const parsedHistory = React.useMemo(() => {
    return history.map(d => ({
        ...d,
        dateObj: new Date(d.date)
    }));
  }, [history]);

  // Current view state (Year, Month)
  // Initialize to the month of the last data point
  const [currentDate, setCurrentDate] = useState(() => {
    if (parsedHistory.length > 0) {
        return new Date(parsedHistory[parsedHistory.length - 1].date);
    }
    return new Date();
  });

  // Calculate Month Boundaries
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth(); // 0-indexed
  
  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);
  
  const daysInMonth = lastDayOfMonth.getDate();
  const startDayOfWeek = firstDayOfMonth.getDay(); // 0=Sun, 1=Mon...

  // Generate Calendar Grid
  const gridCells = [];
  
  // 1. Padding for previous month
  for (let i = 0; i < startDayOfWeek; i++) {
    gridCells.push({ type: 'empty', key: `empty-${i}` });
  }

  // 2. Days of current month
  for (let d = 1; d <= daysInMonth; d++) {
    // Check history for this specific date
    // Create comparisons as string YYYY-MM-DD
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    
    // Find matching date in history (handling potential timezone issues by just string matching)
    const dayData = parsedHistory.find(h => {
        // Assume h.date is YYYY-MM-DD
        return h.date === dateStr;
    });
    
    gridCells.push({
        type: 'day',
        day: d,
        key: dateStr,
        data: dayData
    });
  }

  // Navigation
  const prevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };
  
  const nextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const monthNames = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  return (
    <div className="card calendar-card">
      <div className="card-header cal-header-flex">
        <div>
            <h2>Activity Log</h2>
            <p>Track your consistency</p>
        </div>
      </div>
      
      <div className="cal-nav">
          <button className="icon-btn" onClick={prevMonth}><ChevronLeft size={20}/></button>
          <span className="month-label">{monthNames[month]} {year}</span>
          <button className="icon-btn" onClick={nextMonth}><ChevronRight size={20}/></button>
      </div>
      
      <div className="calendar-grid">
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
          <div key={i} className="calendar-header">{day}</div>
        ))}
        
        {gridCells.map((cell) => {
            if (cell.type === 'empty') return <div key={cell.key}></div>;
            
            const isDone = cell.data?.exercise_done;
            return (
                <div key={cell.key} className={`calendar-day ${isDone ? 'active' : ''} ${!cell.data ? 'future' : ''}`}>
                    <span className="day-number">{cell.day}</span>
                    {isDone && <div className="indicator"></div>}
                </div>
            );
        })}
      </div>
      
      <div className="calendar-legend">
        <div className="legend-item">
            <div className="dot active"></div>
            <span>Done</span>
        </div>
        <div className="legend-item">
            <div className="dot"></div>
            <span>Rest</span>
        </div>
      </div>
    </div>
  );
};

export default CalendarWidget;