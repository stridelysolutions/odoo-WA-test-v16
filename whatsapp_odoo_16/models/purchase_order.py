from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    whats_app = fields.Boolean(
        string='Whats App',
    )

    def action_send_whatsapp(self):
        compose_form_id = self.env.ref('whatsapp_odoo.whatsapp_message_wizard_form').id
        ctx = dict(self.env.context)
        message = "Hi" + " " + self.partner_id.name + ',' + '\n\n' + "Here is in attachment a purchase order" + ' ' + self.name + ' ' + "amounting" + ' ' + str(
            self.amount_total) + self.currency_id.symbol + ' from '+self.company_id.name + ".\n\n"+"The receipt is expected for "+str(self.date_planned.date())+".\n\n"+"Could you please acknowledge the receipt of this order?"
        template = self.env.ref('purchase.email_template_edi_purchase_done')
        ctx.update({
            'default_message': message,
            'default_partner_id': self.partner_id.id,
            'default_mobile': self.partner_id.whatsapp_no,
            'default_image_1920': self.partner_id.image_1920,
            'default_template_id': template.id if template else None,
            'default_model': 'purchase.order',
            'purchase_id':self.id
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

    @api.depends('whats_app')
    def whatsapp_status(self):
        for status in self:
            whats_app = self.env['ir.config_parameter'].sudo().get_param('whatsapp_odoo.whats_app')
            status.whats_app = whats_app