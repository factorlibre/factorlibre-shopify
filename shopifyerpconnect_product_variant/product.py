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

from base_external_referentials.decorator import only_for_referential

class product_template(osv.osv):
    _inherit = 'product.template'

    @only_for_referential('Shopify')
    def _record_one_external_resource(self, cr, uid, external_session, resource, defaults=None,
            mapping=None, mapping_id=None, context=None):

        #dimension_types is {position: erp_dimension_id}
        dimension_types = {}
        for option in resource.get('options', []):
            dimension_res = self.pool.get('product.variant.dimension.type')._record_one_external_resource(cr, 
                uid, external_session, option, context=context)
            dimension_types[option['position']] = dimension_res.get('write_id') or dimension_res.get('create_id')

        if dimension_types:
            defaults.update({'dimension_type_ids': [(6,0, dimension_types.values())]})

        res = super(product_template, self)._record_one_external_resource(cr, uid, external_session, resource,
            defaults=defaults, mapping=mapping, mapping_id=mapping_id, context=context)

        variant_defaults = {
            'product_tmpl_id': res.get('write_id') or res.get('create_id'),
            'name': resource.get('title'),
        }

        for variant in resource.get('variants', []):
            variant_defaults.update({'dimension_types': dimension_types})
            addr_res = self.pool.get('product.product')._record_one_external_resource(cr, uid, 
                external_session, variant, defaults=variant_defaults, context=context)
            
        return res

product_template()

class product_product(osv.osv):
    _inherit = 'product.product'

    @only_for_referential('Shopify')
    def _record_one_external_resource(self, cr, uid, external_session, resource, defaults=None,
            mapping=None, mapping_id=None, context=None):
        variant_option_pool = self.pool.get('product.variant.dimension.option')
        variant_value_pool = self.pool.get('product.variant.dimension.value')

        product_variant_values = []

        if defaults.get('dimension_types'):
            dimension_types = dict(defaults['dimension_types'])
            del defaults['dimension_types']
            for option_position in dimension_types.keys():
                v_option = resource.get("option%s" % option_position)
                if v_option:
                    opt_ids = variant_option_pool.search(cr, uid, [
                        ('dimension_id','=',dimension_types[option_position]),
                        ('name','=',v_option)
                    ])
                    if not opt_ids:
                        opt_id = variant_option_pool.create(cr, uid, 
                            {
                                'dimension_id': dimension_types[option_position],
                                'name': v_option,
                                'code': v_option[0:12]
                            }
                        )
                    else:
                        opt_id = opt_ids[0] 


                    #dimension_values
                    v_value_ids = variant_value_pool.search(cr, uid, [
                        ('product_tmpl_id','=',defaults['product_tmpl_id']),
                        ('dimension_id','=',dimension_types[option_position]),
                        ('option_id', '=', opt_id)
                    ])
                    if v_value_ids:
                        product_variant_values.append(v_value_ids[0])
                    else:
                        v_value_id = variant_value_pool.create(cr, uid, {
                            'product_tmpl_id': defaults['product_tmpl_id'],
                            'dimension_id': dimension_types[option_position],
                            'option_id': opt_id
                        })
                        product_variant_values.append(v_value_id)

        defaults.update({'dimension_value_ids': [(6,0, product_variant_values)]})

        res = super(product_product, self)._record_one_external_resource(cr, uid, external_session, resource,
            defaults=defaults, mapping=mapping, mapping_id=mapping_id, context=context)

        return res                

product_product()