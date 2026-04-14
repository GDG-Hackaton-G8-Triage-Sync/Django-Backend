import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TriageEventsConsumer(AsyncWebsocketConsumer):
    group_name = "triage_events"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            payload = json.loads(text_data)
            await self.send(text_data=json.dumps({"echo": payload}))

    async def triage_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
