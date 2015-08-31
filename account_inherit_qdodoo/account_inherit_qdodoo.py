# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import fields,osv
import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class account_inherit_qdodoo(osv.osv):
    _inherit = 'account.move'

    def _get_text(self,cr, uid, ids, field_names, args, context=None):
        res = ''
        obj = self.browse(cr, uid, ids[0])
        create_name = obj.create_uid.partner_id.name
        create_date = datetime.datetime.strftime(datetime.datetime.strptime(obj.create_date,DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8),DEFAULT_SERVER_DATETIME_FORMAT)
        write_name = obj.write_uid.partner_id.name
        write_date = datetime.datetime.strftime(datetime.datetime.strptime(obj.write_date,DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8),DEFAULT_SERVER_DATETIME_FORMAT)
        if create_name:
            res += '%s %s创建单据\n'%(create_date,create_name)
        if write_name:
            res += '%s %s最后修改单据'%(write_date,write_name)
        return {ids[0]:res}
    _columns = {
        'log_text': fields.function(_get_text,type='text',string='操作记录'),
        'create_uid' : fields.many2one('res.users',u'创建人',readonly=True),
        'write_uid' : fields.many2one('res.users',u'最后修改人',readonly=True),
        'create_date': fields.datetime(u'创建时间',readonly=True),
        'write_date': fields.datetime(u'最后修改时间',readonly=True),
    }


