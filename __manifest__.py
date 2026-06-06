{
    "name": "Graduación de Pacientes",
    "version": "1.2",
    "category": "Optometry",
    "summary": "Registra las graduaciones de pacientes",
    "author": "Christian Torres PeeWee",
    "license": "LGPL-3",
    "depends": ["base", "web", "contacts"],
    "data": [
        "security/ir.model.access.csv",
        "views/graduacion_view.xml",
        "reports/report_historia_templates.xml",
        "reports/report_historia_action.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odoo_graduacion_paciente/static/src/css/graduacion_btn_combo.css",
        ],
    },
    "installable": True,
    "application": True,
}
