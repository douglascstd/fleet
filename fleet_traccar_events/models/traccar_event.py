import json
from datetime import datetime, timedelta, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError


def _traccar_datetime(value):
    if not value:
        return False
    if not isinstance(value, str):
        return value
    return (
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
    )


class TraccarEvent(models.Model):
    _name = "traccar.event"
    _description = "Traccar Event"
    _order = "event_time desc, id desc"
    _rec_name = "type"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    traccar_id = fields.Integer(
        string="Traccar ID", copy=False, index=True, readonly=True
    )
    type = fields.Char(required=True, index=True)
    event_time = fields.Datetime(index=True)
    route_day = fields.Date(compute="_compute_route_day", store=True, index=True)
    device_traccar_id = fields.Integer(
        string="Traccar Device ID", index=True, readonly=True
    )
    device_id = fields.Many2one("traccar.device", string="Device", index=True)
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        related="device_id.vehicle_id",
        store=True,
        readonly=True,
    )
    geofence_traccar_id = fields.Integer(
        string="Traccar Geofence ID", index=True, readonly=True
    )
    geofence_id = fields.Many2one("traccar.geofence", string="Geofence", index=True)
    telemetry_id = fields.Many2one("fleet.telemetry", string="Telemetry", index=True)
    position_id = fields.Integer(string="Traccar Position ID", index=True)
    message = fields.Char()
    attributes = fields.Text(default="{}")
    raw_data = fields.Text(default="{}", readonly=True)

    _sql_constraints = [
        (
            "traccar_event_unique_company_traccar_id",
            "unique(company_id, traccar_id)",
            "The Traccar event ID must be unique per company.",
        ),
    ]

    @api.depends("event_time")
    def _compute_route_day(self):
        for event in self:
            event.route_day = (
                fields.Date.to_date(event.event_time) if event.event_time else False
            )

    @api.model
    def _traccar_int(self, value):
        try:
            return int(value) if value not in (None, False, "") else False
        except (TypeError, ValueError):
            return False

    @api.model
    def _get_traccar_event_value(self, item, *names):
        attributes = item.get("attributes") or {}
        for name in names:
            value = item.get(name)
            if value not in (None, False, ""):
                return value
            value = attributes.get(name)
            if value not in (None, False, ""):
                return value
        return False

    @api.model
    def _prepare_values_from_traccar(self, company, item):
        Device = self.env["traccar.device"]
        Geofence = self.env["traccar.geofence"]
        Telemetry = self.env["fleet.telemetry"]
        device_traccar_id = self._traccar_int(
            self._get_traccar_event_value(item, "deviceId", "device_id")
        )
        geofence_traccar_id = self._traccar_int(
            self._get_traccar_event_value(item, "geofenceId", "geofence_id", "geofence")
        )
        position_id = self._traccar_int(
            self._get_traccar_event_value(item, "positionId", "position_id", "position")
        )

        device = Device.search(
            [("company_id", "=", company.id), ("traccar_id", "=", device_traccar_id)],
            limit=1,
        )
        geofence = Geofence.browse()
        if geofence_traccar_id:
            geofence = Geofence.search(
                [
                    ("company_id", "=", company.id),
                    ("traccar_id", "=", geofence_traccar_id),
                ],
                limit=1,
            )
        telemetry = Telemetry.browse()
        if position_id:
            telemetry = Telemetry.search(
                [
                    ("company_id", "=", company.id),
                    ("provider", "=", "traccar"),
                    ("traccar_position_id", "=", position_id),
                ],
                limit=1,
            )
        event_time = telemetry.fix_time or _traccar_datetime(item.get("eventTime"))
        return {
            "company_id": company.id,
            "traccar_id": item.get("id"),
            "type": item.get("type") or "unknown",
            "event_time": event_time,
            "device_traccar_id": device_traccar_id,
            "device_id": device.id,
            "geofence_traccar_id": geofence_traccar_id,
            "geofence_id": geofence.id,
            "telemetry_id": telemetry.id,
            "position_id": position_id,
            "message": item.get("message"),
            "attributes": json.dumps(item.get("attributes") or {}, ensure_ascii=True),
            "raw_data": json.dumps(item, ensure_ascii=True),
        }

    @api.model
    def _relink_missing_relations(self, company):
        events = self.search(
            [
                ("company_id", "=", company.id),
                "|",
                ("geofence_id", "=", False),
                "|",
                ("device_id", "=", False),
                ("telemetry_id", "=", False),
            ]
        )
        Geofence = self.env["traccar.geofence"]
        Device = self.env["traccar.device"]
        Telemetry = self.env["fleet.telemetry"]
        for event in events:
            values = {}
            if not event.geofence_id and event.geofence_traccar_id:
                geofence = Geofence.search(
                    [
                        ("company_id", "=", company.id),
                        ("traccar_id", "=", event.geofence_traccar_id),
                    ],
                    limit=1,
                )
                if geofence:
                    values["geofence_id"] = geofence.id
            if not event.device_id and event.device_traccar_id:
                device = Device.search(
                    [
                        ("company_id", "=", company.id),
                        ("traccar_id", "=", event.device_traccar_id),
                    ],
                    limit=1,
                )
                if device:
                    values["device_id"] = device.id
            if not event.telemetry_id and event.position_id:
                telemetry = Telemetry.search(
                    [
                        ("company_id", "=", company.id),
                        ("provider", "=", "traccar"),
                        ("traccar_position_id", "=", event.position_id),
                    ],
                    limit=1,
                )
                if telemetry:
                    values["telemetry_id"] = telemetry.id
                    if event.event_time != telemetry.fix_time:
                        values["event_time"] = telemetry.fix_time
            if values:
                event.write(values)

    def _find_existing_event(self, company, values):
        domain = [("company_id", "=", company.id)]
        if values.get("traccar_id"):
            return self.search(
                domain + [("traccar_id", "=", values["traccar_id"])], limit=1
            )
        return self.search(
            domain
            + [
                ("type", "=", values.get("type")),
                ("event_time", "=", values.get("event_time")),
                ("device_id", "=", values.get("device_id")),
                ("position_id", "=", values.get("position_id")),
                ("geofence_id", "=", values.get("geofence_id")),
            ],
            limit=1,
        )

    @api.model
    def _sync_company_events(self, company, date_from=False, date_to=False):
        Device = self.env["traccar.device"]
        devices = Device.search(
            [("company_id", "=", company.id), ("traccar_id", "!=", False)]
        )
        date_to = date_to or fields.Datetime.now()
        if not date_from:
            last_event = self.search(
                [("company_id", "=", company.id)], order="event_time desc", limit=1
            )
            date_from = last_event.event_time or (date_to - timedelta(days=7))
        created_count = 0
        updated_count = 0
        for device in devices:
            events = company._traccar_request(
                "GET",
                "/api/reports/events",
                params={
                    "deviceId": device.traccar_id,
                    "from": fields.Datetime.to_string(date_from).replace(" ", "T")
                    + "Z",
                    "to": fields.Datetime.to_string(date_to).replace(" ", "T") + "Z",
                },
            )
            if isinstance(events, dict):
                raise UserError(events.get("message") or str(events))
            for item in events or []:
                values = self._prepare_values_from_traccar(company, item)
                existing = self._find_existing_event(company, values)
                if existing:
                    existing.write(values)
                    updated_count += 1
                else:
                    self.create(values)
                    created_count += 1
        self._relink_missing_relations(company)
        return created_count, updated_count

    def action_sync_events(self):
        companies = self.mapped("company_id") or self.env.company
        created_count = 0
        updated_count = 0
        for company in companies:
            created, updated = self.with_company(company)._sync_company_events(company)
            created_count += created
            updated_count += updated
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Traccar Events"),
                "message": _(
                    "Events synchronized. Created: %(created)s. Updated: %(updated)s.",
                    created=created_count,
                    updated=updated_count,
                ),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }
