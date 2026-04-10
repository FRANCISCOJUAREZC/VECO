# -*- coding: utf-8 -*-

{
    'name': 'Nomina Electrónica Veco ',
    'summary': 'Agrega modificacion en los cálculos de días semanales.',
    'description': '''
    Nomina CFDI Module
    ''',
    'author': 'IT Admin',
    'version': '19.1.1',
    'category': 'Employees',
    'depends': [
        'hr_payroll','hr_payroll_account','nomina_cfdi_ee'
    ],
    'data': [
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
