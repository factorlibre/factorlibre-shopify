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
from tools.translate import _
from base_external_referentials.external_osv import ExternalSession

class shopify_stock_import(osv.osv_memory):
    _name = 'shopify.stock.import'

    _columns = {
        'product_ids': fields.many2many('product.product', 'stock_import_product_rel', 'import_id', 'product_id', 'Products')
    }

    def import_product_stocks(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        product_pool = self.pool.get('product.product')
        inventory_pool = self.pool.get('stock.inventory')
        inventory_line_pool = self.pool.get('stock.inventory.line')
        location_pool = self.pool.get('stock.location')        

        wiz = self.browse(cr, uid, ids[0], context=context)
        shop = self.pool.get('sale.shop').browse(cr, uid, context.get('active_id'), context=context)
        external_session = ExternalSession(shop.referential_id, shop)

        inv_id = inventory_pool.create(cr, uid, {'name': 'Shopify Inventory'})

        for product in wiz.product_ids:
            prod_extid = product_pool.get_extid(cr, uid, product.id, external_session.referential_id.id, context=context)
            if not prod_extid:
                continue
            product_data = product_pool._get_external_resources(cr, uid, external_session, prod_extid, resource_filter={'fields': 'inventory_quantity'}, context=context)

            if product_data.get('inventory_quantity'):
                line_val = {
                    'product_id': product.id,
                    'location_id': shop.warehouse_id.lot_stock_id.id,
                    'company_id': shop.company_id.id,
                    'product_qty': float(product_data['inventory_quantity']),
                    'product_uom': product.uom_id.id,
                    'inventory_id': inv_id
                }
                inventory_line_pool.create(cr, uid, line_val, context=context)
        return {'type': 'ir.actions.act_window_close'}

shopify_stock_import()