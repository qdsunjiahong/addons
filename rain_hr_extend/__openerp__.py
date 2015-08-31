# -*- coding: utf-8 -*-
{
    'name': '人力资源模块扩展',
    'category': 'hr',
    'summary': '人力资源模块扩展',
    'version': '1.0',
    'description': """
雨水人力资源模块扩展
=================
    1.用于工资模块
        """,
    'author': 'Tiger',
    'depends': ['hr','hr_payroll','rain_hr','hm_hr'],
    'data': [
        'views/hr_payslip_view.xml','views/hr_department_view.xml','views/hr_contract_views.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
