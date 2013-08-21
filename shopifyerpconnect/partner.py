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

class res_partner(osv.osv):
    _inherit = 'res.partner'

    @only_for_referential('Shopify')
    def _record_one_external_resource(self, cr, uid, external_session, resource, defaults=None,
            mapping=None, mapping_id=None, context=None):

        res = super(res_partner, self)._record_one_external_resource(cr, uid, external_session, resource,
            defaults=defaults, mapping=mapping, mapping_id=mapping_id, context=context)

        address_defaults = {
            'email': resource.get('email'),
            'partner_id': res.get('write_id') or res.get('create_id')
        }

        for address_data in resource.get('addresses', []):
            addr_res = self.pool.get('res.partner.address')._record_one_external_resource(cr, uid, 
                external_session, address_data, defaults=address_defaults, context=context)
            
        return res

res_partner()