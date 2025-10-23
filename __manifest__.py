{
    "name": "Graduación de Pacientes",
    "version": "1.2",
    "category": "Optometry",
    "summary": "Modulo de optometria para las graduaciones de los pacientes integra una pestanaña de diagostico para astigmatismo trasposicion notacion bicilindrica calcula distancia al vertice",
    "author": "Christian Torres PeeWee",
    "license": "LGPL-3",
    "depends": ["base", "web", "contacts"],
    "data": [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/series_rx_data.xml',
        'views/graduacion_view.xml',
        'views/laboratorio_views.xml',
        'views/serie_rx_views.xml',
        'views/product_views.xml',
        'views/cotizador_views.xml',
        'views/menu_views.xml',
        'report/graduacion_report.xml',
   
    ],
    "assets": {
        "web.assets_backend": [
            "odoo_graduacion_paciente/static/src/css/graduacion_btn_combo.css",
        ],
    },
    "installable": True,
    "application": True,
}

