# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2012 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2012-2013 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Export Current View',
    'version': '1.2',
    'category': 'Web',
    'description': """
WEB EXPORT VIEW
===============
1.修改原来的7.0版本，适合8.0使用。
""",
    'author': 'sun',
    'website': 'http://www.rainsoft.com',
    'license': 'AGPL-3',
    'depends': ['web'],
    'data':[
        'views/web_export_view.xml'
    ],
    # 'external_dependencies': {
    #     'python': ['xlwt'],
    # },
    'css':['static/css/style.css'],
    # 'js': ['static/*/*.js', 'static/*/js/*.js'],
    # 'js' : ['static/js/web_advanced_export.js'],
    'qweb': ['static/xml/web_advanced_export.xml'],
    'installable': True,
    'auto_install': False,
    'web_preload': False,
}
