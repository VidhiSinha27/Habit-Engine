from typing import List, Dict, Any
from src.domain.api_schemas import EngineResponse, RecommendationType

class RecommendationEngine:
    """
    Rule-based Logic Layer that translates ML signals into User Actions.
    """
    
    def generate_recommendation(
        self, 
        user_id: str,
        date_str: str,
        adherence_prob: float, 
        burnout_risk: float, 
        is_anomaly: bool,
        recent_features: Dict[str, Any]
    ) -> EngineResponse:
        
        reasons = []
        rec_type = RecommendationType.MAINTAIN
        title = "Keep it up!"
        body = "You're on track."
        action = "Complete your standard session."

        # LOGIC HIERARCHY (Safety First)

        # 0. SEVERE SLEEP DEPRIVATION (Hard Rule)
        # Check raw sleep minutes from the current day's feature row
        current_sleep = recent_features.get('sleep_duration_minutes', 480) # default 8h if missing
        if current_sleep < 180: # Less than 3 hours
            rec_type = RecommendationType.RECOVERY
            title = "Sleep First, Train Later"
            body = "You got less than 3 hours of sleep. Training now is counter-productive and dangerous."
            action = "Skip the workout. Go get a nap or go to bed early tonight."
            reasons.append(f"Severe sleep deprivation detected ({current_sleep/60:.1f} hours).")
            reasons.append("Cognitive and physical recovery is severely compromised.")
        
        # 1. ANOMALY / ACUTE DISTRESS CHECK
        elif is_anomaly:
            rec_type = RecommendationType.RECOVERY
            title = "Check-in time"
            body = "We noticed some unusual patterns today. Everything okay?"
            action = "Log a quick mood check-in instead of a workout."
            reasons.append("Behavioral anomaly detected (isolation forest).")

        # 2. BURNOUT RISK CHECK (High Hazard Score)
        elif burnout_risk > 1.2: # Threshold relative to baseline 1.0
            rec_type = RecommendationType.SCALE_DOWN
            title = "Protect your energy"
            body = "Your stats suggest you're pushing hard. Let's avoid burnout."
            action = "Do 50% of your planned duration today."
            reasons.append(f"High burnout risk score ({burnout_risk:.2f}).")
            reasons.append("Recent effort ratio is unsustainable.")

        # 3. LOW ADHERENCE (< 40%) - Reassurance & Reset
        elif adherence_prob < 0.4:
            rec_type = RecommendationType.ANCHORING
            missed_days = recent_features.get('consecutive_misses', 0)
            
            if missed_days <= 7:
                title = "Don't break the chain"
                body = "You missed a few days, but it happens. The key is to get back to it immediately to keep your habit strong."
            else:
                title = "Everything okay?"
                body = "We noticed you've been away for a bit. Don't worry—failures are just data points on the road to success. We can get back on the wagon today."
            
            action = "Start small: Just do 5 minutes of movement to break the seal."
            reasons.append(f"Low adherence probability ({adherence_prob:.1%}).")
            reasons.append("Focus is on re-establishing the habit loop, not intensity.")

        # 4. MODERATE-LOW ADHERENCE (40-50%) - Nudge to Push
        elif adherence_prob < 0.5:
            rec_type = RecommendationType.MAINTAIN
            title = "Time to Shift Gears"
            body = "You've missed a few days, but momentum is waiting for you. Try pushing a little harder today to get back on track."
            action = "Commit to your standard session today—you can do this."
            reasons.append(f"Adherence probability is borderline ({adherence_prob:.1%}).")
            reasons.append("A strong session today will reverse the negative trend.")

        # 5. MODERATE-HIGH ADHERENCE (50-70%) - Encouragement
        elif adherence_prob <= 0.7:
            rec_type = RecommendationType.MAINTAIN
            title = "Good Work"
            body = "You are doing well! Hang in there and keep the momentum building."
            action = "Stick to the plan. Consistency is compounding."
            reasons.append(f"Stable adherence probability ({adherence_prob:.1%}).")
            
        # 6. HIGH ADHERENCE (> 70%) - Praise
        else:
            rec_type = RecommendationType.MAINTAIN
            title = "Keep It Up!"
            body = "Excellent dedication. You're consistently showing up and the results show."
            action = "Use this momentum to your advantage—great day for a PR or just enjoying the flow."
            reasons.append(f"High adherence probability ({adherence_prob:.1%}).")

        return EngineResponse(
            user_id=user_id,
            date=date_str,
            adherence_probability=adherence_prob,
            burnout_risk_score=burnout_risk,
            is_anomaly=is_anomaly,
            recommendation_type=rec_type,
            message_title=title,
            message_body=body,
            suggested_action=action,
            why_this_recommendation=reasons
        )
