#-*- coding:utf-8 -*-
##############################################################################
#
#    Author:Kevin Kong 2014 (kfx2007@163.com)
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

from openerp import models,api,_,fields

class yj_hr(models.Model):
	_name="yj.hr.attendance"

	name = fields.Many2one('hr.employee',string="Employee",required=True)
	e_no = fields.Char(related='name.e_no',string='E_No',readonly=True)
	department = fields.Many2one(related='name.department_id',string='Department',relation='hr.department',readonly=True)
	hours = fields.Integer('Hours')
	in_abs = fields.Integer('Entry Absence')
	out_abs = fields.Integer('Dimiss Absence')
	buiness_leave = fields.Integer('Buiness Leave')
	maternity_leave = fields.Integer('Maternity Leave')
	ill_leave = fields.Integer('Ill Leave')
	occupational_injury = fields.Integer('Occupational Injury')
	marriage_leave = fields.Integer('Marriage Leave')
	funeral_leave = fields.Integer('Funeral Leave')
	annual_leave = fields.Integer('Annual Leave')
	sick_leave = fields.Integer('Sick Leave')
	antenatal_leave = fields.Integer('Antenatal Leave')
        absence = fields.Integer('Absence')
	late_early = fields.Integer('Arriving Late and Leaving Early')
	dalay = fields.Integer('Delay')
	day_off = fields.Integer('Day Off')
	over_work = fields.Integer('Over Work')
	weekend_overwork = fields.Integer('Weekend Work')
	holiday_overwork = fields.Integer('Holiday OverWork')
	


