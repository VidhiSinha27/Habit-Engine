from typing import List, Dict
from datetime import date, timedelta
from collections import defaultdict
import numpy as np

from src.domain.schemas import RawHealthEvent, DailyBehavior, EventType

class DailyAggregator:
    def __init__(self):
        pass

    def aggregate(self, events: List[RawHealthEvent]) -> List[DailyBehavior]:
        """
        Converts a stream of raw events into DailyBehavior rows.
        """
        # Group by "Reporting Date" for the behavior
        # Strategy:
        # - Steps/Exercise: Assigned to the calendar date of the start_time (local)
        # - Sleep: Assigned to the date of the *end_time* (The "Wake Up" day)
        
        day_buckets = defaultdict(lambda: {
            "steps": [],
            "exercise": [],
            "sleep": []
        })
        
        for e in events:
            if e.event_type == EventType.SLEEP:
                # Assign to wake-up day
                bucket_date = e.end_time.date()
                day_buckets[bucket_date]["sleep"].append(e)
            else:
                # Assign to calendar day
                bucket_date = e.start_time.date()
                if e.event_type == EventType.STEPS:
                    day_buckets[bucket_date]["steps"].append(e)
                elif e.event_type == EventType.EXERCISE:
                    day_buckets[bucket_date]["exercise"].append(e)

        results = []
        
        # Sort dates to ensure order
        sorted_dates = sorted(day_buckets.keys())
        
        for d in sorted_dates:
            data = day_buckets[d]
            
            # --- STEPS ---
            total_steps = sum(int(s.value) for s in data["steps"])
            
            # --- EXERCISE ---
            ex_events = data["exercise"]
            ex_minutes = sum(float(x.value) for x in ex_events)
            is_exercise_done = ex_minutes > 15 # Threshold for "Active" flag? Or just > 0. Let's start with > 0.
            # Actually prompt said 0/1, let's strictly say > 0 implies 1.
            # Also finding first exercise time
            first_ex_time = min((x.start_time for x in ex_events), default=None)
            
            # --- SLEEP ---
            sleep_events = data["sleep"]
            # Assuming main sleep is the longest one if multiple
            main_sleep = max(sleep_events, key=lambda x: x.value) if sleep_events else None
            
            sleep_start = main_sleep.start_time if main_sleep else None
            sleep_end = main_sleep.end_time if main_sleep else None
            sleep_dur = main_sleep.value if main_sleep else 0.0
            
            # --- DERIVED ---
            # Sedentary Proxy: (Minutes in Day - Sleep - Exercise) / (Steps / Constant) ? 
            # Simple version: Inverse of activity. 
            # 1440 mins - sleep - exercise = Awake Sedentary Potential.
            # If steps are low, high sedentary.
            # Let's just calculate "Wake time not moving" logic roughly if we had full timeline.
            # For now, just placeholder or simple formula.
            awake_time = 1440 - sleep_dur
            sedentary_calc = awake_time - ex_minutes # Very rough
            
            daily = DailyBehavior(
                date=d,
                total_steps=total_steps,
                exercise_minutes=ex_minutes,
                exercise_done=bool(ex_minutes > 0),
                exercise_start_time=first_ex_time,
                sleep_start_time=sleep_start,
                sleep_end_time=sleep_end,
                sleep_duration_minutes=sleep_dur,
                sedentary_minutes=max(0.0, sedentary_calc),
                data_missing_flag=(total_steps == 0 and sleep_dur == 0)
            )
            results.append(daily)
            
        return results
