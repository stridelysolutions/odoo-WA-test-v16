# -*- coding: utf-8 -*-

{
    'name': "whatsapp_odoo",

    'summary': """
     Whats App Odoo""",

    'description': """
       Whats App Odoo
    """,
    'author': "Stridely Solutions",
    'website': "https://www.stridelysolutions.com/",
    'category': 'Technical',
    'version': '0.1',
    'depends': ['base','sale_management','account','stock','mass_mailing','purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_inherited.xml',
        'views/sale_portal_templates.xml',
        'views/sale_order_inherited.xml',
        'views/whatsapp_template.xml',
        'views/whatsapp_list.xml',
        'views/template_design.xml',
        'views/account_move.xml',
        'views/res_partner.xml',
        'views/res_config_settings.xml',
        'views/message_reduce_scheduled.xml',
        'wizard/wh_message_wizard.xml',
        'data/ir_sequence_data.xml',
        'views/message_history.xml'
    ],
'assets': {
        'web.assets_backend': [
        'whatsapp_odoo/static/src/js/whatsapp_html_field.js',
        'whatsapp_odoo/static/src/scss/mass_mailing.scss',
        ],
},
    
    'license': 'LGPL-3',
}
