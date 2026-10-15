from odoo import api, fields, models


class FleetSimCard(models.Model):
    _name = "fleet.sim.card"
    _description = "Fleet SIM Card"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    display_name = fields.Char(
        compute="_compute_display_name", store=True, readonly=False
    )
    phone_number = fields.Char(required=True, tracking=True)
    imei = fields.Char(string="IMEI", tracking=True)
    carrier = fields.Char(tracking=True)
    contract_date = fields.Date(tracking=True)
    contract_expiration_date = fields.Date(tracking=True)
    billing_period = fields.Selection(
        [("monthly", "Monthly"), ("annual", "Annual")],
        default="monthly",
        required=True,
        tracking=True,
    )
    contract_amount = fields.Monetary(currency_field="currency_id", tracking=True)
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "fleet_sim_card_unique_company_phone",
            "unique(company_id, phone_number)",
            "The phone number must be unique per company.",
        ),
        (
            "fleet_sim_card_unique_company_imei",
            "unique(company_id, imei)",
            "The IMEI must be unique per company.",
        ),
    ]

    @api.depends("phone_number", "carrier")
    def _compute_display_name(self):
        for sim in self:
            sim.display_name = " - ".join(
                part for part in [sim.phone_number, sim.carrier] if part
            )
