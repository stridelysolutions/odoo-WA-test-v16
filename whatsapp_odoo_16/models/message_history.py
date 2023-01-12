# -*- coding: utf-8 -*-

from odoo import models,fields,api,_
from datetime import date


class MessageHistory(models.Model):
    _name = 'message.history'
    _order = 'date_order desc, id desc'
    
    name = fields.Char(string='Message Reference', required=True,
                          readonly=True, default=lambda self: _('New'))
    message = fields.Text(string="Message")
    mobile = fields.Char(required=True, string="Contact Number")
    date_order = fields.Datetime(string='Order Date', required=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    attachment_ids = fields.Many2many(
        string='Attach A File',
        comodel_name='ir.attachment',
    )
    status = fields.Selection(
        string='Status',
        selection=[('error', 'Error'), ('success', 'Success')]
    )
    message_error = fields.Text(string="Message Error")
    active = fields.Boolean(
        string='Active',
        default=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'message.history') or _('New')
        res = super(MessageHistory, self).create(vals)
        return res
    
    def message_reduce(self):
        search_history = self.env['message.history'].search([('active','=',True)])
        for history in search_history:
            today = date.today()
            number_of_days = today - history.create_date.date()
            if number_of_days.days >= 15:
                history.active = False
