# -*- coding: utf-8 -*-

from odoo import models,fields,api
import requests
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    whats_app = fields.Boolean(
        string='Whats App',
        compute= "whatsapp_status"
    )
    
    def action_send_whatsapp(self):
        compose_form_id = self.env.ref('whatsapp_odoo.whatsapp_message_wizard_form').id
        ctx = dict(self.env.context)
        message = "Hi" + " " + self.partner_id.name + ',' + '\n\n' + "Here is your invoice" + ' ' + self.name + ' ' + "amounting" + ' ' + str(
            self.amount_total) + self.currency_id.symbol + ' from '+self.company_id.name + ".\n\n"+"Do not hesitate to contact us if you have any questions.\n\n"+self.user_id.name
        template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
        lang = False
        if template:
            lang = template._render_lang(self.ids)[self.id]
        if not lang:
            lang = get_lang(self.env).code
        ctx.update({
            'default_message': message,
            'default_partner_id': self.partner_id.id,
            'default_mobile': self.partner_id.whatsapp_no,
            'default_image_1920': self.partner_id.image_1920,
            'default_template_id': template.id if template else None,
            'default_model': 'account.move',
            'invoice_id':self.id
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'whatsapp.message.wizard',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        
    def action_post(self):
        for invoice in self:
            res = super().action_post()
            if invoice.move_type == 'out_refund':
                whats_app = invoice.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.whats_app')
                token = invoice.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.token_key')
                end_point = invoice.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.end_point')
                if whats_app:
                    if not end_point or not token:
                        raise ValidationError("Please enter End Point or Token")
                    else:
                        message_data = "Hi" + " " + invoice.partner_id.name + ',' + '\n\n' + "We’ve processed your refund amount "+ str(
                        invoice.amount_total) + invoice.currency_id.symbol+", and you should expect to see the amount credited to your account in about 3 to 5 business days from " +invoice.company_id.name + ".\n\n"+"Do not hesitate to contact us if you have any questions.\n\n"+invoice.user_id.name
                        url = "https://"+end_point+"/api/v1/sendSessionMessage/"+str(invoice.partner_id.whatsapp_no)+"?messageText="+message_data
                        headers = {"Authorization": token}
                        response = requests.post(url, headers=headers)
    
    @api.depends('whats_app')
    def whatsapp_status(self):
        for status in self:
            whats_app = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.whats_app')
            status.whats_app = whats_app
