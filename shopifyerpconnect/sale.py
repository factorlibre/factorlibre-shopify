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

import time
from tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from tools.translate import _

from osv import osv

from base_external_referentials.decorator import only_for_referential

class sale_shop(osv.osv):
    _inherit = 'sale.shop'

    def import_orders(self, cr, uid, ids, context=None):
        self.import_resources(cr, uid, ids, 'sale.order', method='search_then_read', context=context)
        self.write(cr, uid, ids, {'import_orders_from_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return True

sale_shop()

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def play_sale_order_onchange(self, cr, uid, vals, defaults=None, context=None):
        ir_module_obj= self.pool.get('ir.module.module')

        if ir_module_obj.search(cr, uid, [
                            ['name', '=', 'account_fiscal_position_rule_sale'],
                            ['state', 'in', ['installed', 'to upgrade']],
                                                            ], context=context):
            vals = self.call_onchange(cr, uid, 'onchange_partner_id', vals, defaults, context=context)
            vals = self.call_onchange(cr, uid, 'onchange_address_id', vals, defaults, context=context)
        else:
            vals = self.call_onchange(cr, uid, 'onchange_partner_id', vals, defaults, context=context)

        if defaults.get('partner_shipping_id'):
            vals.update({'partner_shipping_id': defaults['partner_shipping_id']})
        if defaults.get('partner_invoice_id'):
            vals.update({'partner_invoice_id': defaults['partner_invoice_id']})

        return vals

    @only_for_referential('Shopify')
    def _get_import_step(self, cr, uid, external_session, context=None):
        return 20

    @only_for_referential('Shopify')
    def _get_sale_related_resources(self, cr, uid, external_session, resource, context=None):
        res = {}
        partner_pool = self.pool.get('res.partner')
        if resource.get('customer'):
            customer_id = resource['customer'].get('id')
            res['customer_id'] = customer_id
            resource.pop('customer')

        return res

    @only_for_referential('Shopify')
    def _create_onfly_address(self, cr, uid, external_session, data, defaults=None, 
            address_type='invoice', context=None):
        if defaults is None:
            defaults = {}
        local_defaults = dict(defaults)

        print 'vdsvsdvsdvsdv'
        print defaults

        address_pool = self.pool.get('res.partner.address')
        address_id = False
        if data.get('id'):
            address_id = address_pool.get_oeid(cr, uid, data['id'], external_session.referential_id.id,
                    context=context)
        else:
            #Check existing_address
            address_domain =  [
                ('street','=',data.get('address1')),
                ('street2','=',data.get('address2')),
                ('zip','=',data.get('zip')),
                ('city','=',data.get('city')),
                ('partner_id','=',defaults.get('partner_id'))
            ]
            address_ids = address_pool.search(cr, uid, address_domain)
            if address_ids:
                address_id = address_ids[0]
            else:
                address_res = address_pool._record_one_external_resource(cr, uid, external_session, 
                    data, defaults=defaults, context=None)
                address_id = address_res.get('write_id') or address_res.get('create_id')
        
        address_field = 'partner_%s_id' % address_type
        local_defaults[address_field] = address_id 
        print 'LOCALLLLLLLLLLLL'
        print local_defaults
        return local_defaults

    @only_for_referential('Shopify')
    def _transform_one_resource(self, cr, uid, external_session, convertion_type, resource, mapping, mapping_id, \
            mapping_line_filter_ids=None, parent_data=None, previous_result=None, defaults=None, context=None):
        
        resource.update(self._get_sale_related_resources(cr, uid, external_session, resource, context=context))

        partner_id = self.pool.get('res.partner').get_or_create_oeid(cr, uid, external_session, 
            resource.get('customer_id'), context=context)

        address_defaults = {'partner_id': partner_id}

        for line in mapping[mapping_id]['mapping_lines']:
            if line['name'] == 'billing_address' and resource.get('billing_address'):
                defaults = self._create_onfly_address(cr, uid, external_session, resource['billing_address'],
                    defaults=address_defaults, context=context)
                resource.pop('billing_address')

            if line['name'] == 'shipping_address' and resource.get('shipping_address'):
                defaults = self._create_onfly_address(cr, uid, external_session, resource['shipping_address'],
                    address_type='shipping', defaults=address_defaults, context=context)
                resource.pop('shipping_address')

        ######################################################################
        #Tax lines from shopify are defined in Sale Order, So its impossible to know
        #the tax that is used in a line
        #Now I use only the first tax line what maybe is a wrong approach in stores that use multiple taxes
        ######################################################################
        tax_rate = resource.get('tax_lines') and resource['tax_lines'][0] and resource['tax_lines'][0]['rate']
        if tax_rate is not False:
            for line in resource.get('line_items'):
                line['tax_rate'] = tax_rate

        if resource.get('shipping_lines'):
            for shipping in resource['shipping_lines']:
                shipping['tax_rate'] = tax_rate
            defaults.update({'shipping_lines': resource['shipping_lines']})

        if resource.get('discount_codes'):
            defaults.update({'discount_codes': resource['discount_codes']})

        if resource.get('gateway'):
            payment_method = {'name': resource['gateway']}
            payment_res = self.pool.get('payment.method')._record_one_external_resource(cr, uid, 
                external_session, payment_method, context=context)
            defaults.update({'payment_method_id': payment_res.get('write_id') or payment_res.get('create_id')})

        shop = False
        if external_session.sync_from_object._name == 'sale.shop':
            shop = external_session.sync_from_object
        elif context.get('sale_shop_id'):
            shop = self.pool.get('sale.shop').browse(cr, uid,  context['sale_shop_id'], context=context)
        defaults.update({'shop_id': shop and shop.id})
        defaults.update({'company_id': shop and shop.company_id and shop.company_id.id})

        return super(sale_order, self)._transform_one_resource(cr, uid, external_session, convertion_type, resource,\
                 mapping, mapping_id,  mapping_line_filter_ids=mapping_line_filter_ids, parent_data=parent_data,\
                 previous_result=previous_result, defaults=defaults, context=context)
    
    def _convert_special_fields(self, cr, uid, vals, referential_id, context=None):
        for shipping in vals.get('shipping_lines', []):
            vals['shipping_amount_tax_included'] = float(shipping['price'])
            vals['shipping_amount_tax_excluded'] = float(shipping['price'])
            vals['shipping_tax_rate'] = float(shipping['tax_rate'])
            del vals['shipping_lines']

        if vals.get('discount_codes'):
            vals['gift_certificates_amount'] = 0
            certificate_code = ""
            for discount in vals.get('discount_codes', []):
                vals['gift_certificates_amount'] += float(discount['amount'])
                certificate_code = "%s %s" % (certificate_code, discount['code'])
            vals['gift_certificates_code'] = certificate_code.strip()
            del vals['discount_codes']
        
        for option in self._get_special_fields(cr, uid, context=context):
            vals = self._add_order_extra_line(cr, uid, vals, option, context=context)
        return vals

    @only_for_referential('Shopify')
    def _get_payment_information(self, cr, uid, external_session, order_id, resource, context=None):
        vals = {}
        sale = self.browse(cr, uid, order_id, context=context)
        vals['payment_method'] = sale.payment_method_id.name
        vals['journal_id'] = sale.payment_method_id.journal_id and sale.payment_method_id.journal_id.id
        vals['date'] = sale.date_order
        if resource.get('financial_status') and resource['financial_status'] == 'paid':
            vals['paid'] = True
            vals['amount'] = float(resource.get('total_price', 0.0))
        return vals

    def _add_order_extra_line(self, cr, uid, vals, option, context):
        """ Add or substract amount on order as a separate line item with single quantity for each type of amounts like :
        shipping, cash on delivery, discount, gift certificates...

        :param dict vals: values of the sale order to create
        :param option: dictionnary of option for the special field to process
        """
        if context is None: context={}
        sign = option.get('sign', 1)
        if context.get('is_tax_included') and vals.get(option['price_unit_tax_included']):
            price_unit = vals.pop(option['price_unit_tax_included']) * sign
        elif vals.get(option['price_unit_tax_excluded']):
            price_unit = vals.pop(option['price_unit_tax_excluded']) * sign
        else:
            for key in ['price_unit_tax_excluded', 'price_unit_tax_included', 'tax_rate_field']:
                if option.get(key) and option[key] in vals:
                    del vals[option[key]]
            return vals #if there is not price, we have nothing to import

        model_data_obj = self.pool.get('ir.model.data')
        model, product_id = model_data_obj.get_object_reference(cr, uid, *option['product_ref'])
        product = self.pool.get('product.product').browse(cr, uid, product_id, context)

        extra_line = {
                        'product_id': product.id,
                        'name': product.name,
                        'product_uom': product.uom_id.id,
                        'product_uom_qty': 1,
                        'price_unit': price_unit,
                    }

        extra_line = self.pool.get('sale.order.line').play_sale_order_line_onchange(cr, uid, extra_line, vals, vals['order_line'], context=context)
        if context.get('use_external_tax') and option.get('tax_rate_field'):
            tax_rate = vals.pop(option['tax_rate_field'])
            if tax_rate:
                line_tax_id = self.pool.get('account.tax').get_tax_from_rate(cr, uid, tax_rate, context.get('is_tax_included'), context=context)
                if not line_tax_id:
                    raise except_osv(_('Error'), _('No tax id found for the rate %s with the tax include = %s')%(tax_rate, context.get('is_tax_included')))
                extra_line['tax_id'] = [(6, 0, [line_tax_id])]
            else:
                extra_line['tax_id'] = False
        if not option.get('tax_rate_field'):
            if extra_line.get('tax_id'):
                del extra_line['tax_id']
        ext_code_field = option.get('code_field')
        if ext_code_field and vals.get(ext_code_field):
            extra_line['name'] = "%s [%s]" % (extra_line['name'], vals[ext_code_field])
        vals['order_line'].append((0, 0, extra_line))
        return vals

    @only_for_referential('Shopify')
    def _get_filter(self, cr, uid, external_session, step, previous_filter=None, context=None):
        order_filter = super(sale_order, self)._get_filter(cr, uid, external_session, step, 
            previous_filter=previous_filter, context=context)
        
        shop = False
        if external_session.sync_from_object._name == 'sale.shop':
            shop = external_session.sync_from_object
        elif context.get('sale_shop_id'):
            shop = self.pool.get('sale.shop').browse(cr, uid,  context['sale_shop_id'], context=context)
        if shop and shop.import_orders_from_date:
            order_filter['updated_at_min'] = shop.import_orders_from_date
        return order_filter

sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _transform_one_resource(self, cr, uid, external_session, convertion_type, resource, mapping, mapping_id,
                    mapping_line_filter_ids=None, parent_data=None, previous_result=None, defaults=None, context=None):
        if context is None: context={}
        line = super(sale_order_line, self)._transform_one_resource(cr, uid, external_session, convertion_type, resource,
                            mapping, mapping_id, mapping_line_filter_ids=mapping_line_filter_ids, parent_data=parent_data,
                            previous_result=previous_result, defaults=defaults, context=context)

        if context.get('use_external_tax'):
            if resource.get('tax_rate'):
                line_tax_id = self.pool.get('account.tax').get_tax_from_rate(cr, uid, resource['tax_rate'], context.get('is_tax_included', False), context=context)
                if not line_tax_id:
                    raise osv.except_osv(_('Error'), _('No tax id found for the rate %s with the tax include = %s')%(resource['tax_rate'], context.get('is_tax_included')))
                line['tax_id'] = [(6, 0, [line_tax_id])]
            else:
                line['tax_id'] = False
        return line

sale_order_line()    