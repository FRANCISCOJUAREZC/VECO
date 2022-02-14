# -*- coding: utf-8 -*-
{
    "name": "Nomina CFDI SUA/IDSE",
    "author": "IT Admin",
    "version": "12.0.1.0.1",
    "category": "Other",
    "description":"Genera un archivo texto para la carga de de incapacidades, faltas e incidencias para el sistema SUA",
    "depends": ["nomina_cfdi_extras_ee"],
    "data": [
        "wizard/exportar_cfdi_sua_view.xml",
        "views/employee_sua.xml"
    ],
    "license": 'AGPL-3',
    'installable': True,
    'images': [''],
}
