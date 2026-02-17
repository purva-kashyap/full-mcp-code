"""Metrics and observability for production monitoring"""
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from threading import Lock
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    rate_limit_count: int = 0
    server_error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: Optional[float] = None
    max_duration_ms: Optional[float] = None


class MetricsCollector:
    """
    Thread-safe metrics collector for monitoring application performance.
    
    Tracks:
    - Request counts (total, success, errors)
    - Duration statistics (min, max, avg)
    - Error types (rate limits, server errors)
    - Per-endpoint metrics
    """
    
    def __init__(self):
        self._lock = Lock()
        self._global_metrics = RequestMetrics()
        self._endpoint_metrics: Dict[str, RequestMetrics] = {}
        self._start_time = time.time()
    
    def record_request(
        self,
        endpoint: str,
        duration_ms: float,
        status_code: int,
        error: Optional[str] = None
    ):
        """
        Record a request with its outcome.
        
        Args:
            endpoint: API endpoint called
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code
            error: Optional error type
        """
        with self._lock:
            # Update global metrics
            self._update_metrics(self._global_metrics, duration_ms, status_code, error)
            
            # Update per-endpoint metrics
            if endpoint not in self._endpoint_metrics:
                self._endpoint_metrics[endpoint] = RequestMetrics()
            self._update_metrics(self._endpoint_metrics[endpoint], duration_ms, status_code, error)
    
    def _update_metrics(
        self,
        metrics: RequestMetrics,
        duration_ms: float,
        status_code: int,
        error: Optional[str]
    ):
        """Update metrics object with new data"""
        metrics.total_requests += 1
        metrics.total_duration_ms += duration_ms
        
        if metrics.min_duration_ms is None or duration_ms < metrics.min_duration_ms:
            metrics.min_duration_ms = duration_ms
        
        if metrics.max_duration_ms is None or duration_ms > metrics.max_duration_ms:
            metrics.max_duration_ms = duration_ms
        
        if 200 <= status_code < 300:
            metrics.success_count += 1
        elif status_code >= 400:
            metrics.error_count += 1
            
            if status_code == 429:
                metrics.rate_limit_count += 1
            elif status_code >= 500:
                metrics.server_error_count += 1
    
    def get_global_metrics(self) -> Dict:
        """Get global metrics summary"""
        with self._lock:
            uptime_seconds = time.time() - self._start_time
            
            return {
                "uptime_seconds": round(uptime_seconds, 2),
                "total_requests": self._global_metrics.total_requests,
                "success_count": self._global_metrics.success_count,
                "error_count": self._global_metrics.error_count,
                "rate_limit_count": self._global_metrics.rate_limit_count,
                "server_error_count": self._global_metrics.server_error_count,
                "success_rate": self._calculate_success_rate(self._global_metrics),
                "avg_duration_ms": self._calculate_avg_duration(self._global_metrics),
                "min_duration_ms": self._global_metrics.min_duration_ms,
                "max_duration_ms": self._global_metrics.max_duration_ms,
            }
    
    def get_endpoint_metrics(self) -> Dict[str, Dict]:
        """Get per-endpoint metrics"""
        with self._lock:
            return {
                endpoint: {
                    "total_requests": metrics.total_requests,
                    "success_count": metrics.success_count,
                    "error_count": metrics.error_count,
                    "rate_limit_count": metrics.rate_limit_count,
                    "server_error_count": metrics.server_error_count,
                    "success_rate": self._calculate_success_rate(metrics),
                    "avg_duration_ms": self._calculate_avg_duration(metrics),
                    "min_duration_ms": metrics.min_duration_ms,
                    "max_duration_ms": metrics.max_duration_ms,
                }
                for endpoint, metrics in self._endpoint_metrics.items()
            }
    
    def _calculate_success_rate(self, metrics: RequestMetrics) -> float:
        """Calculate success rate percentage"""
        if metrics.total_requests == 0:
            return 0.0
        return round((metrics.success_count / metrics.total_requests) * 100, 2)
    
    def _calculate_avg_duration(self, metrics: RequestMetrics) -> float:
        """Calculate average duration"""
        if metrics.total_requests == 0:
            return 0.0
        return round(metrics.total_duration_ms / metrics.total_requests, 2)
    
    def log_metrics_summary(self):
        """Log metrics summary for monitoring"""
        global_metrics = self.get_global_metrics()
        
        logger.info(
            "Metrics summary",
            extra={
                "uptime_seconds": global_metrics["uptime_seconds"],
                "total_requests": global_metrics["total_requests"],
                "success_rate": global_metrics["success_rate"],
                "avg_duration_ms": global_metrics["avg_duration_ms"],
                "rate_limit_count": global_metrics["rate_limit_count"],
            }
        )


# Global metrics collector
metrics_collector = MetricsCollector()
