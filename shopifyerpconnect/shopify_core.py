# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Factor Libre.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

from tools.translate import _

from openerp.osv.orm import Model
from openerp.osv.osv import except_osv

from .shopify_osv import Connection

from base_external_referentials.decorator import only_for_referential
from base_external_referentials.external_referentials import REF_VISIBLE_FIELDS

import time

REF_VISIBLE_FIELDS['Shopify'] = ['location', 'apiusername', 'apipass']

_logger = logging.getLogger(__name__)

class external_referential(Model):
    _inherit = "external.referential"

    @only_for_referential('Shopify')
    def external_connection(self, cr, uid, id, debug=False, logger=False, context=None):
        if isinstance(id, list):
            id=id[0]
        referential = self.browse(cr, uid, id, context=context)
        attr_conn = Connection(referential.location, referential.apiusername, referential.apipass, debug, logger)
        return attr_conn or False

    @only_for_referential('Shopify')
    def import_referentials(self, cr, uid, ids, context=None):
        self.import_resources(cr, uid, ids, 'sale.shop', method='search_read_no_loop', context=context)
        return True

    @only_for_referential('Shopify')
    def import_categories(self, cr, uid, ids, context=None):
        ctx = dict(context)
        ctx.update({'filter_params': {'published_status': 'published'}})
        self.import_resources(cr, uid, ids, 'product.category', method='search_then_read', context=ctx)
        return True

    @only_for_referential('Shopify')
    def import_products(self, cr, uid, ids, context=None):
        ctx = dict(context)
        ctx.update({'filter_params': {'published_status': 'published'}})
        self.import_resources(cr, uid, ids, 'product.product', method='search_then_read', context=ctx)
        return True

    @only_for_referential('Shopify')
    def import_customers(self, cr, uid, ids, context=None):
        self.import_resources(cr, uid, ids, 'res.partner', method='search_then_read', context=context)
        return True

external_referential()