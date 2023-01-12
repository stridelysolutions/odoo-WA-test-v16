# -*- coding: utf-8 -*-

from odoo import models,fields,api
import requests
from odoo.http import request
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
       
    whats_app = fields.Boolean(
        string='Whats App',
        compute= "whatsapp_status"
    )

    def action_send_whatsapp(self):
        self.ensure_one()
        compose_form_id = self.env.ref('whatsapp_odoo.whatsapp_message_wizard_form').id
        ctx = dict(self.env.context)
        message = "Hi" + " " + self.partner_id.name + ',' + '\n' + "Your quotation" + ' ' + self.name + ' ' + "amounting" + ' ' + str(
            self.amount_total) + self.currency_id.symbol + ' ' + "is ready for review.Do not hesitate to contact us if you have any questions."
        lang = self.env.context.get('lang')
        mail_template = self._find_mail_template()
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]
        ctx.update({
            'default_message': message,
            'default_partner_id': self.partner_id.id,
            'default_whatsapp_no': self.partner_id.phone,
            'default_image_1920': self.partner_id.image_1920,
            'default_template_id': mail_template.id if mail_template else None,
            'default_model': 'sale.order',
            'sale_id':self.id
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
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        whats_app = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.whats_app')
        token = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.token_key')
        end_point = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.end_point')
        url_portal = self.get_portal_url()
        url = ''
        try:
            url = url + request.httprequest.host_url
        except:
            pass
        if whats_app:
            if not end_point or not token:
                raise ValidationError("Please enter End Point or Token")
            else:
                if self.partner_id.whatsapp_no:
                    message_data = "Hi" + " " + self.partner_id.name + ',' +  '\n\n' + "Your Order are confirmed " + self.name + " is ready for review. "+'\n\n'+str(url[:len(url)-1]+url_portal)+"\n\n"+"Do not hesitate to contact us if you have any questions."
                    if self.state == 'sale':
                        url = "https://"+end_point+"/api/v1/sendSessionMessage/"+str(self.partner_id.whatsapp_no)+"?messageText="+message_data
                        headers = {"Authorization": token}
                        response = requests.post(url, headers=headers)
                        try:
                            error_msg=response.json()['message']
                        except:
                            error_msg=response.json()['info']
                        if response.json()['result'] == 'success':
                            message_data_change = message_data.replace("\n", "<br/>")
                            self.message_post(body=message_data_change)
                            self.env['message.history'].create({
                                'message':message_data,
                                'mobile':self.partner_id.whatsapp_no,
                                'status':'success'
                            })
                        else:
                            self.env['message.history'].create({
                                'message':message_data,
                                'mobile':self.partner_id.whatsapp_no,
                                'message_error':error_msg,
                                'status':'error'
                            })   

        return res

    @api.depends('whats_app')
    def whatsapp_status(self):
        for status in self:
            whats_app = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.whats_app')
            status.whats_app = whats_app
     
    def write(self,values):
        res = super(SaleOrder, self).write(values)
        if 'order_line' in values.keys():
            for product in values['order_line']:
                if product[0] == 0 or product[0] == 1:
                    whats_app = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.whats_app')
                    token = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.token_key')
                    end_point = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.end_point')
                    url_portal = self.get_portal_url()
                    url = ''
                    try:
                        url = url + request.httprequest.host_url
                    except:
                        pass
                    if whats_app:
                        if not end_point or not token:
                            raise ValidationError("Please enter End Point or Token")
                        else:
                            if self.partner_id.whatsapp_no:
                                message_data = "Hi" + " " + self.partner_id.name + ',' + '\n\n' + "Your Order are modified " + self.name + " is ready for review. "+'\n'+str(url[:len(url)-1]+url_portal)+'\n\n'+"Do not hesitate to contact us if you have any questions."
                                if self.state == 'sale':
                                    url = "https://"+end_point+"/api/v1/sendSessionMessage/"+str(self.partner_id.whatsapp_no)+"?messageText="+message_data
                                    headers = {"Authorization": token}
                                    response = requests.post(url, headers=headers)
                                    try:
                                        error_msg=response.json()['message']
                                    except:
                                        error_msg=response.json()['info']
                                    if response.json()['result'] == 'success':
                                        self.message_post(body=message_data)
                                        self.env['message.history'].create({
                                            'message':message_data,
                                            'mobile':self.partner_id.whatsapp_no,
                                            'status':'success'
                                        })
                                    else:
                                        self.env['message.history'].create({
                                            'message':message_data,
                                            'mobile':self.partner_id.whatsapp_no,
                                            'message_error':error_msg,
                                            'status':'error'
                                        })
