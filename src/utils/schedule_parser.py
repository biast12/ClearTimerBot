import re
import pytz
from datetime import datetime, timedelta
from typing import Tuple, Union, Callable, Optional
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class ScheduleParseError(ValueError):
    pass


class ScheduleExpressionParser:
    TIMEZONE_PATTERN = re.compile(r"^(\d{1,2}:\d{2})\s*([A-Z][\w+-]*)?\s*$")
    INTERVAL_PATTERN = re.compile(r"^(?:(\d+)d)?(?:(\d+)h(?:r)?)?(?:(\d+)m)?$")
    FRACTION_TIME_PATTERN = re.compile(
        r"^(\d+)/(\d+)\s+(\d{1,2}:\d{2})(?:\s+([A-Z][\w+-]*))?$"
    )
    WEEKLY_PATTERN = re.compile(
        r"^((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:[,-](?:Mon|Tue|Wed|Thu|Fri|Sat|Sun))*)\s+(\d{1,2}:\d{2})(?:\s+([A-Z][\w+-]*))?\s*$",
        re.IGNORECASE,
    )
    VALID_DAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
    DAY_ORDER = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

    def __init__(
        self,
        timezone_resolver: Callable[[str], Optional[str]],
        get_server_timezone_func: Optional[
            Callable[[str, Optional[str]], Optional[str]]
        ] = None,
    ) -> None:
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

        # Try to parse as fractional time (e.g., "1/4 15:30 EST")
        if match := self.FRACTION_TIME_PATTERN.match(timer_string):
            return self._parse_fractional_time_schedule(match, server_id)

        # Try to parse as weekly schedule (e.g., "Mon 15:30 EST", "Mon-Fri 09:00")
        if match := self.WEEKLY_PATTERN.match(timer_string):
            return self._parse_weekly_cron_schedule(match, server_id)

        # Try to parse as daily scheduled time
        if match := self.TIMEZONE_PATTERN.match(timer_string):
            return self._parse_daily_cron_schedule(match, server_id)

        # Try to parse as interval
        if match := self.INTERVAL_PATTERN.match(timer_string):
            return self._parse_interval_schedule(match)

        raise ScheduleParseError(
            f"Invalid timer format: '{timer_string}'. "
            "Use '1d2h3m' for intervals, '24' for hours, '1/2 HH:MM TIMEZONE' for fractional time, 'HH:MM TIMEZONE' for daily schedules, or 'Mon 15:30 EST' for weekly."
        )

    def _parse_fractional_time_schedule(
        self, match: re.Match, server_id: str = None
    ) -> Tuple[CronTrigger, datetime]:
        numerator = int(match.group(1))
        denominator = int(match.group(2))
        time_str = match.group(3)
        timezone_abbr = match.group(4)

        # Validate fraction
        if denominator == 0:
            raise ScheduleParseError("Denominator cannot be zero")
        if numerator == 0:
            raise ScheduleParseError("Numerator cannot be zero")
        if numerator != 1:
            raise ScheduleParseError(
                f"Only unit fractions (1/n) are supported. Got {numerator}/{denominator}"
            )

        # Check if denominator is a factor of 24
        if 24 % denominator != 0:
            raise ScheduleParseError(
                f"Denominator {denominator} must be a factor of 24 (valid: 1, 2, 3, 4, 6, 8, 12, 24)"
            )

        # Parse the time
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except ValueError:
            raise ScheduleParseError(
                f"Invalid time format: '{time_str}'. Use HH:MM format."
            )

        # Get timezone
        if not timezone_abbr and server_id and self.get_server_timezone:
            timezone_str = self.get_server_timezone(server_id, None)
        else:
            timezone_abbr = timezone_abbr or "GMT"
            timezone_str = self.timezone_resolver(timezone_abbr)
            if not timezone_str:
                raise ScheduleParseError(f"Unknown timezone: '{timezone_abbr}'")

        try:
            timezone = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ScheduleParseError(f"Invalid timezone mapping for '{timezone_abbr}'")

        # Calculate hour interval (how many hours between runs)
        hour_interval = 24 // denominator

        # Generate all hours when the task should run
        run_hours = []
        current_hour = hour
        for _ in range(denominator):
            run_hours.append(current_hour)
            current_hour = (current_hour + hour_interval) % 24

        # Create cron trigger that runs at specified hours
        # Sort and deduplicate hours
        hours_str = ",".join(map(str, sorted(set(run_hours))))
        trigger = CronTrigger(hour=hours_str, minute=minute, timezone=timezone)

        # Calculate next run time
        now = datetime.now(timezone)
        next_run = None

        # Find the next run time from the list of hours
        for run_hour in sorted(run_hours):
            potential_time = now.replace(
                hour=run_hour, minute=minute, second=0, microsecond=0
            )
            if potential_time > now:
                next_run = potential_time
                break

        # If no time found today, use the first time tomorrow
        if next_run is None:
            next_run = now.replace(
                hour=run_hours[0], minute=minute, second=0, microsecond=0
            )
            next_run += timedelta(days=1)

        return trigger, next_run

    def _parse_daily_cron_schedule(
        self, match: re.Match, server_id: str = None
    ) -> Tuple[CronTrigger, datetime]:
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

    def _parse_interval_schedule(
        self, match: re.Match
    ) -> Tuple[IntervalTrigger, datetime]:
        days = int(match.group(1) or 0)
        # Handle hours - group 2 might include 'hr' or just 'h'
        hours_str = match.group(2) or "0"
        hours = int(hours_str.replace("hr", "").replace("h", "") or 0)
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

    def _parse_weekly_cron_schedule(
        self, match: re.Match, server_id: str = None
    ) -> Tuple[CronTrigger, datetime]:
        days_str = match.group(1)
        time_str = match.group(2)
        timezone_abbr = match.group(3)

        # Parse time
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except ValueError:
            raise ScheduleParseError(
                f"Invalid time format: '{time_str}'. Use HH:MM format."
            )

        # Expand day spec into individual day names
        day_parts = self._expand_day_spec(days_str)

        # Get timezone
        if not timezone_abbr and server_id and self.get_server_timezone:
            timezone_str = self.get_server_timezone(server_id, None)
        else:
            timezone_abbr = timezone_abbr or "GMT"
            timezone_str = self.timezone_resolver(timezone_abbr)
            if not timezone_str:
                raise ScheduleParseError(f"Unknown timezone: '{timezone_abbr}'")

        try:
            timezone = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ScheduleParseError(f"Invalid timezone mapping for '{timezone_abbr}'")

        # Build APScheduler day_of_week string
        day_of_week = ",".join(day_parts)

        trigger = CronTrigger(
            day_of_week=day_of_week, hour=hour, minute=minute, timezone=timezone
        )

        # Calculate next run time
        next_run = self._find_next_weekly_run(
            datetime.now(timezone), day_parts, hour, minute, timezone
        )

        return trigger, next_run

    def _expand_day_spec(self, days_str: str) -> list:
        """Expand a day spec like 'Mon-Fri,Sun' into ['mon', 'tue', 'wed', 'thu', 'fri', 'sun']."""
        ordered_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        result = set()

        for part in days_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                start = start.strip().lower()
                end = end.strip().lower()
                if start not in self.VALID_DAYS or end not in self.VALID_DAYS:
                    raise ScheduleParseError(
                        f"Invalid day name in range: '{part}'. Use Mon, Tue, Wed, Thu, Fri, Sat, Sun."
                    )
                start_idx = self.DAY_ORDER[start]
                end_idx = self.DAY_ORDER[end]
                if start_idx <= end_idx:
                    for i in range(start_idx, end_idx + 1):
                        result.add(ordered_days[i])
                else:
                    # Wrap-around range (e.g., Fri-Mon)
                    for i in range(start_idx, 7):
                        result.add(ordered_days[i])
                    for i in range(0, end_idx + 1):
                        result.add(ordered_days[i])
            else:
                day = part.lower()
                if day not in self.VALID_DAYS:
                    raise ScheduleParseError(
                        f"Invalid day name: '{part}'. Use Mon, Tue, Wed, Thu, Fri, Sat, Sun."
                    )
                result.add(day)

        # Return sorted by day order
        return sorted(result, key=lambda d: self.DAY_ORDER[d])

    def _find_next_weekly_run(
        self,
        now: datetime,
        day_parts: list,
        hour: int,
        minute: int,
        timezone,
    ) -> datetime:
        """Find the next datetime that matches one of the specified days at the given time."""
        # Map day names to Python weekday numbers (Monday=0)
        target_weekdays = {self.DAY_ORDER[d] for d in day_parts}

        for offset in range(8):  # Check up to 7 days ahead + today
            candidate = now + timedelta(days=offset)
            if candidate.weekday() in target_weekdays:
                run_time = candidate.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                if run_time > now:
                    return run_time

        # Fallback: shouldn't reach here with valid days, but use first matching day next week
        candidate = now + timedelta(days=7)
        return candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)
