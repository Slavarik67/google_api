{
    'name': 'Google Drive Api',
    'version': '1.0',
    'depends': ['base',
                'mrp',
                'uom',
                'odoo_transport_management'
                ],
    'author': 'V.Sapelkin',
    'description' : """ Filling boms from google """,
    'data': [
        'views/py_google_drive_api.xml',
        'security/ir.model.access.csv',
        'views/active_button_google_import.xml',
        'views/active_button_table_export.xml',
        'views/py_google_drive_api_tipovoy.xml',
        # 'views/active_button_google_sale.xml',
        'views/py_product_create.xml',
        # 'views/py_sale_create.xml',
],
}