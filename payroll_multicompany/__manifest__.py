# -*- coding: utf-8 -*-

{
    "name": "Payroll Multicompany",
    "description": """
    Added mutlti company filter in Payroll models.
    """,
    "version": "12.0.1.0",
    "author": "Nikunj Antala",
    "website": "",
    "category": "Hidden",
    "depends": ["hr_contract","hr_payroll"],
    "data": [
             "security/security.xml",
             "views/hr_payslip_view.xml",
    ],
    "demo": [
        
    ],
    "installable": True,
}
