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

from osv import osv

from base_external_referentials.decorator import only_for_referential

class external_referential(osv.osv):
    _inherit = 'external.referential'

    @only_for_referential('Shopify')
    def import_products(self, cr, uid, ids, context=None):
        ctx = dict(context)
        ctx.update({'filter_params': {'published_status': 'published'}})
        self.import_resources(cr, uid, ids, 'product.template', method='search_then_read', context=ctx)
        return True

external_referential()