"""
Python → Java WebSocket broker bridge.

Sends fire-and-forget HTTP notifications to the Java backendPerm
so it can relay events to connected Angular clients via STOMP WebSocket.

Java may not be running (dev mode) — all errors are silently swallowed.
"""

import os
import threading

import httpx

_JAVA_URL = os.getenv("JAVA_URL", "http://localhost:8001")
_BROKER_API_KEY = os.getenv("BROKER_API_KEY", "koreon-broker-dev-key")


def notify_broker(type_: str, payload: dict, tenant_id: int = 1) -> None:
    """Send event to Java broker asynchronously. Never raises."""
    def _send():
        try:
            body = {"type": type_, "tenant_id": tenant_id, **payload}
            httpx.post(
                f"{_JAVA_URL}/broker/event",
                json=body,
                headers={"X-Broker-Key": _BROKER_API_KEY},
                timeout=3.0,
            )
        except Exception:
            pass  # Java service may not be running in dev

    threading.Thread(target=_send, daemon=True).start()
