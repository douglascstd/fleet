import json

from odoo import _, api, fields, models


class TraccarGeofence(models.Model):
    _name = "traccar.geofence"
    _description = "Traccar Geofence"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, id"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    traccar_id = fields.Integer(
        string="Traccar ID", copy=False, index=True, readonly=True
    )
    name = fields.Char(required=True, tracking=True)
    description = fields.Text()
    area = fields.Text(required=True, help="Traccar geofence area expression.")
    calendar_id = fields.Integer(string="Traccar Calendar ID", readonly=True)
    attributes = fields.Text(default="{}")
    active = fields.Boolean(default=True)
    event_ids = fields.One2many("traccar.event", "geofence_id", string="Events")
    event_count = fields.Integer(compute="_compute_event_count")

    _sql_constraints = [
        (
            "traccar_geofence_unique_company_traccar_id",
            "unique(company_id, traccar_id)",
            "The Traccar geofence ID must be unique per company.",
        ),
    ]

    @api.depends("event_ids")
    def _compute_event_count(self):
        grouped = self.env["traccar.event"].read_group(
            [("geofence_id", "in", self.ids)], ["geofence_id"], ["geofence_id"]
        )
        counts = {item["geofence_id"][0]: item["geofence_id_count"] for item in grouped}
        for geofence in self:
            geofence.event_count = counts.get(geofence.id, 0)

    @api.model
    def _prepare_values_from_traccar(self, company, item):
        return {
            "company_id": company.id,
            "traccar_id": item.get("id"),
            "name": item.get("name") or str(item.get("id")),
            "description": item.get("description"),
            "area": item.get("area") or "",
            "calendar_id": item.get("calendarId"),
            "attributes": json.dumps(item.get("attributes") or {}, ensure_ascii=True),
        }

    @api.model
    def _sync_company_geofences(self, company):
        geofences = company._traccar_request("GET", "/api/geofences")
        created_count = 0
        updated_count = 0
        for item in geofences or []:
            traccar_id = item.get("id")
            if not traccar_id:
                continue
            values = self._prepare_values_from_traccar(company, item)
            geofence = self.search(
                [("company_id", "=", company.id), ("traccar_id", "=", traccar_id)],
                limit=1,
            )
            if geofence:
                geofence.write(values)
                updated_count += 1
            else:
                self.create(values)
                created_count += 1
        self.env["traccar.event"]._relink_missing_relations(company)
        return created_count, updated_count

    def action_sync_geofences(self):
        companies = self.mapped("company_id") or self.env.company
        created_count = 0
        updated_count = 0
        for company in companies:
            created, updated = self.with_company(company)._sync_company_geofences(
                company
            )
            created_count += created
            updated_count += updated
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Traccar Geofences"),
                "message": _(
                    "Geofences synchronized. Created: %(created)s. Updated: %(updated)s.",  # noqa: E501
                    created=created_count,
                    updated=updated_count,
                ),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def action_view_events(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Traccar Events"),
            "res_model": "traccar.event",
            "view_mode": "list,form",
            "domain": [("geofence_id", "=", self.id)],
            "context": {
                "default_geofence_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }
