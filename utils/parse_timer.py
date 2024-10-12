import re
import pytz
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from utils.data_manager import get_timezone

def parse_timer(timer: str):
    timezone_pattern = r'(\d{1,2}:\d{2})\s*([A-Z]*)'
    timezone_matches = re.match(timezone_pattern, timer)

    if timezone_matches:
        time_str = timezone_matches.group(1)
        timezone_abbr = timezone_matches.group(2) or 'GMT'
        hour, minute = map(int, time_str.split(':'))
        timezone = get_timezone(timezone_abbr)
        if timezone is None:
            raise ValueError(f"Invalid timezone abbreviation: {timezone_abbr}")
        next_run_time = datetime.now(timezone).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run_time < datetime.now(timezone):
            next_run_time += timedelta(days=1)
        trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)
    else:
        pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?'
        matches = re.match(pattern, timer)
        if matches:
            days = int(matches.group(1) or 0)
            hours = int(matches.group(2) or 0)
            minutes = int(matches.group(3) or 0)
            if days == 0 and hours == 0 and minutes == 0:
                raise ValueError("Timer duration cannot be zero.")
            delta = timedelta(days=days, hours=hours, minutes=minutes)
            next_run_time = datetime.now(pytz.UTC) + delta
            total_minutes = (days * 24 * 60) + (hours * 60) + minutes
            trigger = IntervalTrigger(minutes=total_minutes)
        else:
            raise ValueError("Invalid timer format. Use '1d2h3m' or 'HH:MM <timezone>' format for durations.")
    return trigger, next_run_time