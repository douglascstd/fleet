{
    "name": "Fleet SIM",
    "summary": "SIM card contract management for the fleet",
    "version": "18.0.1.0.0",
    "category": "Fleet",
    "author": "Ragna, douglascstd@yahoo.com, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/fleet",
    "maintainers": ["douglascstd"],
    "license": "AGPL-3",
    "depends": ["fleet", "mail"],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/fleet_sim_card_views.xml",
        "views/fleet_sim_menu.xml",
    ],
    "application": False,
    "installable": True,
}
