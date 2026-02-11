import uuid
import random
from datetime import datetime, timedelta
from typing import List
from src.domain.schemas import RawHealthEvent, EventType, HealthSource
from src.ingestion.base import HealthDataProvider

class MockHealthProvider(HealthDataProvider):
    """
    Simulated Health Provider for dev & testing.
    Generates realistic-looking data with some noise to test robustness.
    """
    
    def __init__(self, seed: int = 42):
        random.seed(seed)

    def fetch_all_events(self, start_time: datetime, end_time: datetime) -> List[RawHealthEvent]:
        events = []
        events.extend(self.fetch_steps(start_time, end_time))
        events.extend(self.fetch_sleep(start_time, end_time))
        events.extend(self.fetch_exercise(start_time, end_time))
        
        # Sort by start time for realism
        events.sort(key=lambda x: x.start_time)
        return events

    def fetch_steps(self, start_time: datetime, end_time: datetime) -> List[RawHealthEvent]:
        events = []
        current = start_time
        while current < end_time:
            # Simulate bursts of walking during the day (8am - 8pm)
            if 8 <= current.hour <= 20:
                if random.random() > 0.3: # 70% chance of movement in active hours
                    duration_s = random.randint(60, 600)  # 1 to 10 mins walk
                    steps = int(duration_s * random.uniform(1.0, 2.0)) # ~1-2 steps/sec
                    
                    event_end = current + timedelta(seconds=duration_s)
                    if event_end > end_time: break
                    
                    events.append(RawHealthEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=EventType.STEPS,
                        source=HealthSource.MOCK,
                        start_time=current,
                        end_time=event_end,
                        value=steps
                    ))
                    current = event_end + timedelta(minutes=random.randint(5, 60))
                else:
                    current += timedelta(hours=1)
            else:
                # Night time, sparse movement
                current += timedelta(hours=1)
                
        return events

    def fetch_sleep(self, start_time: datetime, end_time: datetime) -> List[RawHealthEvent]:
        events = []
        # Naive simulation: find every "night" in the range
        # Iterate by days
        current_date = start_time.date()
        end_date = end_time.date()
        
        delta = end_date - current_date
        
        for i in range(delta.days + 1):
            day = current_date + timedelta(days=i)
            
            # Simulate sleep start 10pm - 2am
            sleep_hour = random.randint(22, 26) # 22=10pm, 26=2am next day
            start_hour_normalized = sleep_hour if sleep_hour < 24 else sleep_hour - 24
            
            # Create datetime
            if sleep_hour >= 24:
                # It's actually the next morning physically
                sleep_start = datetime.combine(day + timedelta(days=1), datetime.min.time()) + timedelta(hours=start_hour_normalized)
            else:
                sleep_start = datetime.combine(day, datetime.min.time()) + timedelta(hours=start_hour_normalized)
                
            # Random jitter minutes
            sleep_start += timedelta(minutes=random.randint(0, 59))
            
            # Duration 5-9 hours
            duration_hours = random.uniform(5.0, 9.0)
            sleep_end = sleep_start + timedelta(hours=duration_hours)
            
            if sleep_start >= start_time and sleep_end <= end_time:
                events.append(RawHealthEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.SLEEP,
                    source=HealthSource.MOCK,
                    start_time=sleep_start,
                    end_time=sleep_end,
                    value=duration_hours * 60, # Minutes
                    metadata={"efficiency": random.uniform(0.8, 0.99)}
                ))
                
        return events

    def fetch_exercise(self, start_time: datetime, end_time: datetime) -> List[RawHealthEvent]:
        events = []
        # Exercise 3 times a week randomly
        current_date = start_time.date()
        end_date = end_time.date()
        delta = end_date - current_date

        for i in range(delta.days + 1):
            day = current_date + timedelta(days=i)
            
            if random.random() < 0.4: # 40% chance of exercise
                # Random time
                ex_start = datetime.combine(day, datetime.min.time()) + timedelta(hours=random.randint(7, 20))
                duration = random.randint(20, 60) # minutes
                ex_end = ex_start + timedelta(minutes=duration)
                
                if ex_start >= start_time and ex_end <= end_time:
                    events.append(RawHealthEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=EventType.EXERCISE,
                        source=HealthSource.MOCK,
                        start_time=ex_start,
                        end_time=ex_end,
                        value=duration,
                        metadata={"type": random.choice(["running", "cycling", "weightlifting", "yoga"])}
                    ))
        return events
