"""
Token cache manager for persistent authentication
Stores tokens securely and handles refresh automatically
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import threading


class TokenCache:
    """Manage OAuth tokens with automatic refresh"""
    
    def __init__(self, cache_file: str = "~/.mcp_token_cache.json"):
        self.cache_file = Path(cache_file).expanduser()
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: Dict[str, dict] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load token cache from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self._cache = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load token cache: {e}")
                self._cache = {}
    
    def _save_cache(self):
        """Save token cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.cache_file, 0o600)
        except Exception as e:
            print(f"Warning: Could not save token cache: {e}")
    
    def get_token(self, user_id: str) -> Optional[dict]:
        """
        Get cached token for user.
        
        Args:
            user_id: Unique user identifier (e.g., email or user principal name)
        
        Returns:
            Token data if valid, None if expired or not found
        """
        with self._lock:
            if user_id not in self._cache:
                return None
            
            token_data = self._cache[user_id]
            expires_at = datetime.fromisoformat(token_data.get('expires_at', '2000-01-01'))
            
            # Check if token is still valid (with 5 minute buffer)
            if datetime.now() + timedelta(minutes=5) < expires_at:
                return token_data
            
            # Token expired, try to refresh if we have refresh token
            if token_data.get('refresh_token'):
                refreshed = self._refresh_token(user_id, token_data['refresh_token'])
                if refreshed:
                    return refreshed
            
            # Could not refresh, remove from cache
            del self._cache[user_id]
            self._save_cache()
            return None
    
    def save_token(self, user_id: str, access_token: str, refresh_token: Optional[str] = None, 
                   expires_in: int = 3600):
        """
        Save token to cache.
        
        Args:
            user_id: Unique user identifier
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional but recommended)
            expires_in: Token lifetime in seconds
        """
        with self._lock:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self._cache[user_id] = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': expires_at.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self._save_cache()
    
    def _refresh_token(self, user_id: str, refresh_token: str) -> Optional[dict]:
        """
        Refresh access token using refresh token.
        
        Args:
            user_id: User identifier
            refresh_token: OAuth refresh token
        
        Returns:
            Updated token data or None if refresh failed
        """
        try:
            from msal import ConfidentialClientApplication
            
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            tenant = os.getenv("AZURE_TENANT_ID", "consumers")
            
            app = ConfidentialClientApplication(
                client_id,
                authority=f"https://login.microsoftonline.com/{tenant}",
                client_credential=client_secret,
            )
            
            result = app.acquire_token_by_refresh_token(
                refresh_token,
                scopes=["User.Read", "Mail.Read"]
            )
            
            if "access_token" in result:
                # Save refreshed token
                self.save_token(
                    user_id,
                    result["access_token"],
                    result.get("refresh_token", refresh_token),  # Use new or keep old
                    result.get("expires_in", 3600)
                )
                return self._cache[user_id]
            
        except Exception as e:
            print(f"Token refresh failed: {e}")
        
        return None
    
    def remove_token(self, user_id: str):
        """Remove token from cache (logout)"""
        with self._lock:
            if user_id in self._cache:
                del self._cache[user_id]
                self._save_cache()
    
    def clear_all(self):
        """Clear all cached tokens"""
        with self._lock:
            self._cache = {}
            self._save_cache()
    
    def list_users(self) -> list:
        """List all cached user IDs"""
        with self._lock:
            return list(self._cache.keys())


# Global token cache instance
_token_cache = TokenCache()


def get_token_cache() -> TokenCache:
    """Get the global token cache instance"""
    return _token_cache
