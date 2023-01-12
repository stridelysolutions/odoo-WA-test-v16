# -*- coding: utf-8 -*-

from odoo import models,api,fields
import requests,os,io
from odoo.exceptions import ValidationError
from collections import defaultdict
from odoo.modules.module import get_module_resource
try:
    import base64,PyPDF2
except ImportError as e:
    os.system("pip3 install base64")
    os.system("pip3 install PyPDF2")


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    attachment_ids = fields.Many2many(
        string='Attach A File',
        comodel_name='ir.attachment',
    )
    
    def send_whatsapp_message(self):
        whats_app = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.whats_app')
        token = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.token_key')
        end_point = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.end_point')
        if whats_app:
            if not end_point or not token:
                raise ValidationError("Please enter End Point or Token")
            else:
                if self.partner_id.whatsapp_no:
                    message_data = ''
                    if self.picking_type_id.name == 'Returns':
                        message_data = message_data+"Hi" + " " + self.partner_id.name + ',' + '\n\n' + "Your Delevery has been " +self.origin
                    else:
                        message_data = message_data+"Hi" + " " + self.partner_id.name + ',' + '\n\n' + "We are glad to inform you that your order n°"+ self.origin +" has been shipped."
                    url = "https://"+end_point+"/api/v1/sendSessionMessage/"+str(self.partner_id.whatsapp_no)+"?messageText="+message_data
                    headers = {"Authorization": token}
                    response = requests.post(url, headers=headers)
                    if response.json()['result'] == 'success':
                        message_data_change = message_data.replace("\n", "<br/>")
                        self.message_post(body=message_data_change)
                        self.env['message.history'].create({
                            'message':message_data,
                            'mobile':self.partner_id.whatsapp_no,
                            'status':'success'
                        })
                    else:
                        try:
                            error_msg=response.json()['message']
                        except:
                            error_msg=response.json()['info']
                        self.env['message.history'].create({
                            'message':message_data,
                            'mobile':self.partner_id.whatsapp_no,
                            'message_error':error_msg,
                            'status':'error'
                        })
                    template_selection=self.env.ref('stock.mail_template_data_delivery_confirmation').id
                    search_mail_template = self.env['mail.template'].search([('id','=',template_selection)])
                    values = self.env['mail.compose.message'].generate_email_for_composer(
                        search_mail_template.id, [self.id],
                        ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc',  'reply_to', 'attachment_ids', 'mail_server_id']
                    )[self.id]
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
                    writer = PyPDF2.PdfFileWriter()
                    reader = PyPDF2.PdfFileReader(io.BytesIO(base64.b64decode(self.attachment_ids.datas)), strict=False, overwriteWarnings=False)
                    writer.addPage(reader.getPage(0))
                    pdf_path = get_module_resource('whatsapp_odoo', 'static', 'template.html')
                    pdf_path = pdf_path.replace('template.html','') + self.origin+".pdf"
                    output = open(pdf_path,'wb')
                    writer.write(output)
                    output.close()
                    if self.attachment_ids:
                        pdf_path = get_module_resource('whatsapp_odoo', 'static', self.origin+".pdf")
                        url_file = "https://"+end_point+"/api/v1/sendSessionFile/"+str(self.partner_id.whatsapp_no)
                        files = {"file": (self.origin+".pdf", open(pdf_path, "rb"), "application/pdf")}
                        headers = headers
                        response_pdf = requests.post(url_file,files=files, headers=headers)
                        self.check_pdf_data(response_pdf)
                        os.remove(pdf_path)
    
    def check_pdf_data(self,data):
        if data.json()['result'] == True:
            self.message_post(attachment_ids=self.attachment_ids.ids)
            self.env['message.history'].create({
                            'mobile':self.partner_id.whatsapp_no,
                            'attachment_ids':self.attachment_ids,
                            'message':'',
                            'status':'success'
                        })
        else:
            try:
                error_msg=data.json()['message']
            except:
                error_msg=data.json()['info']
            self.env['message.history'].create({
                            'mobile':self.partner_id.whatsapp_no,
                            'attachment_ids':self.attachment_ids,
                            'message':'',
                            'message_error':error_msg,
                            'status':'error'
                        })
                            

    @api.depends('move_type', 'immediate_transfer', 'move_ids.state', 'move_ids.picking_id')
    def _compute_state(self):
        picking_moves_state_map = defaultdict(dict)
        picking_move_lines = defaultdict(set)
        for move in self.env['stock.move'].search([('picking_id', 'in', self.ids)]):
            picking_id = move.picking_id
            move_state = move.state
            picking_moves_state_map[picking_id.id].update({
                'any_draft': picking_moves_state_map[picking_id.id].get('any_draft', False) or move_state == 'draft',
                'all_cancel': picking_moves_state_map[picking_id.id].get('all_cancel', True) and move_state == 'cancel',
                'all_cancel_done': picking_moves_state_map[picking_id.id].get('all_cancel_done', True) and move_state in ('cancel', 'done'),
                'all_done_are_scrapped': picking_moves_state_map[picking_id.id].get('all_done_are_scrapped', True) and (move.scrapped if move_state == 'done' else True),
                'any_cancel_and_not_scrapped': picking_moves_state_map[picking_id.id].get('any_cancel_and_not_scrapped', False) or (move_state == 'cancel' and not move.scrapped),
            })
            picking_move_lines[picking_id.id].add(move.id)
        for picking in self:
            picking_id = (picking.ids and picking.ids[0]) or picking.id
            if not picking_moves_state_map[picking_id]:
                picking.state = 'draft'
            elif picking_moves_state_map[picking_id]['any_draft']:
                picking.state = 'draft'
            elif picking_moves_state_map[picking_id]['all_cancel']:
                picking.state = 'cancel'
            elif picking_moves_state_map[picking_id]['all_cancel_done']:
                if picking_moves_state_map[picking_id]['all_done_are_scrapped'] and picking_moves_state_map[picking_id]['any_cancel_and_not_scrapped']:
                    picking.state = 'cancel'
                else:
                    picking.state = 'done'
                    if picking.state == 'done':
                            picking.send_whatsapp_message()
            else:
                relevant_move_state = self.env['stock.move'].browse(picking_move_lines[picking_id])._get_relevant_state_among_moves()
                if picking.immediate_transfer and relevant_move_state not in ('draft', 'cancel', 'done'):
                    picking.state = 'assigned'
                elif relevant_move_state == 'partially_available':
                    picking.state = 'assigned'
                else:
                    picking.state = relevant_move_state
