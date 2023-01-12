# -*- coding: utf-8 -*-

from odoo import models, fields,api,_
import requests
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    whats_app = fields.Boolean(string="Whats App" ,config_parameter='whatsapp_odoo.whats_app')
    token_key = fields.Char(string="Access Token",config_parameter='whatsapp_odoo.token_key')
    end_point = fields.Char(string="Api Endpoint",config_parameter='whatsapp_odoo.end_point')
    
    @api.constrains("token_key", "end_point")
    def _check_field(self):
        for auth in self:
            if auth.token_key and auth.end_point:
                headers = {"Authorization": auth.token_key}
                response = requests.get('https://'+auth.end_point+'/api/v1/getContacts', headers=headers)
                if response.text == '':
                    raise ValidationError(_("Please Enter Proper Access Token or End point"))
