import ipaddress
import re
import socket
from pathlib import Path
from typing import Iterable, Optional, Tuple
from urllib.parse import urlparse

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]")
LOCAL_HOSTNAMES = {"localhost", "localhost.localdomain"}


def sanitize_filename(filename: Optional[str], default: str = "upload") -> str:
    candidate = Path(filename or default).name.strip().replace("\x00", "")
    if not candidate:
        candidate = default
    return SAFE_FILENAME_RE.sub("_", candidate)


def validate_public_http_url(
    url: str, allowed_hosts: Optional[Iterable[str]] = None
) -> Tuple[bool, str]:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return False, "Only http and https URLs are allowed"
    if not parsed.hostname:
        return False, "URL must include a hostname"
    if parsed.username or parsed.password:
        return False, "Credentials in URLs are not allowed"

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in LOCAL_HOSTNAMES or hostname.endswith(".local"):
        return False, "Local hostnames are not allowed"

    normalized_hosts = [host.strip().lower() for host in (allowed_hosts or []) if host.strip()]
    if normalized_hosts and not _is_allowed_hostname(hostname, normalized_hosts):
        return False, "Hostname is not in the allowed list"

    try:
        resolved = {
            sockaddr[0]
            for _, _, _, _, sockaddr in socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        }
    except socket.gaierror:
        return False, "Hostname could not be resolved"

    if not resolved:
        return False, "Hostname could not be resolved"

    for address in resolved:
        ip = ipaddress.ip_address(address)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False, "Private or reserved network addresses are not allowed"

    return True, ""


def _is_allowed_hostname(hostname: str, allowed_hosts: Iterable[str]) -> bool:
    for allowed in allowed_hosts:
        if hostname == allowed or hostname.endswith(f".{allowed}"):
            return True
    return False
