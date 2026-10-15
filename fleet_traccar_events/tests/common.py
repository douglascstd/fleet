from odoo.addons.base.tests.common import BaseCommon


class FleetTraccarEventsCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write(
            {
                "traccar_enabled": True,
                "traccar_base_url": "https://traccar.example.com",
                "traccar_username": "user",
                "traccar_password": "secret",
            }
        )
        cls.Device = cls.env["traccar.device"]
        cls.Geofence = cls.env["traccar.geofence"]
        cls.Event = cls.env["traccar.event"]
        cls.device = cls.Device.with_context(skip_traccar_remote_create=True).create(
            {
                "name": "Tracker 1",
                "unique_id": "TRC-1",
                "company_id": cls.company.id,
                "traccar_id": 42,
            }
        )
