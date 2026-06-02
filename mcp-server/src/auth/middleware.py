import ipaddress
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config import settings


# DEV_MODE bypass: localhost and Docker/private networks
_DEV_MODE_ALLOWED_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),      # IPv4 loopback
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private (Docker bridge default)
    ipaddress.ip_network("172.16.0.0/12"),    # Private (Docker bridge range)
    ipaddress.ip_network("192.168.0.0/16"),   # Private (Docker compose)
]


def _is_local_ip(client_ip: str) -> bool:
    """Check if client IP is local (localhost or Docker network)."""
    try:
        ip = ipaddress.ip_address(client_ip)
        return any(ip in network for network in _DEV_MODE_ALLOWED_RANGES)
    except ValueError:
        return False


class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Bearer token auth. DEV_MODE bypasses auth for local/Docker IPs only."""

    async def dispatch(self, request, call_next):
        # Always allow health check endpoint without auth
        if request.url.path == "/health":
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        if settings.dev_mode and _is_local_ip(client_ip):
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        
        provided_token = auth[7:]
        # Constant-time comparison prevents timing attacks
        if not secrets.compare_digest(provided_token, settings.auth_token):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        
        return await call_next(request)

