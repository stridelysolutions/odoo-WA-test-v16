# -*- coding: utf-8 -*-

from ast import Return
from urllib3 import Retry
from odoo import http
from odoo.http import request

import werkzeug.urls
import werkzeug.utils
import werkzeug.wrappers
import requests


class WhatsappMsg(http.Controller):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
    @http.route('/message',auth='public',csrf=False,type='json')
    def index(self, **kw):
        data = request.httprequest.data
