import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from src.models import ErrorDocument, LogArea, LogLevel


class BotLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self.console_enabled = True
            self.db_enabled = True
            self.min_level = LogLevel.INFO

    def _get_color(self, level: LogLevel) -> str:
        colors = {
            LogLevel.DEBUG: "\033[90m",  # Gray
            LogLevel.INFO: "\033[92m",  # Green
            LogLevel.WARNING: "\033[93m",  # Yellow
            LogLevel.ERROR: "\033[91m",  # Red
            LogLevel.CRITICAL: "\033[95m",  # Magenta
            LogLevel.NONE: "\033[37m",  # White/default
        }
        return colors.get(level, "")

    def _reset_color(self) -> str:
        return "\033[0m"

    def _should_log(self, level: LogLevel) -> bool:
        if level == LogLevel.NONE:
            return True
        level_order = [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL,
        ]
        return level_order.index(level) >= level_order.index(self.min_level)

    def _format_message(self, level: LogLevel, area: LogArea, message: str) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        color = self._get_color(level)
        reset = self._reset_color()

        if level == LogLevel.NONE and area == LogArea.NONE:
            return f"{color}[{timestamp}] {message}{reset}"
        elif level == LogLevel.NONE:
            return f"{color}[{timestamp}] [{area.value:10}] {message}{reset}"
        elif area == LogArea.NONE:
            return f"{color}[{timestamp}] [{level.value:8}] {message}{reset}"
        else:
            return f"{color}[{timestamp}] [{level.value:8}] [{area.value:10}] {message}{reset}"

    async def _save_error_to_db(self, error_record: ErrorDocument) -> None:
        if not self.db_enabled:
            return

        try:
            from src.services.database_connection_manager import db_manager

            await db_manager.execute(
                """
                INSERT INTO errors
                    (error_id, timestamp, level, area, message, stack_trace,
                     guild_id, channel_id, user_id, command)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (error_id) DO NOTHING
                """,
                error_record.error_id,
                error_record.timestamp,
                error_record.level,
                error_record.area,
                error_record.message,
                error_record.stack_trace,
                error_record.guild_id,
                error_record.channel_id,
                error_record.user_id,
                error_record.command,
            )
        except Exception as e:
            print(f"Failed to save error to database: {e}")

    def log(
        self, level: LogLevel, area: LogArea, message: str, **kwargs
    ) -> Optional[str]:
        if not self._should_log(level):
            return None

        if self.console_enabled:
            formatted = self._format_message(level, area, message)
            try:
                print(formatted)
            except UnicodeEncodeError:
                safe = formatted.encode(
                    sys.stdout.encoding or "utf-8", errors="replace"
                ).decode(sys.stdout.encoding or "utf-8")
                print(safe)

        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            return self._generate_error_id()

        return None

    async def log_error(
        self,
        area: LogArea,
        message: str,
        exception: Optional[Exception] = None,
        server_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        user_id: Optional[str] = None,
        command: Optional[str] = None,
        **additional_data,
    ) -> str:
        error_id = str(uuid.uuid4())[:8]

        tb_str = ""
        if exception:
            tb_str = "".join(
                traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            )
        elif sys.exc_info()[0]:
            tb_str = traceback.format_exc()

        error_record = ErrorDocument(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.ERROR.value,
            area=area.value if hasattr(area, "value") else str(area),
            message=message,
            stack_trace=tb_str,
            guild_id=server_id,
            channel_id=channel_id,
            user_id=user_id,
            command=command,
        )

        if self.console_enabled:
            formatted = self._format_message(
                LogLevel.ERROR, area, f"{message} [Error ID: {error_id}]"
            )
            try:
                print(formatted)
            except UnicodeEncodeError:
                safe = formatted.encode(
                    sys.stdout.encoding or "utf-8", errors="replace"
                ).decode(sys.stdout.encoding or "utf-8")
                print(safe)
            if tb_str and self.min_level == LogLevel.DEBUG:
                try:
                    print(tb_str)
                except UnicodeEncodeError:
                    safe_tb = tb_str.encode(
                        sys.stdout.encoding or "utf-8", errors="replace"
                    ).decode(sys.stdout.encoding or "utf-8")
                    print(safe_tb)

        await self._save_error_to_db(error_record)

        return error_id

    def _generate_error_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def debug(self, area: LogArea, message: str, **kwargs) -> None:
        self.log(LogLevel.DEBUG, area, message, **kwargs)

    def info(self, area: LogArea, message: str, **kwargs) -> None:
        self.log(LogLevel.INFO, area, message, **kwargs)

    def warning(self, area: LogArea, message: str, **kwargs) -> None:
        self.log(LogLevel.WARNING, area, message, **kwargs)

    def error(self, area: LogArea, message: str, **kwargs) -> Optional[str]:
        return self.log(LogLevel.ERROR, area, message, **kwargs)

    def critical(self, area: LogArea, message: str, **kwargs) -> Optional[str]:
        return self.log(LogLevel.CRITICAL, area, message, **kwargs)

    def print(self, message: str, **kwargs) -> None:
        self.log(LogLevel.NONE, LogArea.NONE, message, **kwargs)

    def spacer(
        self,
        char: str = "=",
        length: Optional[int] = None,
        color: Optional[LogLevel] = None,
    ) -> None:
        if length is None:
            try:
                terminal_width = os.get_terminal_size().columns
            except (OSError, AttributeError):
                terminal_width = 100
        else:
            terminal_width = length

        color_code = self._get_color(color) if color else "\033[36m"
        reset = self._reset_color()
        output = f"{color_code}{char * terminal_width}{reset}"
        try:
            print(output)
        except UnicodeEncodeError:
            safe = output.encode(
                sys.stdout.encoding or "utf-8", errors="replace"
            ).decode(sys.stdout.encoding or "utf-8")
            print(safe)

    async def get_error(self, error_id: str) -> Optional[ErrorDocument]:
        try:
            from src.services.database_connection_manager import db_manager

            row = await db_manager.fetchrow(
                "SELECT * FROM errors WHERE error_id = $1", error_id
            )
            if row:
                return ErrorDocument(
                    error_id=row["error_id"],
                    timestamp=row["timestamp"],
                    level=row["level"],
                    area=row["area"],
                    message=row["message"],
                    stack_trace=row["stack_trace"],
                    guild_id=row["guild_id"],
                    channel_id=row["channel_id"],
                    user_id=row["user_id"],
                    command=row["command"],
                )
            return None
        except Exception:
            return None

    async def delete_error(self, error_id: str) -> bool:
        try:
            from src.services.database_connection_manager import db_manager

            result = await db_manager.execute(
                "DELETE FROM errors WHERE error_id = $1", error_id
            )
            return result == "DELETE 1"
        except Exception:
            return False

    async def get_recent_errors(
        self, limit: int = 10, guild_id: Optional[str] = None
    ) -> List[ErrorDocument]:
        try:
            from src.services.database_connection_manager import db_manager

            if guild_id:
                rows = await db_manager.fetch(
                    "SELECT * FROM errors WHERE guild_id = $1 ORDER BY timestamp DESC LIMIT $2",
                    guild_id,
                    limit,
                )
            else:
                rows = await db_manager.fetch(
                    "SELECT * FROM errors ORDER BY timestamp DESC LIMIT $1",
                    limit,
                )

            return [
                ErrorDocument(
                    error_id=row["error_id"],
                    timestamp=row["timestamp"],
                    level=row["level"],
                    area=row["area"],
                    message=row["message"],
                    stack_trace=row["stack_trace"],
                    guild_id=row["guild_id"],
                    channel_id=row["channel_id"],
                    user_id=row["user_id"],
                    command=row["command"],
                )
                for row in rows
            ]
        except Exception:
            return []


logger = BotLogger()
