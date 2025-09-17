"""
Retry service with exponential backoff and circuit breaker patterns.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import random

from exceptions import KiroException

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_multiplier: float = 1.0
    retryable_exceptions: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [Exception]


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception
    name: str = "default"


class CircuitBreaker:
    """Circuit breaker implementation."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker {self.config.name} moved to HALF_OPEN state")
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        return False
    
    def record_success(self):
        """Record successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:  # Require 3 successes to close
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker {self.config.name} moved to CLOSED state")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self, exception: Exception):
        """Record failed execution."""
        if isinstance(exception, self.config.expected_exception):
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.config.name} moved to OPEN state after {self.failure_count} failures")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.config.name} moved back to OPEN state")


class RetryService:
    """Service for handling retries with exponential backoff and circuit breakers."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig(name=name)
            self.circuit_breakers[name] = CircuitBreaker(config)
        return self.circuit_breakers[name]
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        delay = min(
            config.base_delay * (config.exponential_base ** (attempt - 1)) * config.backoff_multiplier,
            config.max_delay
        )
        
        if config.jitter:
            # Add jitter to prevent thundering herd
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, exception: Exception, attempt: int, config: RetryConfig) -> bool:
        """Determine if operation should be retried."""
        if attempt >= config.max_attempts:
            return False
        
        return any(isinstance(exception, exc_type) for exc_type in config.retryable_exceptions)
    
    async def execute_with_retry(
        self,
        func: Callable,
        config: RetryConfig,
        circuit_breaker_name: str = None,
        circuit_breaker_config: CircuitBreakerConfig = None,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic and optional circuit breaker."""
        circuit_breaker = None
        if circuit_breaker_name:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_name, circuit_breaker_config)
        
        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.can_execute():
                raise KiroException(
                    message=f"Circuit breaker {circuit_breaker_name} is OPEN",
                    error_code="CIRCUIT_BREAKER_OPEN",
                    details={
                        "circuit_breaker": circuit_breaker_name,
                        "state": circuit_breaker.state.value,
                        "failure_count": circuit_breaker.failure_count
                    }
                )
            
            try:
                logger.debug(f"Executing function attempt {attempt}/{config.max_attempts}")
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success()
                
                if attempt > 1:
                    logger.info(f"Function succeeded on attempt {attempt}")
                
                return result
                
            except Exception as exc:
                last_exception = exc
                
                # Record failure in circuit breaker
                if circuit_breaker:
                    circuit_breaker.record_failure(exc)
                
                # Check if we should retry
                if not self.should_retry(exc, attempt, config):
                    logger.error(f"Function failed on attempt {attempt}, not retrying: {str(exc)}")
                    raise exc
                
                # Calculate delay for next attempt
                if attempt < config.max_attempts:
                    delay = self.calculate_delay(attempt, config)
                    logger.warning(
                        f"Function failed on attempt {attempt}, retrying in {delay:.2f}s: {str(exc)}",
                        extra={
                            "attempt": attempt,
                            "max_attempts": config.max_attempts,
                            "delay": delay,
                            "exception": str(exc)
                        }
                    )
                    await asyncio.sleep(delay)
        
        # All attempts failed
        logger.error(f"Function failed after {config.max_attempts} attempts")
        raise last_exception


# Global retry service instance
retry_service = RetryService()


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: List[Type[Exception]] = None,
    circuit_breaker_name: str = None,
    circuit_breaker_config: CircuitBreakerConfig = None
):
    """Decorator for adding retry logic to functions."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions or [Exception]
            )
            
            return await retry_service.execute_with_retry(
                func, config, circuit_breaker_name, circuit_breaker_config, *args, **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions or [Exception]
            )
            
            return asyncio.run(retry_service.execute_with_retry(
                func, config, circuit_breaker_name, circuit_breaker_config, *args, **kwargs
            ))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception
):
    """Decorator for adding circuit breaker to functions."""
    
    def decorator(func: Callable) -> Callable:
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            circuit = retry_service.get_circuit_breaker(name, config)
            
            if not circuit.can_execute():
                raise KiroException(
                    message=f"Circuit breaker {name} is OPEN",
                    error_code="CIRCUIT_BREAKER_OPEN",
                    details={
                        "circuit_breaker": name,
                        "state": circuit.state.value
                    }
                )
            
            try:
                result = await func(*args, **kwargs)
                circuit.record_success()
                return result
            except Exception as exc:
                circuit.record_failure(exc)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            circuit = retry_service.get_circuit_breaker(name, config)
            
            if not circuit.can_execute():
                raise KiroException(
                    message=f"Circuit breaker {name} is OPEN",
                    error_code="CIRCUIT_BREAKER_OPEN",
                    details={
                        "circuit_breaker": name,
                        "state": circuit.state.value
                    }
                )
            
            try:
                result = func(*args, **kwargs)
                circuit.record_success()
                return result
            except Exception as exc:
                circuit.record_failure(exc)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator