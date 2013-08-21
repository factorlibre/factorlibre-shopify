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

{
    'name': 'Shopify Connector',
    'version': '0.1',
    'category': 'E-commerce',
    'description': """Shopify Connector""",
    'author': 'Factor Libre',
    'maintainer': 'Factor Libre',
    'website': 'http://www.factorlibre.com',
    'depends': ['base', 'base_sale_multichannels', 'base_external_referentials'],
    'init_xml': [],
    'update_xml': [
        'settings/external.referential.type.csv',
        'settings/external.referential.version.csv',
        'settings/external.mapping.template.csv',
        'settings/external.mappinglines.template.csv',
        'shopify_view.xml',
        'sale_view.xml',
        'wizard/import_collection_products_view.xml'
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: