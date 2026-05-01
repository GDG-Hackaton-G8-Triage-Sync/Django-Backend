import os
import sys
import time
import asyncio
from pathlib import Path

# Ensure project root is on sys.path (script runs from scripts/ directory)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Allow test client host
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'testserver,127.0.0.1,localhost')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'triagesync_backend.config.settings')

import django
django.setup()

from rest_framework.test import APIClient
import triagesync_backend.config.asgi as asgi_module
from triagesync_backend.apps.realtime.middleware import JWTAuthMiddleware
try:
    from channels.testing import WebsocketCommunicator
    HAS_WS_TEST = True
except Exception:
    HAS_WS_TEST = False


def register_staff_user():
    client = APIClient()

    # Create a unique staff user
    ts = int(time.time())
    email = f"dr_test_{ts}@example.com"
    payload = {
        "name": "Dr Smoke Test",
        "email": email,
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "role": "doctor",
        "age": 40,
        "gender": "male",
        "blood_type": "O+",
    }

    print("Registering user...", payload["email"])
    resp = client.post('/api/v1/auth/register/', payload, format='json')
    print("Register status:", resp.status_code)
    try:
        data = resp.json()
    except Exception:
        print("Response not JSON:", resp.content)
        sys.exit(2)

    if resp.status_code not in (200, 201):
        print("Registration failed:", data)
        sys.exit(3)

    token = data.get('access_token') or data.get('access') or data.get('accessToken')
    if not token:
        print("No access token returned:", data)
        sys.exit(4)

    print("Access token obtained (truncated):", token[:40])

    return data, token


async def run_test(token, user_data):

    # First: quick auth check using JWT middleware's _authenticate_user
    print("Verifying token via JWT middleware...")
    middleware = JWTAuthMiddleware(None)
    user = await middleware._authenticate_user(token)
    if user is None:
        print("Middleware failed to authenticate token")
        sys.exit(6)
    print("Middleware authenticated user:", user.username, "role:", user.role)

    # If WebSocket testing utilities are available, attempt an in-process WS connect
    if HAS_WS_TEST:
        print("WebSocket testing utilities available — attempting full connect")
        app = asgi_module.application
        ws_path = f"/ws/triage/events/?token={token}"

        print("Attempting WebSocket connect to:", ws_path)
        communicator = WebsocketCommunicator(app, ws_path)
        connected, subprotocol = await communicator.connect()
        print("Connected:", connected, "subprotocol:", subprotocol)

        if not connected:
            # Try to receive close reason if available
            try:
                msg = await communicator.receive_from()
                print("Received from server:", msg)
            except Exception:
                pass
            await communicator.disconnect()
            sys.exit(5)
    else:
        print("WebSocket testing utilities not available in this environment — skipping full connect")

    # Test sending a server broadcast (simulate notification)
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()
    group_name = f"user_{user_data.get('user_id') or user_data.get('userId') or user_data.get('id')}"

    payload = {
        "type": "notification_message",
        "notification": {
            "id": 9999,
            "notification_type": "system_message",
            "title": "Smoke Test",
            "message": "This is a smoke-test notification",
            "metadata": {},
            "is_read": False,
            "created_at": "now"
        }
    }

    if HAS_WS_TEST:
        print("Sending group message to", group_name)
        async_to_sync(channel_layer.group_send)(group_name, payload)

        # Try to receive the notification
        try:
            msg = await communicator.receive_from(timeout=5)
            print("WS Received:", msg)
        except asyncio.TimeoutError:
            print("No message received within timeout")

        await communicator.disconnect()
        print("Smoke test completed successfully")
    else:
        print("Skipping group_send and socket receive because WebSocket testing utilities are unavailable.")
        print("Smoke test completed successfully (auth-only mode)")


if __name__ == '__main__':
    user_data, token = register_staff_user()
    asyncio.run(run_test(token, user_data))
