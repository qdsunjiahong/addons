# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2013 Amos <sale@100china.cn>
##############################################################################
from openerp.osv import osv, fields
from lxml import etree
from openerp import SUPERUSER_ID


class amos_res_groups(osv.Model):
    amos_menu_ids = []
    _inherit = "res.groups"
    _columns = {
        'value': fields.char(u'值'),
        'inherit_base_id': fields.many2one('res.groups', u'底层'),
        'model_ok': fields.many2many('ir.model', 'amos_groups_model_rel', 'groups_id', 'model_id', U'模块'),
    }

    def amos_access(self, cr, uid, ids, context=None):
        obj = self.pool.get('ir.model.access')
        obj_model = self.pool.get('ir.model')
        if context['perm'] == 'access_create':
            instructors = self.browse(cr, uid, ids)
            for instructor in instructors.model_ok:
                for field in instructor.field_id:
                    if field.ttype == 'many2one' or field.ttype == 'one2many' or field.ttype == 'many2many':
                        model_id = obj_model.search(cr, uid, [('model', '=', field.relation)])
                        model_ = obj.search(cr, uid, [('group_id', '=', ids[0]), ('model_id', '=', model_id[0])])
                        if len(model_) == 0:
                            parm = {
                                'model_id': model_id[0],
                                'group_id': ids[0],
                                'name': instructors.name, }
                            id = obj.create(cr, uid, parm)
                model_id = obj_model.search(cr, uid, [('model', '=', instructor.model)])
                model_ = obj.search(cr, uid, [('group_id', '=', ids[0]), ('model_id', '=', model_id[0])])
                if len(model_) == 0:
                    parm = {
                        'model_id': model_id[0],
                        'group_id': ids[0],
                        'name': instructors.name, }
                    id = obj.create(cr, uid, parm)
            if instructors.inherit_base_id!=False:
                for model in instructors.inherit_base_id.model_access:
                    model_ = obj.search(cr, uid, [('group_id', '=', ids[0]), ('model_id', '=', model.model_id.id)])
                    if len(model_) == 0:
                        parm = {
                            'model_id': model.model_id.id,
                            'group_id': ids[0],
                            'name': instructors.name,
                            'perm_read': model.perm_read,
                            'perm_write': model.perm_write,
                            'perm_create': model.perm_create,
                            'perm_unlink': model.perm_unlink,
                            }
                        id = obj.create(cr, uid, parm)
        elif context['perm'] == 'access_base':
            instructors = self.browse(cr, uid, ids)
            if instructors.inherit_base_id!=False:
                for model in instructors.inherit_base_id.model_access:
                    model_ = obj.search(cr, uid, [('group_id', '=', ids[0]), ('model_id', '=', model.model_id.id)])
                    if len(model_) == 0:
                        parm = {
                            'model_id': model.model_id.id,
                            'group_id': ids[0],
                            'name': instructors.name,
                            'perm_read': model.perm_read,
                            'perm_write': model.perm_write,
                            'perm_create': model.perm_create,
                            'perm_unlink': model.perm_unlink,
                            }
                        id = obj.create(cr, uid, parm)
                    else:
                        parm = {
                            'perm_read': model.perm_read,
                            'perm_write': model.perm_write,
                            'perm_create': model.perm_create,
                            'perm_unlink': model.perm_unlink,
                            'name': instructors.name,
                            }
                        obj.write(cr, uid, model_[0], parm)
        elif context['perm'] == 'access_unlink':
            instructors = self.browse(cr, uid, ids)
            arr = []
            for instructor in instructors.model_access:
                arr.append(instructor.id)
            obj.unlink(cr, uid, arr)
        elif context['perm'] == 'access_menu':
            amos_menu_ids = []
            obj_actions = self.pool.get('ir.actions.act_window')
            obj_menu = self.pool.get('ir.ui.menu')
            obj_values = self.pool.get('ir.values')
            #当前的对象 找所有事件，每一个事件都去找菜单，如果存在就一直向上找 只到顶层结束
            #所有菜单ID 存入数组，去重再抛入系统
            instructors = self.browse(cr, uid, ids)
            actions_arr = []
            menu = []
            for instructor in instructors.model_ok:
                actions_id = obj_actions.search(cr, uid, [('res_model', '=', instructor.model)])
                actions_arr += actions_id
            actions_list = {}.fromkeys(actions_arr).keys()
            if len(actions_list) ==0:
                return True
            for m in actions_list:
                actions_menu = obj_values.search_read(cr, uid, [('model', '=', 'ir.ui.menu'),
                                                                ('value', '=', 'ir.actions.act_window,%s' % m)],
                                                      ['res_id'])
                if len(actions_menu) > 0:
                    menu.append(actions_menu[0]['res_id'])
            self.amos_menu_ids += menu
            h = self.amos_menu(cr, uid, menu, context)
            #排序

            menu_list = {}.fromkeys(self.amos_menu_ids).keys()
            print sorted(menu_list, reverse=False)
            parm = {
                'menu_access': [(6, 0,sorted(menu_list, reverse=False))],
            }
            self.write(cr, uid, ids, parm)


        else:
            instructors = self.browse(cr, uid, ids)
            for instructor in instructors.model_access:
                parm = {
                    context['perm']: bool(context['perm_value']),
                }
                obj.write(cr, uid, instructor.id, parm)

        return True

    def amos_menu(self, cr, uid, ids, context=None):
        id_list = []
        obj_menu = self.pool.get('ir.ui.menu')
        for id in ids:
            records = obj_menu.read(cr, uid, id, ['parent_id'])
            if len(records) > 1 and records['parent_id'] != False:
                id_list.append(records['parent_id'][0])
        self.amos_menu_ids += id_list
        if len(id_list) > 0:
            self.amos_menu(cr, uid, id_list, context)
        return True


class amos_res_rule(osv.Model):
    _inherit = "ir.rule"

    _columns = {

        'rule_amos': fields.one2many('ir.rule.formula', 'rule_line', u'规则'),
        'is_rule': fields.boolean(u'更新规则', help=u'如果为True，点击生成规则，会把自定义规则更新到Domain 过滤器,为False不更新'),
    }

    def _get_groups(self, cr, uid, *args):
        #如果父级id存在找到组，然后返回默认参数到界面上
        if args[0].has_key('default_parent_id') == True:
            obj = self.pool.get(args[0]['active_model'])
            records = obj.read(cr, uid, int(args[0]['active_id']), ['group_id'])
            return [records['group_id'][0]]
        return False

    _defaults = {
        'groups': _get_groups,
    }

    def amos_formula(self, cr, uid, ids, context=None):
        #把所有规则拼接到 Domain 过滤器
        instructors = self.browse(cr, uid, ids[0])
        rule = ''
        if instructors.is_rule == True:
            for r in instructors.rule_amos:
                if r.state == False:
                    rule += "%s," % (r.formula)
                else:
                    rule += "('%s','%s',%s)," % (r.fields_id.name, r.state, r.formula)

            parm = {
                'domain_force': '[' + rule + ']',
            }
            self.write(cr, uid, ids, parm)

        assert len(ids) == 1, u'只能返回一条信息'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'base', 'view_rule_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        # ctx.update({
        #             'id': ids[0],
        #             }
        #            )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'res_id': ids[0],
            'target': 'current',
            'nodestroy': True,
            'context': ctx,
        }

        # def amos_formula(self, cr, uid, ids, context=None):
        #     ctx = dict(context)
        #     ctx.update({
        #                 'default_res_id': ids[0],
        #                 'id': ids[0],
        #                 # 'active_id': ids[0],
        #                 # 'active_ids': [ids[0]],
        #                 # 'default_use_template': bool(template_id),
        #                 }
        #                )
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'ir.rule',
        #         'target': 'new',
        #         'context': ctx,
        #     }


class amos_res_groups_ir_rule_formula(osv.Model):
    _name = "ir.rule.formula"
    _description = "ir.rule.formula"

    _columns = {
        'rule_line': fields.many2one('ir.rule', u'规则', required=True, ondelete='cascade'),
        'sequence': fields.integer(u'排序'),
        'name': fields.char(u'公式名称'),
        'fields_id': fields.many2one('ir.model.fields', u'字段', required=True),
        'state': fields.selection([('=', u'='),
                                   ('!=', u'!='),
                                   ('>', u'>'),
                                   ('>=', u'>='),
                                   ('<', u'<'),
                                   ('<=', u'<='),
                                   ('like', u'like'),
                                   ('ilike', u'ilike'),
                                   ('in', u'in'),
                                   ('not in', u'not in'),
                                   ('child_of', u'child_of'),
                                   # ('parent_left', u'parent_left'),
                                   # ('parent_right', u'parent_right'),
                                  ],
                                  u'条件'),
        'formula': fields.text(u'值'),
        'defaults': fields.many2one('ir.rule.value.data', u'属性'),
    }

    def onchange_defaults(self, cr, uid, ids, defaults, fields_id, context=None):
        res = {}
        if defaults and fields_id:
            value_data = self.pool.get('ir.rule.value.data').browse(cr, uid, defaults, context=context)
            fields = self.pool.get('ir.model.fields').browse(cr, uid, fields_id, context=context)
            res['formula'] = value_data.value.replace('%s', fields.name)
        print res
        return {'value': res}


class amos_res_groups_ir_rule_value_data(osv.Model):
    _name = "ir.rule.value.data"
    _description = "ir.rule.value.data"

    _columns = {
        'name': fields.char(u'名称'),
        'value': fields.char(u'值'),
    }

