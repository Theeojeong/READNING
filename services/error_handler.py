"""
Error handling utilities following functional programming principles.

Provides safe error handling without relying on exceptions for control flow.
"""

import traceback
from typing import Callable, Any, Optional, TypeVar
from functools import wraps
from utils.logger import log
from services.types import Result


T = TypeVar('T')


class ErrorCode:
    """Error codes for different failure scenarios."""

    # Text processing errors
    TEXT_SPLIT_FAILED = "TEXT_SPLIT_FAILED"
    TEXT_TOO_SHORT = "TEXT_TOO_SHORT"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"

    # Emotion analysis errors
    EMOTION_ANALYSIS_FAILED = "EMOTION_ANALYSIS_FAILED"
    EMOTION_API_TIMEOUT = "EMOTION_API_TIMEOUT"
    INVALID_EMOTION_RESPONSE = "INVALID_EMOTION_RESPONSE"

    # Chunk processing errors
    CHUNK_TOO_SMALL = "CHUNK_TOO_SMALL"
    CHUNK_TOO_LARGE = "CHUNK_TOO_LARGE"
    INVALID_CHUNK_DATA = "INVALID_CHUNK_DATA"

    # Music generation errors
    MUSIC_GENERATION_FAILED = "MUSIC_GENERATION_FAILED"
    MODEL_NOT_LOADED = "MODEL_NOT_LOADED"

    # Database errors
    DATABASE_CONNECTION_FAILED = "DATABASE_CONNECTION_FAILED"
    DATABASE_WRITE_FAILED = "DATABASE_WRITE_FAILED"

    # Workflow errors
    WORKFLOW_INITIALIZATION_FAILED = "WORKFLOW_INITIALIZATION_FAILED"
    WORKFLOW_EXECUTION_FAILED = "WORKFLOW_EXECUTION_FAILED"


def safe_execute(
    func: Callable[..., T],
    *args,
    error_message: str = "Operation failed",
    error_code: str = ErrorCode.WORKFLOW_EXECUTION_FAILED,
    **kwargs
) -> Result:
    """
    Safely execute a function and return a Result.

    This replaces try-except patterns with functional error handling.

    Args:
        func: The function to execute
        *args: Positional arguments for the function
        error_message: Custom error message if function fails
        error_code: Error code for categorizing the failure
        **kwargs: Keyword arguments for the function

    Returns:
        Result object containing either success data or error information

    Example:
        >>> result = safe_execute(risky_operation, param1, param2)
        >>> if result.is_ok():
        ...     data = result.unwrap()
        ... else:
        ...     log(f"Error: {result.error}")
    """
    try:
        data = func(*args, **kwargs)
        return Result.ok(data)
    except Exception as e:
        error_detail = f"{error_message}: {str(e)}"
        log(f"❌ {error_detail}")
        log(f"   Stack trace: {traceback.format_exc()}")
        return Result.fail(error=error_detail, error_code=error_code)


async def safe_execute_async(
    func: Callable[..., T],
    *args,
    error_message: str = "Async operation failed",
    error_code: str = ErrorCode.WORKFLOW_EXECUTION_FAILED,
    **kwargs
) -> Result:
    """
    Safely execute an async function and return a Result.

    Async version of safe_execute.

    Args:
        func: The async function to execute
        *args: Positional arguments for the function
        error_message: Custom error message if function fails
        error_code: Error code for categorizing the failure
        **kwargs: Keyword arguments for the function

    Returns:
        Result object containing either success data or error information
    """
    try:
        data = await func(*args, **kwargs)
        return Result.ok(data)
    except Exception as e:
        error_detail = f"{error_message}: {str(e)}"
        log(f"❌ {error_detail}")
        log(f"   Stack trace: {traceback.format_exc()}")
        return Result.fail(error=error_detail, error_code=error_code)


def retry_on_failure(max_attempts: int = 3, delay_seconds: float = 1.0):
    """
    Decorator for retrying operations that might fail transiently.

    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Delay between attempts in seconds

    Example:
        >>> @retry_on_failure(max_attempts=3, delay_seconds=2.0)
        ... def unstable_api_call():
        ...     return call_external_api()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    log(f"🔄 Attempt {attempt}/{max_attempts}: {func.__name__}")
                    result = func(*args, **kwargs)
                    log(f"✅ Success on attempt {attempt}")
                    return result
                except Exception as e:
                    last_error = e
                    log(f"⚠️ Attempt {attempt} failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay_seconds)

            log(f"❌ All {max_attempts} attempts failed for {func.__name__}")
            raise last_error

        return wrapper
    return decorator


def validate_result(
    condition: bool,
    error_message: str,
    error_code: str = ErrorCode.WORKFLOW_EXECUTION_FAILED
) -> Optional[Result]:
    """
    Validate a condition and return an error Result if it fails.

    Returns None if validation passes, allowing for early returns.

    Args:
        condition: The condition to check
        error_message: Error message if condition is False
        error_code: Error code for the failure

    Returns:
        None if validation passes, Result.fail() otherwise

    Example:
        >>> if error := validate_result(len(text) > 0, "Text cannot be empty"):
        ...     return error
        >>> # Continue with processing
    """
    if not condition:
        return Result.fail(error=error_message, error_code=error_code)
    return None


class SafeContextManager:
    """
    Context manager that converts exceptions to Results.

    Example:
        >>> with SafeContextManager() as ctx:
        ...     risky_operation()
        >>> if ctx.result.is_err():
        ...     print(f"Error occurred: {ctx.result.error}")
    """

    def __init__(self, error_message: str = "Operation failed"):
        self.error_message = error_message
        self.result: Optional[Result] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            error_detail = f"{self.error_message}: {exc_val}"
            log(f"❌ {error_detail}")
            self.result = Result.fail(error=error_detail)
            return True  # Suppress the exception
        self.result = Result.ok()
        return False
