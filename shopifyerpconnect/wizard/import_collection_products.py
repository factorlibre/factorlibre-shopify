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

from osv import osv, fields

class import_collection_products(osv.osv_memory):
    _name = 'import.collection.products'

    _columns = {
        'referential_id': fields.many2one('external.referential', 'Ext. Ref', required=True),
        'product_category_ids': fields.many2many('product.category', 'category_import_rel', 
            'import_id', 'category_id', 'Categories')
    }

    def import_products(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        category_pool = self.pool.get('product.category')
        external_referential_pool = self.pool.get('external.referential')

        for obj in self.browse(cr, uid, ids, context=context):
            ctx = dict(context)
            for categ in obj.product_category_ids:
                extid = category_pool.get_extid(cr, uid, categ.id, obj.referential_id.id, context=context)
                if not extid:
                    continue
                ctx.update({'filter_params': {'collection_id': extid}, 'default_values': {'categ_id': categ.id}})
                external_referential_pool.import_resources(cr, uid, [obj.referential_id.id], 'product.product', method='search_then_read', context=ctx)


        return {'type': 'ir.actions.act_window_close'}

import_collection_products()