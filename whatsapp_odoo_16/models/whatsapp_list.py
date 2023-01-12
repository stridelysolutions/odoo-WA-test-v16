# -*- coding: utf-8 -*-

from odoo import models, fields

class WhatsappList(models.Model):
    _name = 'whatsapp.list'
    
    name = fields.Char(string='WhatsApp List')
    customer_ids = fields.Many2many(
        string='Recipients',
        comodel_name='res.partner',
    )
