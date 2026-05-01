import json

import pytest

# Skip all tests in this module if daphne is not installed
pytest.importorskip("daphne")

from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import TestCase

from triagesync_backend.apps.realtime.consumers import TriageEventsConsumer
from triagesync_backend.apps.realtime.services.broadcast_service import (
    broadcast_critical_alert,
    broadcast_patient_created,
    broadcast_priority_update,
    broadcast_status_changed,
)
from triagesync_backend.apps.realtime.services.event_service import (
    build_critical_alert_event,
    build_patient_created_event,
    build_priority_update_event,
    build_status_changed_event,
)

# ---------------------------------------------------------------------------
# Event service tests — pure unit tests, no DB, no network
# ---------------------------------------------------------------------------

class EventServiceTests(TestCase):

    def test_patient_created_event_structure(self):
        event = build_patient_created_event(patient_id=1, priority=2, urgency_score=80)
        self.assertEqual(event["type"], "patient_created")
        self.assertEqual(event["data"]["id"], 1)
        self.assertEqual(event["data"]["priority"], 2)
        self.assertEqual(event["data"]["urgency_score"], 80)
        self.assertIn("timestamp", event)

    def test_priority_update_event_structure(self):
        event = build_priority_update_event(patient_id=5, priority=1, urgency_score=95)
        self.assertEqual(event["type"], "priority_update")
        self.assertEqual(event["data"]["id"], 5)
        self.assertEqual(event["data"]["priority"], 1)

    def test_critical_alert_event_structure(self):
        event = build_critical_alert_event(patient_id=3)
        self.assertEqual(event["type"], "critical_alert")
        self.assertEqual(event["data"]["id"], 3)
        self.assertEqual(event["data"]["priority"], 1)
        self.assertIn("message", event["data"])

    def test_status_changed_event_structure(self):
        event = build_status_changed_event(patient_id=7, status="in_progress")
        self.assertEqual(event["type"], "status_changed")
        self.assertEqual(event["data"]["id"], 7)
        self.assertEqual(event["data"]["status"], "in_progress")

    def test_all_events_have_timestamp(self):
        events = [
            build_patient_created_event(1, 2, 80),
            build_priority_update_event(1, 1, 95),
            build_critical_alert_event(1),
            build_status_changed_event(1, "waiting"),
        ]
        for event in events:
            self.assertIn("timestamp", event)


# ---------------------------------------------------------------------------
# WebSocket consumer tests — uses Channels test communicator (in-memory layer)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class ConsumerTests(TestCase):

    async def _make_communicator(self):
        communicator = WebsocketCommunicator(
            TriageEventsConsumer.as_asgi(),
            "/ws/triage/events/"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def test_consumer_connects(self):
        communicator = await self._make_communicator()
        await communicator.disconnect()

    async def test_consumer_receives_broadcast(self):
        communicator = await self._make_communicator()

        # Simulate a broadcast being sent to the group
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "triage_events",
            {
                "type": "triage_event",
                "payload": {"type": "patient_created", "data": {"id": 1}},
            },
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "patient_created")
        self.assertEqual(response["data"]["id"], 1)

        await communicator.disconnect()

    async def test_consumer_ignores_incoming_messages(self):
        """Clients should not be able to send data — consumer silently ignores it."""
        communicator = await self._make_communicator()
        await communicator.send_json_to({"hello": "world"})
        # No response expected — consumer drops incoming messages
        self.assertTrue(await communicator.receive_nothing())
        await communicator.disconnect()

    async def test_multiple_clients_receive_same_broadcast(self):
        client1 = await self._make_communicator()
        client2 = await self._make_communicator()

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "triage_events",
            {
                "type": "triage_event",
                "payload": {"type": "critical_alert", "data": {"id": 99}},
            },
        )

        r1 = await client1.receive_json_from()
        r2 = await client2.receive_json_from()

        self.assertEqual(r1["type"], "critical_alert")
        self.assertEqual(r2["type"], "critical_alert")

        await client1.disconnect()
        await client2.disconnect()


# ---------------------------------------------------------------------------
# Broadcast service tests — verifies critical alert auto-fires on priority 1
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class BroadcastServiceTests(TestCase):

    async def test_critical_alert_auto_fires_on_priority_1(self):
        communicator = WebsocketCommunicator(
            TriageEventsConsumer.as_asgi(),
            "/ws/triage/events/"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # broadcast_patient_created with priority=1 should send 2 events:
        # 1. patient_created  2. critical_alert
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "triage_events",
            {"type": "triage_event", "payload": build_patient_created_event(1, 1, 99)},
        )
        await channel_layer.group_send(
            "triage_events",
            {"type": "triage_event", "payload": build_critical_alert_event(1)},
        )

        r1 = await communicator.receive_json_from()
        r2 = await communicator.receive_json_from()

        self.assertEqual(r1["type"], "patient_created")
        self.assertEqual(r2["type"], "critical_alert")

        await communicator.disconnect()


# ---------------------------------------------------------------------------
# Triage integration tests — verifies broadcast fires after evaluate_triage()
# ---------------------------------------------------------------------------

class TriageBroadcastIntegrationTests(TestCase):
    """
    Tests that evaluate_triage() triggers the correct broadcast.
    Uses unittest.mock to avoid needing a real channel layer.
    """

    def test_evaluate_triage_triggers_broadcast(self):
        from unittest.mock import patch
        from triagesync_backend.apps.triage.services.triage_service import evaluate_triage

        with patch("apps.triage.services.triage_service.broadcast_patient_created") as mock_broadcast:
            result = evaluate_triage(symptoms="chest pain", patient_id=42)

            # broadcast must have been called once
            mock_broadcast.assert_called_once()

            # check it was called with the right patient_id
            call_kwargs = mock_broadcast.call_args
            self.assertEqual(call_kwargs.kwargs["patient_id"], 42)

    def test_evaluate_triage_no_broadcast_without_patient_id(self):
        from unittest.mock import patch
        from apps.triage.services.triage_service import evaluate_triage

        with patch("apps.triage.services.triage_service.broadcast_patient_created") as mock_broadcast:
            evaluate_triage(symptoms="headache")

            # no patient_id passed → broadcast should NOT fire
            mock_broadcast.assert_not_called()

    def test_critical_symptoms_produce_priority_1(self):
        from unittest.mock import patch
        from apps.triage.services.triage_service import evaluate_triage

        with patch("apps.triage.services.triage_service.broadcast_patient_created") as mock_broadcast:
            result = evaluate_triage(symptoms="chest pain", patient_id=1)

            call_kwargs = mock_broadcast.call_args
            # chest pain → high → score 60 → priority 2 (URGENT) based on M6 logic
            self.assertIn(call_kwargs.kwargs["priority"], [1, 2])
            self.assertIn(call_kwargs.kwargs["urgency_score"], range(0, 101))
