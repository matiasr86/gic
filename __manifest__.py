# -*- coding: utf-8 -*-
{
    'name': "Gic",

    'summary': """
        Aplicación para gestion de cobros en el POS""",

    'description': """
        Gic permite acceder a toda la informacion correspondiente a los cobros
        realizados en el Punto de Venta en un solo lugar. Agiliza los procesos de 
        control y permite conocer una proyección certera sobre cuando y cuanto (calculando
        la quita de todas las deducciones aplicables) se cobrara de aquellos cobros 
        diferidos.
    """,

    'author': "Matias Marinelli",
    'website': "https://www.devcode73.com.ar",
    'icon_image': ['static/description/icon.png'],
    'installable': True,
    'application': True,  # Indica que es una aplicación

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/gic_way.xml',
        'views/gic_deduction.xml',
        'views/gic_pos_payment.xml',
        'views/gic_payment_plan.xml',
        'views/gic_payment_method.xml',
        'views/gic_holiday.xml',
        'views/gic_pos.xml',
        'views/gic_subscription.xml',
        'views/gic_destination.xml',
        'views/gic_dashboard.xml',
        'views/gic_dashboard_payment.xml',
        'views/gic_dashboard_plan.xml',
        'views/menu.xml',
        #'data/gic.way.csv',
        'demo/demo.xml',
    ],
}
