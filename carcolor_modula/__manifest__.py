
{
    "name": "Modula api",
    "summary": "Modulo connettore modula odoo",
    "version": "18.0.1.0.0",
    "category": "Carcolor",
    "website": "",
    "author": "Carcolor",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "web",
        "base"
    ],
    "data": [
        "views/stock_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'web/static/lib/owl/owl.js',
            'carcolor_modula/static/src/js/modula_sync_action.js',
            'carcolor_modula/static/src/xml/modula_sync_action.xml',
        ],
    },
}