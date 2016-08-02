# encoding:utf-8
from openerp import models, fields, api


class qdodoo_account_analytic_init(models.Model):
    _name = 'qdodoo.account.analytic.init'

    @api.one
    def action_done(self):
        sql = """
        select
            aal.id as aal_id,
            ap.id as ap_id
        from account_analytic_line aal
            LEFT JOIN account_period ap on ap.date_start <= aal.date and ap.date_stop >= aal.date and ap.company_id=aal.company_id
        where aal.period_id2 is NULL
        """
        self.env.cr.execute(sql)
        res = self.env.cr.fetchall()
        if res:
            for res_l in res:
                if res_l[1]:
                    sql_move = """
                    update account_analytic_line set period_id2 = %s where id = %s
                    """ % (res_l[1], res_l[0])
                    self.env.cr.execute(sql_move)

