# coding:utf-8


from openerp.osv import osv,fields

class hm_partner(osv.osv):
		_inherit='res.partner'

		_columns={
						'city':fields.many2one('hm.city','city'),
						'district':fields.many2one('hm.district','district'),
						'QQ':fields.char('QQ'),
						'is_vip':fields.boolean('VIP'),
						'supervisor':fields.many2one('res.users','Supservisor'),
						'contract_type':fields.char('Contract Type'),
						'supplier_attr':fields.char('Supplier Attribute'),
						}
