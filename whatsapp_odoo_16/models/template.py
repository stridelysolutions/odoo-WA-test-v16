# -*- coding: utf-8 -*-

from odoo import models, fields


class Template(models.Model):
    _name = 'template.design'
    
    name = fields.Char(string="Name")
    body_arch = fields.Html(string='Body')
    body_html = fields.Html(string='Body converted to be sent by mail', sanitize=False)
