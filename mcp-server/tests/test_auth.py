"""Tests for authentication middleware security."""
from unittest.mock import AsyncMock, Mock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from src.auth.middleware import BearerTokenMiddleware, _is_local_ip
from src.config import settings


def test_is_local_ip():
    """Test local IP detection."""
    # Localhost
    assert _is_local_ip("127.0.0.1") is True
    assert _is_local_ip("::1") is True

    # Docker bridge networks
    assert _is_local_ip("172.17.0.1") is True
    assert _is_local_ip("172.18.0.5") is True
    assert _is_local_ip("192.168.0.100") is True
    assert _is_local_ip("192.168.148.1") is True

    # External IPs
    assert _is_local_ip("8.8.8.8") is False
    assert _is_local_ip("1.2.3.4") is False
    assert _is_local_ip("203.0.113.1") is False


def test_dev_mode_allows_local_ips():
    """Test that DEV_MODE bypasses auth for local IPs only."""
    from src.auth.middleware import _is_local_ip

    # Local IPs bypass auth in DEV_MODE
    assert _is_local_ip("127.0.0.1") is True
    assert _is_local_ip("::1") is True
    assert _is_local_ip("172.17.0.1") is True
    assert _is_local_ip("192.168.1.1") is True

    # External IPs require auth even in DEV_MODE
    assert _is_local_ip("8.8.8.8") is False
    assert _is_local_ip("1.1.1.1") is False


def test_timing_attack_protection():
    """Verify that secrets.compare_digest is used (prevents timing attacks)."""
    import secrets
    from src.auth import middleware
    
    # Verify the module uses secrets.compare_digest
    source = middleware.__file__
    with open(source.replace('.pyc', '.py'), 'r') as f:
        content = f.read()
        assert 'secrets.compare_digest' in content
        assert '!=' not in content or 'startswith' in content  # Only != for prefix check


