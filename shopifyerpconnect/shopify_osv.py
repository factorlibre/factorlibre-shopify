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
import requests

from tools.translate import _
from openerp.osv.orm import Model
from openerp.osv.osv import except_osv
from base_external_referentials.decorator import only_for_referential
from base_external_referentials.external_osv import override, extend, ExternalSession

import logging
_logger = logging.getLogger(__name__)

#Model._shopify_get_external_resources = Model._get_external_resources

@only_for_referential('Shopify')
def _get_external_resource_ids(self, cr, uid, external_session, resource_filter=None, \
        mapping=None, mapping_id=None, context=None):
    mapping, mapping_id = self._init_mapping(cr, uid, external_session.referential_id.id, mapping=mapping, mapping_id=mapping_id, context=context)
    ext_resource = mapping[mapping_id]['external_resource_name']
    list_method = mapping[mapping_id]['external_list_method']
    get_method = mapping[mapping_id]['external_get_method']

    id_field = mapping[mapping_id]['key_for_external_id']

    if not list_method:
        if not get_method:
            raise except_osv(_('User Error'), _('There is not list method for the mapping %s')%(mapping[mapping_id]['model'],))
        else:
            #Return [None] because in shopify are models with only one record. List Method is not defined in mapping
            return [None]

    params = {'fields': 'id'}
    if resource_filter:
        params.update(resource_filter)

    res = external_session.connection.call(list_method, params=resource_filter)
    ids = []
    if res.get(list_method):
        ids = map(lambda obj: obj.get(id_field), res[list_method])
    return ids

Model._get_external_resource_ids = _get_external_resource_ids

@only_for_referential('Shopify')
def _get_external_resources(self, cr, uid, external_session, external_id=None, resource_filter=None, \
        mapping=None, mapping_id=None, fields=None, context=None):
    
    mapping, mapping_id = self._init_mapping(cr, uid, external_session.referential_id.id, mapping=mapping, mapping_id=mapping_id, context=context)
    ext_resource = mapping[mapping_id]['external_resource_name']
    read_method = mapping[mapping_id]['external_get_method']

    params = {}

    if not read_method:
        raise except_osv(_('User Error'),
            _('There is no "Get Method" configured on the mapping %s') %
            mapping[mapping_id]['model'])

    if external_id:
        res = external_session.connection.call('%s/%s' % (read_method, external_id))
    else:
        if resource_filter:
            params.update(resource_filter)
        res = external_session.connection.call(read_method, params=params)
    
    if res.get(ext_resource):
        res = res[ext_resource]
    return res

Model._get_external_resources = _get_external_resources

@only_for_referential('Shopify')
def _get_filter(self, cr, uid, external_session, step, previous_filter=None, context=None):
    if context is None:
        context = {}

    filter_params = {'limit': step}

    if context.get('filter_params'):
        filter_params.update(context['filter_params'])

    if previous_filter:
        filter_params.update(previous_filter)
    filter_params.update({'page': filter_params.get('page', 0) + 1})
    return filter_params

Model._get_filter = _get_filter

@only_for_referential('Shopify')
def _get_default_import_values(self, cr, uid, external_session, mapping_id=None, defaults=None, context=None):
    if defaults is None:
        defaults = {}
    if context is None:
        context = {}

    if context.get('default_values'):
        defaults.update(context['default_values'])
    return defaults

Model._get_default_import_values = _get_default_import_values

class Connection(object):
    def __init__(self, location, apikey, password, debug=False, logger=None):
        self.corelocation = location
        self.location = "%s/admin" % location
        self.apikey = apikey
        self.password = password
        self.debug = debug
        self.logger = logger or _logger

    def call(self, resource, method='GET', params=None):
        url = "%s/%s.json" % (self.location, resource)
        if params is None:
            params = {}
        for sleep_time in [1, 3, 6]:
            try:
                if self.debug:
                    self.logger.info(_("Calling URL: %s Method:%s") % (url, method))
                res = requests.request(method, url, auth=(self.apikey, self.password), params=params)
                res.raise_for_status()
                return res.json()
            except requests.exceptions.RequestException, e:
                self.logger.error(_("Calling URL: %s Method:%s, Error: %s") % (url, method, e))
                self.logger.warning(_("Webservice Failure, sleeping %s second before next attempt") % (sleep_time))
                time.sleep(sleep_time)
        raise

