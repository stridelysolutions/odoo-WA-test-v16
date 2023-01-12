# -*- coding: utf-8 -*-

from odoo import models, fields, api
import io,os,requests
try:
    import base64,PyPDF2
except ImportError as e:
    os.system("pip3 install base64")
    os.system("pip3 install PyPDF2")
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource


class WhatsappSendMessage(models.TransientModel):
    _name = 'whatsapp.message.wizard'

    partner_id = fields.Many2one('res.partner', string="Recipient")
    mobile = fields.Char(required=True, string="Contact Number")
    message = fields.Text(string="Message", required=True)
    image_1920 = fields.Binary(readonly=1,)
    template_id = fields.Many2one('mail.template', 'Use template', domain="[('model', '=', model)]")
    model = fields.Char('Related Document Model')    
    attachment_ids = fields.Many2many(
        string='Attach A File',
        comodel_name='ir.attachment',
    )
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        sale_id = self.env.context.get('sale_id')
        invoice_id = self.env.context.get('invoice_id')
        purchase_id = self.env.context.get('purchase_id')
        self.mobile = self.partner_id.whatsapp_no
        self.image_1920 = self.partner_id.image_1920
        search_mail_template = self.env['mail.template'].search([('id','=',self.template_id.id)])
        if sale_id:
            values = self.env['mail.compose.message'].generate_email_for_composer(
                    search_mail_template.id, [sale_id],
                    ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc',  'reply_to', 'attachment_ids', 'mail_server_id']
                )[sale_id]
        if invoice_id:
            values = self.env['mail.compose.message'].generate_email_for_composer(
                    search_mail_template.id, [invoice_id],
                    ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc',  'reply_to', 'attachment_ids', 'mail_server_id']
                )[invoice_id]
        if purchase_id:
            values = self.env['mail.compose.message'].generate_email_for_composer(
                    search_mail_template.id, [purchase_id],
                    ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc',  'reply_to', 'attachment_ids', 'mail_server_id']
                )[purchase_id]
        attachment_ids = []
        Attachment = self.env['ir.attachment']
        for attach_fname, attach_datas in values.pop('attachments', []):
            data_attach = {
                'name': attach_fname,
                'datas': attach_datas,
                'res_model': 'mail.compose.message',
                'res_id': 0,
                'type': 'binary',
            }
            attachment_ids.append(Attachment.create(data_attach).id)
        self.attachment_ids = attachment_ids
    
    def create_pdf(self,attachment):
        writer = PyPDF2.PdfFileWriter()
        reader = PyPDF2.PdfFileReader(io.BytesIO(base64.b64decode(attachment.datas)), strict=False, overwriteWarnings=False)
        writer.addPage(reader.getPage(0))
        pdf_path = get_module_resource('whatsapp_odoo', 'static', 'template.html')
        pdf_path = pdf_path.replace('template.html','') + attachment.name
        output = open(pdf_path,'wb')
        writer.write(output)
        output.close()

    def send_message(self):
        if self.message and self.mobile:
            whats_app = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.whats_app')
            token = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.token_key')
            end_point = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.end_point')
            if whats_app:
                if not end_point or not token:
                    raise ValidationError("Please enter End Point or Token")
                else:
                    url = "https://"+end_point+"/api/v1/sendSessionMessage/"+str(self.mobile)+"?messageText="+self.message
                    headers = {"Authorization": token}
                    response = requests.post(url, headers=headers)
                    if self.attachment_ids:
                        for attachment in self.attachment_ids:
                            if attachment.name.split('.')[1] == 'pdf':
                                self.create_pdf(attachment)
                                pdf_path = get_module_resource('whatsapp_odoo', 'static', attachment.name)
                                url_file = "https://"+end_point+"/api/v1/sendSessionFile/"+str(self.mobile)
                                files = {"file": (attachment.name, open(pdf_path, "rb"), "application/pdf")}
                                headers = headers
                                response_pdf = requests.post(url_file,files=files, headers=headers)
                                os.remove(pdf_path)
                                self.check_pdf_data(response_pdf,attachment)
                    if response.json()['result'] == 'success':
                        if self.env.context.get('sale_id'):
                            current_id = self.env.context.get('sale_id')
                        elif self.env.context.get('purchase_id'):
                            current_id = self.env.context.get('purchase_id')
                        else:
                            current_id = self.env.context.get('invoice_id')
                        message_sent = self.env[self.model].search([('id','=',current_id)])
                        message_data_change = self.message.replace("\n", "<br/>")
                        message_sent.message_post(body=message_data_change)
                        self.env['message.history'].create({
                                    'message':self.message,
                                    'mobile':self.mobile,
                                    'status':'success'
                                })
                    else:
                        try:
                            error_msg=response.json()['message']
                        except:
                            error_msg=response.json()['info']
                        self.env['message.history'].create({
                                    'message':self.message,
                                    'mobile':self.mobile,
                                    'message_error':error_msg,
                                    'status':'error'
                                })

    def check_pdf_data(self,data,attachment):
        if data.json()['result'] == True:
            if self.env.context.get('sale_id'):
                current_id = self.env.context.get('sale_id')
            elif self.env.context.get('purchase_id'):
                current_id = self.env.context.get('purchase_id')
            else:
                current_id = self.env.context.get('invoice_id')
            message_sent = self.env[self.model].search([('id','=',current_id)])
            message_sent.message_post(attachment_ids=[attachment.id])
            self.env['message.history'].create({
                            'mobile':self.mobile,
                            'attachment_ids':attachment,
                            'message':'',
                            'status':'success'
                        })
        else:
            try:
                error_msg=data.json()['message']
            except:
                error_msg=data.json()['info']
            self.env['message.history'].create({
                            'mobile':self.mobile,
                            'attachment_ids':attachment,
                            'message':'',
                            'message_error':error_msg,
                            'status':'error'
                        })
