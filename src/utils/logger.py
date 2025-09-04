import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Optional
import uuid

from src.models import (
    ErrorDocument,
    LogArea,
    LogLevel
)


class BotLogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.console_enabled = True
            self.db_enabled = True
            self.min_level = LogLevel.INFO
    
    def _get_color(self, level: LogLevel) -> str:
        """Get ANSI color code for log level"""
        colors = {
            LogLevel.DEBUG: "\033[90m",     # Gray
            LogLevel.INFO: "\033[92m",      # Green
            LogLevel.WARNING: "\033[93m",   # Yellow
            LogLevel.ERROR: "\033[91m",     # Red
            LogLevel.CRITICAL: "\033[95m",   # Magenta
            LogLevel.NONE: "\033[37m"       # White/default
        }
        return colors.get(level, "")
    
    def _reset_color(self) -> str:
        """Reset ANSI color"""
        return "\033[0m"
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if this level should be logged based on min_level"""
        # NONE level always gets logged
        if level == LogLevel.NONE:
            return True
        level_order = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        return level_order.index(level) >= level_order.index(self.min_level)
    
    def _format_message(self, level: LogLevel, area: LogArea, message: str) -> str:
        """Format log message for console output"""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        color = self._get_color(level)
        reset = self._reset_color()
        
        # Build format based on NONE values
        if level == LogLevel.NONE and area == LogArea.NONE:
            # Neither level nor area
            return f"{color}[{timestamp}] {message}{reset}"
        elif level == LogLevel.NONE:
            # No level, but has area
            return f"{color}[{timestamp}] [{area.value:10}] {message}{reset}"
        elif area == LogArea.NONE:
            # No area, but has level
            return f"{color}[{timestamp}] [{level.value:8}] {message}{reset}"
        else:
            # Both level and area
            return f"{color}[{timestamp}] [{level.value:8}] [{area.value:10}] {message}{reset}"
    
    async def _save_error_to_db(self, error_record: ErrorDocument) -> None:
        """Save error record to database"""
        if not self.db_enabled:
            return
            
        try:
            from src.services.database_connection_manager import db_manager
            errors_collection = db_manager.errors
            error_doc = error_record.to_dict()
            await errors_collection.insert_one(error_doc)
        except Exception as e:
            # Fallback to console if DB save fails
            print(f"Failed to save error to database: {e}")
    
    def log(self, level: LogLevel, area: LogArea, message: str, **kwargs) -> Optional[str]:
        """
        Log a message with specified level and area.
        Returns error_id if level is ERROR or CRITICAL.
        """
        if not self._should_log(level):
            return None
        
        # Console output
        if self.console_enabled:
            formatted = self._format_message(level, area, message)
            print(formatted)
        
        # Return error_id for errors
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
        **additional_data
    ) -> str:
        """
        Log an error and save it to the database.
        Returns the error ID for reference.
        """
        error_id = str(uuid.uuid4())[:8]  # Short ID for easy reference
        
        # Get traceback if exception provided
        tb_str = ""
        if exception:
            tb_str = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        elif sys.exc_info()[0]:
            tb_str = traceback.format_exc()
        
        # Create error document using the model
        error_record = ErrorDocument(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.ERROR.value,
            area=area.value if hasattr(area, 'value') else str(area),
            message=message,
            stack_trace=tb_str,
            guild_id=server_id,
            channel_id=channel_id,
            user_id=user_id,
            command=command
        )
        
        # Console output
        if self.console_enabled:
            formatted = self._format_message(LogLevel.ERROR, area, f"{message} [Error ID: {error_id}]")
            print(formatted)
            if tb_str and self.min_level == LogLevel.DEBUG:
                print(tb_str)
        
        # Save to database
        await self._save_error_to_db(error_record)
        
        return error_id
    
    def _generate_error_id(self) -> str:
        """Generate a short unique error ID"""
        return str(uuid.uuid4())[:8]
    
    # Convenience methods
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
        """Print a clean message without level or area fields"""
        self.log(LogLevel.NONE, LogArea.NONE, message, **kwargs)
    
    def spacer(self, char: str = "=", length: Optional[int] = None, color: Optional[LogLevel] = None) -> None:
        """Print a colored spacer line that fits the logger theme"""
        # Get terminal width, fallback to 100 if unable to determine
        if length is None:
            try:
                # Get terminal width on Windows and Unix systems
                terminal_width = os.get_terminal_size().columns
            except (OSError, AttributeError):
                # Fallback if terminal size can't be determined
                terminal_width = 100
        else:
            terminal_width = length
            
        if color:
            color_code = self._get_color(color)
        else:
            # Default to a cyan/blue color for better visibility
            color_code = "\033[36m"  # Cyan
        reset = self._reset_color()
        print(f"{color_code}{char * terminal_width}{reset}")
    
    async def get_error(self, error_id: str) -> Optional[ErrorDocument]:
        """Retrieve an error from the database by ID"""
        try:
            from src.services.database_connection_manager import db_manager
            errors_collection = db_manager.errors
            error_doc = await errors_collection.find_one({"_id": error_id})
            if error_doc:
                return ErrorDocument.from_dict(error_doc)
            return None
        except Exception:
            return None
    
    async def delete_error(self, error_id: str) -> bool:
        """Delete an error from the database by ID"""
        try:
            from src.services.database_connection_manager import db_manager
            errors_collection = db_manager.errors
            result = await errors_collection.delete_one({"_id": error_id})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def get_recent_errors(self, limit: int = 10) -> list[ErrorDocument]:
        """Get recent errors from the database"""
        try:
            from src.services.database_connection_manager import db_manager
            errors_collection = db_manager.errors
            cursor = errors_collection.find().sort("timestamp", -1).limit(limit)
            error_docs = await cursor.to_list(length=limit)
            return [ErrorDocument.from_dict(doc) for doc in error_docs]
        except Exception:
            return []


# Global logger instance
logger = BotLogger()