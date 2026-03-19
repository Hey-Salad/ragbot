import socket

from security_utils import sanitize_filename, validate_public_http_url


def test_sanitize_filename_strips_path_characters():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("hello world?.pdf") == "hello_world_.pdf"


def test_validate_public_http_url_rejects_localhost():
    allowed, reason = validate_public_http_url("http://localhost:8000/test")
    assert allowed is False
    assert "Local hostnames" in reason


def test_validate_public_http_url_accepts_public_host(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        ],
    )

    allowed, reason = validate_public_http_url("https://example.com/resource")
    assert allowed is True
    assert reason == ""


def test_validate_public_http_url_enforces_allowlist(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        ],
    )

    allowed, reason = validate_public_http_url(
        "https://api.twilio.com/resource",
        allowed_hosts=["mms.twiliocdn.com"],
    )
    assert allowed is False
    assert "allowed list" in reason
