import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

TRIAGE_GROUP = "triage_events"
logger = logging.getLogger(__name__)


class TriageEventsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time triage events.

    Clients connect to ws/triage/events/ and receive broadcast events:
      - patient_created
      - priority_update
      - critical_alert
      - status_changed

    Note: JWT authentication and role-based authorization are enforced by
    JWTAuthMiddleware before connections reach this consumer. All connections
    are guaranteed to have an authenticated user with authorized role.
    """

    group_name = TRIAGE_GROUP

    async def connect(self):
        # Access authenticated user from scope (provided by JWTAuthMiddleware)
        user = self.scope.get('user')
        
        if user and user.is_authenticated:
            logger.info(
                f"WebSocket connection established for user {user.username} "
                f"(role: {user.role}, channel: {self.channel_name})"
            )
        else:
            # This should not happen if middleware is working correctly
            logger.warning(f"WebSocket connection without authenticated user (channel: {self.channel_name})")
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Clients don't send data in this system — this is a server-push only channel.
        We silently ignore any incoming messages.
        """
        pass

    # --- Group message handlers ---
    # Each method name maps to the "type" field in group_send calls.
    # "triage_event" maps to triage_event() via Django Channels convention.

    async def triage_event(self, event):
        """Forwards any broadcast payload to the connected WebSocket client."""
        await self.send(text_data=json.dumps(event["payload"]))
