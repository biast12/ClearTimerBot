import re
import pytz
from datetime import datetime, timedelta
from typing import Tuple, Union
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class ScheduleParseError(ValueError):
    pass


class ScheduleExpressionParser:
    TIMEZONE_PATTERN = re.compile(r"^(\d{1,2}:\d{2})\s*([A-Z][\w+-]*)?\s*$")
    INTERVAL_PATTERN = re.compile(r"^(?:(\d+)d)?(?:(\d+)h(?:r)?)?(?:(\d+)m)?$")

    def __init__(self, timezone_resolver, get_server_timezone_func=None):
        self.timezone_resolver = timezone_resolver
        self.get_server_timezone = get_server_timezone_func

    def parse_schedule_expression(
        self, timer_string: str, server_id: str = None
    ) -> Tuple[Union[CronTrigger, IntervalTrigger], datetime]:
        if not timer_string:
            raise ScheduleParseError("Timer string cannot be empty")

        timer_string = timer_string.strip()

        # Check if it's just a number (interpret as hours)
        if timer_string.isdigit():
            hours = int(timer_string)
            if hours < 1:
                raise ScheduleParseError("Hour value must be at least 1")
            
            total_minutes = hours * 60
            delta = timedelta(hours=hours)
            next_run = datetime.now(pytz.UTC) + delta
            trigger = IntervalTrigger(minutes=total_minutes)
            return trigger, next_run

        # Try to parse as daily scheduled time
        if match := self.TIMEZONE_PATTERN.match(timer_string):
            return self._parse_daily_cron_schedule(match, server_id)

        # Try to parse as interval
        if match := self.INTERVAL_PATTERN.match(timer_string):
            return self._parse_interval_schedule(match)

        raise ScheduleParseError(
            f"Invalid timer format: '{timer_string}'. "
            "Use '1d2h3m' for intervals, '24' for hours, or 'HH:MM TIMEZONE' for daily schedules."
        )

    def _parse_daily_cron_schedule(self, match: re.Match, server_id: str = None) -> Tuple[CronTrigger, datetime]:
        time_str = match.group(1)
        timezone_abbr = match.group(2)

        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except ValueError:
            raise ScheduleParseError(
                f"Invalid time format: '{time_str}'. Use HH:MM format."
            )

        # If no timezone specified in the command, use server's timezone if available
        if not timezone_abbr and server_id and self.get_server_timezone:
            timezone_str = self.get_server_timezone(server_id, None)
        else:
            # Use provided timezone or default to GMT
            timezone_abbr = timezone_abbr or "GMT"
            timezone_str = self.timezone_resolver(timezone_abbr)
            if not timezone_str:
                raise ScheduleParseError(f"Unknown timezone: '{timezone_abbr}'")

        try:
            timezone = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ScheduleParseError(f"Invalid timezone mapping for '{timezone_abbr}'")

        # Calculate next run time
        now = datetime.now(timezone)
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(days=1)

        trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)
        return trigger, next_run

    def _parse_interval_schedule(self, match: re.Match) -> Tuple[IntervalTrigger, datetime]:
        days = int(match.group(1) or 0)
        # Handle hours - group 2 might include 'hr' or just 'h'
        hours_str = match.group(2) or "0"
        hours = int(hours_str.replace('hr', '').replace('h', '') or 0)
        minutes = int(match.group(3) or 0)

        if days == 0 and hours == 0 and minutes == 0:
            raise ScheduleParseError("Timer interval cannot be zero.")

        total_minutes = (days * 24 * 60) + (hours * 60) + minutes

        if total_minutes < 1:
            raise ScheduleParseError("Timer interval must be at least 1 minute.")

        delta = timedelta(days=days, hours=hours, minutes=minutes)
        next_run = datetime.now(pytz.UTC) + delta

        trigger = IntervalTrigger(minutes=total_minutes)
        return trigger, next_run
