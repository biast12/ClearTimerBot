import re
import pytz
from datetime import datetime, timedelta
from typing import Tuple, Union
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class TimerParseError(ValueError):
    pass


class TimerParser:
    TIMEZONE_PATTERN = re.compile(r"^(\d{1,2}:\d{2})\s*([A-Z][\w+-]*)?\s*$")
    INTERVAL_PATTERN = re.compile(r"^(?:(\d+)d)?(?:(\d+)h(?:r)?)?(?:(\d+)m)?$")

    def __init__(self, timezone_resolver):
        self.timezone_resolver = timezone_resolver

    def parse(
        self, timer_string: str
    ) -> Tuple[Union[CronTrigger, IntervalTrigger], datetime]:
        if not timer_string:
            raise TimerParseError("Timer string cannot be empty")

        timer_string = timer_string.strip()

        # Try to parse as daily scheduled time
        if match := self.TIMEZONE_PATTERN.match(timer_string):
            return self._parse_scheduled_time(match)

        # Try to parse as interval
        if match := self.INTERVAL_PATTERN.match(timer_string):
            return self._parse_interval(match)

        raise TimerParseError(
            f"Invalid timer format: '{timer_string}'. "
            "Use '1d2h3m' for intervals or 'HH:MM TIMEZONE' for daily schedules."
        )

    def _parse_scheduled_time(self, match: re.Match) -> Tuple[CronTrigger, datetime]:
        time_str = match.group(1)
        timezone_abbr = match.group(2) or "GMT"

        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except ValueError:
            raise TimerParseError(
                f"Invalid time format: '{time_str}'. Use HH:MM format."
            )

        timezone_str = self.timezone_resolver(timezone_abbr)
        if not timezone_str:
            raise TimerParseError(f"Unknown timezone: '{timezone_abbr}'")

        try:
            timezone = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            raise TimerParseError(f"Invalid timezone mapping for '{timezone_abbr}'")

        # Calculate next run time
        now = datetime.now(timezone)
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(days=1)

        trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)
        return trigger, next_run

    def _parse_interval(self, match: re.Match) -> Tuple[IntervalTrigger, datetime]:
        days = int(match.group(1) or 0)
        # Handle hours - group 2 might include 'hr' or just 'h'
        hours_str = match.group(2) or "0"
        hours = int(hours_str.replace('hr', '').replace('h', '') or 0)
        minutes = int(match.group(3) or 0)

        if days == 0 and hours == 0 and minutes == 0:
            raise TimerParseError("Timer interval cannot be zero.")

        if days > 365:
            raise TimerParseError("Timer interval cannot exceed 365 days.")

        total_minutes = (days * 24 * 60) + (hours * 60) + minutes

        if total_minutes < 1:
            raise TimerParseError("Timer interval must be at least 1 minute.")

        delta = timedelta(days=days, hours=hours, minutes=minutes)
        next_run = datetime.now(pytz.UTC) + delta

        trigger = IntervalTrigger(minutes=total_minutes)
        return trigger, next_run
