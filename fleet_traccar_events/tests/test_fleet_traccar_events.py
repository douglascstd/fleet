from datetime import datetime
from unittest.mock import patch

from odoo.addons.fleet_traccar_events.models.traccar_event import _traccar_datetime

from .common import FleetTraccarEventsCommon


class TestFleetTraccarEvents(FleetTraccarEventsCommon):
    def test_traccar_datetime(self):
        self.assertFalse(_traccar_datetime(False))
        self.assertEqual(
            _traccar_datetime("2026-01-10T10:00:00.000Z"),
            datetime(2026, 1, 10, 10, 0),
        )

    def test_traccar_int(self):
        self.assertFalse(self.Event._traccar_int(None))
        self.assertFalse(self.Event._traccar_int("x"))
        self.assertEqual(self.Event._traccar_int("42"), 42)
        self.assertEqual(self.Event._traccar_int(7), 7)

    def test_get_traccar_event_value(self):
        item = {"deviceId": 42, "attributes": {"geofenceId": 7}}
        self.assertEqual(self.Event._get_traccar_event_value(item, "deviceId"), 42)
        self.assertEqual(
            self.Event._get_traccar_event_value(item, "geofenceId", "geofence"), 7
        )
        self.assertFalse(
            self.Event._get_traccar_event_value(item, "positionId", "position")
        )

    def test_sync_company_geofences(self):
        geofences = [
            {
                "id": 1,
                "name": "Geofence 1",
                "description": "Zone",
                "area": "circle: -23.5, -46.6, 100",
                "calendarId": 3,
                "attributes": {"a": 1},
            }
        ]
        with patch.object(
            type(self.company), "_traccar_request", return_value=geofences
        ) as mocked:
            created, updated = self.Geofence._sync_company_geofences(self.company)
        self.assertEqual((created, updated), (1, 0))
        mocked.assert_called_once()
        geofence = self.Geofence.search([("traccar_id", "=", 1)])
        self.assertEqual(geofence.name, "Geofence 1")
        self.assertEqual(geofence.description, "Zone")
        self.assertEqual(geofence.calendar_id, 3)
        with patch.object(
            type(self.company), "_traccar_request", return_value=geofences
        ):
            created, updated = self.Geofence._sync_company_geofences(self.company)
        self.assertEqual((created, updated), (0, 1))

    def test_action_sync_geofences(self):
        with patch.object(type(self.company), "_traccar_request", return_value=[]):
            action = self.Geofence.action_sync_geofences()
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "display_notification")

    def test_sync_company_events(self):
        geofence = self.Geofence.create(
            {
                "company_id": self.company.id,
                "name": "Geofence 1",
                "area": "circle",
                "traccar_id": 1,
            }
        )
        events = [
            {
                "id": 100,
                "type": "geofenceEnter",
                "eventTime": "2026-01-10T10:00:00.000Z",
                "deviceId": 42,
                "geofenceId": 1,
                "positionId": 55,
                "message": "entered",
                "attributes": {"speed": 10},
            }
        ]
        with patch.object(type(self.company), "_traccar_request", return_value=events):
            created, updated = self.Event._sync_company_events(self.company)
        self.assertEqual((created, updated), (1, 0))
        event = self.Event.search([("traccar_id", "=", 100)])
        self.assertEqual(event.type, "geofenceEnter")
        self.assertEqual(event.event_time, datetime(2026, 1, 10, 10, 0))
        self.assertEqual(event.device_id, self.device)
        self.assertEqual(event.geofence_id, geofence)
        self.assertEqual(event.position_id, 55)
        self.assertEqual(event.message, "entered")
        with patch.object(type(self.company), "_traccar_request", return_value=events):
            created, updated = self.Event._sync_company_events(self.company)
        self.assertEqual((created, updated), (0, 1))
        self.assertEqual(self.Event.search_count([("traccar_id", "=", 100)]), 1)

    def test_relink_missing_relations(self):
        geofence = self.Geofence.create(
            {
                "company_id": self.company.id,
                "name": "Geofence 1",
                "area": "circle",
                "traccar_id": 1,
            }
        )
        event = self.Event.create(
            {
                "company_id": self.company.id,
                "traccar_id": 200,
                "type": "geofenceEnter",
                "event_time": "2026-01-10 10:00:00",
                "device_traccar_id": 42,
                "geofence_traccar_id": 1,
            }
        )
        self.assertFalse(event.device_id)
        self.assertFalse(event.geofence_id)
        self.Event._relink_missing_relations(self.company)
        self.assertEqual(event.device_id, self.device)
        self.assertEqual(event.geofence_id, geofence)

    def test_data_records(self):
        self.assertTrue(self.env.ref("fleet_traccar_events.action_traccar_geofence"))
        self.assertTrue(self.env.ref("fleet_traccar_events.action_traccar_event"))
        self.assertTrue(self.env.ref("fleet_traccar_events.menu_traccar_geofence"))
        self.assertTrue(self.env.ref("fleet_traccar_events.menu_traccar_event"))
