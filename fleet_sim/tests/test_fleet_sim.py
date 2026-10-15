from psycopg2 import IntegrityError

from odoo.exceptions import AccessError
from odoo.tests import new_test_user
from odoo.tools import mute_logger

from .common import FleetSimCommon


class TestFleetSim(FleetSimCommon):
    def test_compute_display_name(self):
        sim = self._create_sim_card()
        self.assertEqual(sim.display_name, "+55 11 99999-0001 - Test Carrier")
        sim.carrier = False
        self.assertEqual(sim.display_name, "+55 11 99999-0001")

    def test_unique_phone_per_company(self):
        self._create_sim_card()
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._create_sim_card(imei="IMEI-1")

    def test_unique_imei_per_company(self):
        self._create_sim_card(imei="IMEI-1")
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._create_sim_card(phone_number="+55 11 99999-0002", imei="IMEI-1")

    def test_access_rights(self):
        sim = self._create_sim_card()
        fleet_user = new_test_user(
            self.env, login="fleet_sim_user", groups="fleet.fleet_group_user"
        )
        fleet_manager = new_test_user(
            self.env, login="fleet_sim_manager", groups="fleet.fleet_group_manager"
        )
        self.assertEqual(sim.with_user(fleet_user).phone_number, "+55 11 99999-0001")
        created = self.SimCard.with_user(fleet_user).create(
            {
                "company_id": self.company.id,
                "phone_number": "+55 11 99999-0003",
            }
        )
        with self.assertRaises(AccessError):
            created.with_user(fleet_user).unlink()
        created.with_user(fleet_manager).unlink()
        self.assertFalse(created.exists())

    def test_data_records(self):
        self.assertTrue(self.env.ref("fleet_sim.action_fleet_sim_card"))
        self.assertTrue(self.env.ref("fleet_sim.menu_fleet_sim_root"))
        self.assertTrue(self.env.ref("fleet_sim.group_sim_administrator"))
