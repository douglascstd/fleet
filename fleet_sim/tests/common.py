from odoo.addons.base.tests.common import BaseCommon


class FleetSimCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.SimCard = cls.env["fleet.sim.card"]

    @classmethod
    def _create_sim_card(cls, **values):
        vals = {
            "company_id": cls.company.id,
            "phone_number": "+55 11 99999-0001",
            "carrier": "Test Carrier",
        }
        vals.update(values)
        return cls.SimCard.create(vals)
