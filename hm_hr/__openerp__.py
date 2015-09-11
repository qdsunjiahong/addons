#coding:utf-8

{
	"name":"Empoylee Extension For China Company",
	"description":"""
中国人力资源拓展
===================================
* 添加多个适用于中国企业的字段
* 根据身份证号自动计算员工的年龄和性别
        """,
	'author':'Rainsoft',
	'depends':['base','hr','hr_contract','hr_payroll'],
	'data':[
			"hm_employee_view.xml",
			"hr_payroll_fix_view.xml",
			],
	'installable':True,
	'category':'Others',
}
