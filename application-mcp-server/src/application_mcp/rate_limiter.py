"""Rate limiting for Graph API requests using AsyncLimiter"""
from typing import Dict, Tuple
from aiolimiter import AsyncLimiter
from .config import config
from .logging_config import get_logger

logger = get_logger(__name__)

# Endpoint pattern to rate limiter mapping
_rate_limiters: Dict[str, AsyncLimiter] = {}


def _parse_rate_limit(rate_limit_str: str) -> Tuple[int, float]:
    """
    Parse rate limit configuration string.
    
    Args:
        rate_limit_str: Format "max_requests,time_period_seconds" e.g., "10000,600"
    
    Returns:
        Tuple of (max_requests, time_period_seconds)
    """
    try:
        parts = rate_limit_str.split(",")
        max_requests = int(parts[0].strip())
        time_period = float(parts[1].strip())
        return (max_requests, time_period)
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid rate limit configuration: {rate_limit_str}", exc_info=True)
        # Return conservative defaults
        return (100, 60)  # 100 requests per minute


def _get_endpoint_category(endpoint: str) -> str:
    """
    Determine the category of an endpoint for rate limiting.
    
    Args:
        endpoint: API endpoint path
    
    Returns:
        Category name (mail, calendar, teams_messages, etc.)
    """
    endpoint_lower = endpoint.lower()
    
    # Mail endpoints
    if '/messages' in endpoint_lower or '/mailfolder' in endpoint_lower:
        return 'mail'
    
    # Calendar endpoints
    if '/calendar' in endpoint_lower or '/events' in endpoint_lower:
        return 'calendar'
    
    # Teams channel messages (most restrictive)
    if '/channels/' in endpoint_lower and '/messages' in endpoint_lower:
        return 'teams_messages'
    
    # Search API
    if '/search' in endpoint_lower or '$search' in endpoint_lower:
        return 'search'
    
    # Users/Groups
    if endpoint_lower.startswith('/users') or endpoint_lower.startswith('/groups'):
        # Check if it's not a mail/calendar sub-resource
        if '/messages' not in endpoint_lower and '/calendar' not in endpoint_lower:
            return 'users'
    
    # OneDrive/Files
    if '/drive' in endpoint_lower or '/drives/' in endpoint_lower:
        return 'files'
    
    # Online Meetings
    if '/onlinemeetings' in endpoint_lower or '/meetings' in endpoint_lower:
        return 'meetings'
    
    # Default to global
    return 'global'


def get_rate_limiter(endpoint: str) -> AsyncLimiter:
    """
    Get or create a rate limiter for the given endpoint.
    
    Rate limiters are cached and reused based on endpoint category.
    
    Args:
        endpoint: API endpoint path
    
    Returns:
        AsyncLimiter instance for the endpoint category
    """
    category = _get_endpoint_category(endpoint)
    
    # Return cached limiter if exists
    if category in _rate_limiters:
        return _rate_limiters[category]
    
    # Create new rate limiter based on category
    rate_limit_config = {
        'global': config.RATE_LIMIT_GLOBAL,
        'mail': config.RATE_LIMIT_MAIL,
        'calendar': config.RATE_LIMIT_CALENDAR,
        'teams_messages': config.RATE_LIMIT_TEAMS_MESSAGES,
        'search': config.RATE_LIMIT_SEARCH,
        'users': config.RATE_LIMIT_USERS,
        'files': config.RATE_LIMIT_FILES,
        'meetings': config.RATE_LIMIT_MEETINGS,
    }
    
    rate_config_str = rate_limit_config.get(category, config.RATE_LIMIT_GLOBAL)
    max_requests, time_period = _parse_rate_limit(rate_config_str)
    
    limiter = AsyncLimiter(max_requests, time_period)
    _rate_limiters[category] = limiter
    
    logger.info(
        f"Rate limiter initialized for '{category}' category",
        extra={
            "category": category,
            "max_requests": max_requests,
            "time_period_seconds": time_period,
            "rate_per_second": round(max_requests / time_period, 2)
        }
    )
    
    return limiter


def get_all_limiters() -> Dict[str, AsyncLimiter]:
    """
    Get all initialized rate limiters.
    
    Returns:
        Dictionary of category -> AsyncLimiter
    """
    return _rate_limiters.copy()


def get_limiter_stats() -> Dict[str, Dict]:
    """
    Get statistics about rate limiters.
    
    Returns:
        Dictionary with stats for each limiter
    """
    stats = {}
    
    for category, limiter in _rate_limiters.items():
        stats[category] = {
            "max_rate": limiter.max_rate,
            "time_period": limiter.time_period,
            "current_level": limiter._level if hasattr(limiter, '_level') else None,
        }
    
    return stats
