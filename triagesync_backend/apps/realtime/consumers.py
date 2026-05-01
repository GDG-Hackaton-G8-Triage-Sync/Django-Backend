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
        self.user = self.scope.get('user')
        
        if self.user and self.user.is_authenticated:
            logger.info(
                f"WebSocket connection established for user {self.user.username} "
                f"(role: {self.user.role}, channel: {self.channel_name})"
            )
            
            # 1. Join global triage events group (only for staff roles)
            if self.user.role in ['admin', 'doctor', 'nurse', 'staff']:
                await self.channel_layer.group_add(TRIAGE_GROUP, self.channel_name)
            
            # 2. Join private user notification group (for all users)
            self.user_group = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            
            await self.accept()
        else:
            # This should not happen if middleware is working correctly
            logger.warning(f"WebSocket connection attempt without authenticated user (channel: {self.channel_name})")
            await self.close()

    async def disconnect(self, close_code):
        # Leave global triage group if staff
        if hasattr(self, 'user') and self.user.role in ['admin', 'doctor', 'nurse', 'staff']:
            await self.channel_layer.group_discard(TRIAGE_GROUP, self.channel_name)
        
        # Leave private user group
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Clients don't send data in this system — this is a server-push only channel.
        We silently ignore any incoming messages.
        """
        pass

    # --- Group message handlers ---

    async def triage_event(self, event):
        """Forwards global broadcast payloads to staff clients."""
        await self.send(text_data=json.dumps(event["payload"]))

    async def notification_message(self, event):
        """Forwards private notification payloads to the specific user."""
        await self.send(text_data=json.dumps({
            "type": "notification",
            "data": event["notification"]
        }))
