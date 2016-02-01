# __author__:Adger Zhou
# encoding:utf-8

from openerp.osv import osv, fields
from openerp.exceptions import except_orm


class qdodoo_dd_congigure(osv.osv):
    """
    配置钉钉系统参数
    """
    _name = 'qdodoo.dd.congigure'
    _inherit = 'res.config.settings'
    # _description = 'qdodoo.dd.congigure'
    _columns = {
        "dd_corpid": fields.char(string=u'钉钉corpid', required=True),
        "dd_secrect": fields.char(string=u'钉钉secrect', required=True)
    }

    def get_default_val(self, cr, uid, fields, context=None):
        dd_corpid = self.pool.get("ir.config_parameter").get_param(cr, uid, "qdoo.dd.corpid", context=context)
        dd_secrect = self.pool.get("ir.config_parameter").get_param(cr, uid, "qdoo.dd.secrect", context=context)
        res = {"dd_corpid": dd_corpid, "dd_secrect": dd_secrect}
        return res

    def set_default_val(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get('ir.config_parameter')
        for record in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, 'qdoo.dd.corpid', record.dd_corpid, context=context)
            config_parameters.set_param(cr, uid, 'qdoo.dd.secrect', record.dd_secrect, context=context)

    def default_get(self, cr, uid, fields, context=None):
        res = super(qdodoo_dd_congigure, self).default_get(cr, uid, fields, context)
        return res
