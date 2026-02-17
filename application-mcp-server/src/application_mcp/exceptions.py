"""Custom exceptions for application-mcp-server"""
from typing import Optional, Dict, Any


class MCPServerError(Exception):
    """Base exception for all MCP server errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Authentication Errors
class AuthenticationError(MCPServerError):
    """Error acquiring or validating authentication token"""
    pass


class TokenAcquisitionError(AuthenticationError):
    """Failed to acquire access token from Azure AD"""
    pass


class TokenExpiredError(AuthenticationError):
    """Access token has expired"""
    pass


# API Errors
class GraphAPIError(MCPServerError):
    """Base exception for Microsoft Graph API errors"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        response_body: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "status_code": status_code,
            "endpoint": endpoint,
            "response_body": response_body[:500] if response_body else None
        })
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.endpoint = endpoint
        self.response_body = response_body


class RateLimitError(GraphAPIError):
    """API rate limit exceeded (429 error)"""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after
        self.details["retry_after_seconds"] = retry_after


class ResourceNotFoundError(GraphAPIError):
    """Requested resource not found (404 error)"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, **kwargs):
        super().__init__(message, status_code=404, **kwargs)
        self.resource_type = resource_type
        if resource_type:
            self.details["resource_type"] = resource_type


class PermissionDeniedError(GraphAPIError):
    """Permission denied to access resource (403 error)"""
    
    def __init__(self, message: str, required_permission: Optional[str] = None, **kwargs):
        super().__init__(message, status_code=403, **kwargs)
        self.required_permission = required_permission
        if required_permission:
            self.details["required_permission"] = required_permission


class BadRequestError(GraphAPIError):
    """Invalid request parameters (400 error)"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, status_code=400, **kwargs)


class ServerError(GraphAPIError):
    """Microsoft Graph API server error (5xx)"""
    pass


# Network Errors
class NetworkError(MCPServerError):
    """Network-related errors"""
    pass


class ConnectionError(NetworkError):
    """Failed to connect to API"""
    pass


class TimeoutError(NetworkError):
    """Request timed out"""
    pass


class DNSError(NetworkError):
    """DNS resolution failed"""
    pass


# Configuration Errors
class ConfigurationError(MCPServerError):
    """Configuration validation or loading error"""
    pass


class MissingConfigurationError(ConfigurationError):
    """Required configuration is missing"""
    
    def __init__(self, config_key: str, **kwargs):
        message = f"Required configuration '{config_key}' is missing"
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.details["config_key"] = config_key


# Validation Errors
class ValidationError(MCPServerError):
    """Input validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field = field
        if field:
            self.details["field"] = field


# Quota/Resource Errors
class QuotaExceededError(MCPServerError):
    """API quota or resource limit exceeded"""
    pass


class ConcurrencyLimitError(MCPServerError):
    """Too many concurrent requests"""
    
    def __init__(self, message: str, limit: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.limit = limit
        if limit:
            self.details["limit"] = limit


# Retry Errors
class MaxRetriesExceededError(MCPServerError):
    """Maximum retry attempts exceeded"""
    
    def __init__(
        self,
        message: str,
        attempts: int,
        last_error: Optional[Exception] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.attempts = attempts
        self.last_error = last_error
        self.details["attempts"] = attempts
        if last_error:
            self.details["last_error"] = str(last_error)


# Helper functions
def classify_http_error(
    status_code: int,
    endpoint: str,
    response_body: Optional[str] = None
) -> GraphAPIError:
    """
    Classify HTTP error by status code and return appropriate exception.
    
    Args:
        status_code: HTTP status code
        endpoint: API endpoint that failed
        response_body: Response body text
    
    Returns:
        Appropriate GraphAPIError subclass
    """
    error_kwargs = {
        "endpoint": endpoint,
        "response_body": response_body
    }
    
    if status_code == 400:
        return BadRequestError(
            f"Bad request to {endpoint}",
            **error_kwargs
        )
    elif status_code == 403:
        return PermissionDeniedError(
            f"Permission denied accessing {endpoint}",
            **error_kwargs
        )
    elif status_code == 404:
        # Try to determine resource type from endpoint
        resource_type = None
        if '/users/' in endpoint:
            resource_type = 'user'
        elif '/messages' in endpoint:
            resource_type = 'message'
        elif '/calendar' in endpoint or '/events' in endpoint:
            resource_type = 'calendar_event'
        
        return ResourceNotFoundError(
            f"Resource not found: {endpoint}",
            resource_type=resource_type,
            **error_kwargs
        )
    elif status_code == 429:
        return RateLimitError(
            f"Rate limit exceeded for {endpoint}",
            **error_kwargs
        )
    elif status_code >= 500:
        return ServerError(
            f"Server error ({status_code}) from {endpoint}",
            **error_kwargs
        )
    else:
        return GraphAPIError(
            f"HTTP error {status_code} from {endpoint}",
            status_code=status_code,
            **error_kwargs
        )


def is_retriable_error(error: Exception) -> bool:
    """
    Determine if an error is retriable.
    
    Args:
        error: Exception to check
    
    Returns:
        True if the error should be retried
    """
    # Server errors are retriable
    if isinstance(error, ServerError):
        return True
    
    # Rate limits are retriable (with backoff)
    if isinstance(error, RateLimitError):
        return True
    
    # Network errors are retriable
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    
    # Other errors are not retriable
    return False
