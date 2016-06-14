# Copyright (c) 2015 Cisco Systems, Inc.
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from requests import get, put, post, delete
import json
from gluonclient import exceptions as exc
from novaclient import client as nova_client


class GluonAPI(object):
    """Base class for all APIs to Gluon, dealing with comms fundamentals."""

    def __init__(self, svcurl):
        self._svcurl = svcurl

    def _make_url(self, x):
        return '%s%s' % (self._svcurl, x)

    def _get_port(self, id, backend=None):
        try:
            if backend is None:
                port = get(self._make_url('ports/%s' % id))
            else:
                port = get(self._make_url('backends/%s/ports/%s'
                                          % (backend, id)))
            return port
        except exc.GluonClientException as e:
            if e.status_code == 404:
                raise exc.PortNotFoundClient()
            raise

    def json_get(self, url):
        try:
            resp = get(url)
            if resp.status_code != 200:
                raise exc.GluonClientException('Bad return status %d'
                                               % resp.status_code,
                                               status_code=resp.status_code)
            try:
                rv = json.loads(resp.content)
                return rv
            except Exception as e:
                raise exc.MalformedResponseBody(reason="JSON unreadable: %s on %s"
                                                       % (e.message, resp.content))
        except exc.GluonClientException as e:
            if e.status_code == 404:
                raise exc.PortNotFoundClient()
            raise

    def _get_backend(self, name):
        return self.json_get(self._make_url('backends/%s'))

    def _list_ports(self, backend=None, owner=None, device=None):
        ret_port_list = []
        port_list = self.json_get(self._make_url('ports'))
        for port in port_list:
            add = True
            if owner is not None and port.get('device_owner', '') != owner:
                add = False
            elif device is not None and port.get('device_id', '') != device:
                add = False
            if add:
                ret_port_list.append(port)
        return ret_port_list
        # if backend is not None and owner is not None:
        #     raise ValueError("only one of owner and backend may be given")
        # if backend is not None:
        #     l = self.json_get(self._make_url('backends/%s/ports' % (backend)))
        # elif owner is not None and device is not None:
        #     l = self.json_get(self._make_url('services/%s/devices/%s/ports'
        #                                      % (owner, device)))
        # elif owner is not None:
        #     l = self.json_get(self._make_url('services/%s/ports' % (owner)))
        # else:
        #     l = self.json_get(self._make_url('ports'))
        # return l

    def _list_backends(self):
        return self.json_get(self._make_url('backends'))

    def _get_port(self, id, backend=None):
        if backend is None:
            return self.json_get(self._make_url('ports/%s' % id))
        else:
            return self.json_get(self._make_url('backends/%s/ports/%s'
                                                % (backend, id)))

    def _get_backend(self, name):
        return self.json_get(self._make_url('backends/%s' % name))


# TODO whole bunch of duplication here, fix with superclasses

# TODO should be santising the results - our job to make sure we're
# ubercompatible and insulate callers from the over the wire JSON
class ClientAPI(GluonAPI):
    """Class for CLI clients that are used for diagnostic purposes.

    Generally a bunch of view commands."""

    def __init__(self, svcurl):
        super(ClientAPI, self).__init__(svcurl)

    def list_ports(self, backend=None, owner=None, device=None):
        return self._list_ports(backend=backend, owner=owner, device=device)

    def list_all_ports(self):
        return self._list_ports()

    def list_backends(self):
        return self._list_backends()

    def port(self, id):
        return self._get_port(id)

    def backend(self, name):
        return self._get_backend(name)

    def is_unbound(self, id):
        port = self._get_port(id)
        val = port.get('device_owner', '')
        return val is None or val == ''


VIF_UNPLUGGED = 'network-vif-unplugged'
VIF_PLUGGED = 'network-vif-plugged'
VIF_DELETED = 'network-vif-deleted'


# TODO error management
class NetworkServiceAPI(GluonAPI):
    """API for network services such as Neutron to use
    when talking to Gluon."""

    def __init__(self, svcurl, name, url):
        super(NetworkServiceAPI, self).__init__(svcurl)
        self._name = name
        self._url = url
        self._registered = False
        self._register()

    # TODO Retries, because Gluon may not be up when the network
    # service comes up.  Right now we register overenthusiastically.
    def _register(self):
        resp = post(self._make_url('backends'),
                    data={'name': self._name,
                          'service_type': self._name,
                          'url': self._url})
        if (resp.status_code == 201):
            self._registered = True

    def notify_create(self, id):
        self._register()
        post(self._make_url('backends/%s/ports' % self._name), data={'id': id})

    # TODO ignore already created errors.

    def notify_delete(self, id):
        self._register()
        delete(self._make_url('backends/%s/ports/%s' % (self._name, id)))

    # TODO ignore not found errors.


    def notify_event(self, device_id, port_id, event):
        self._register()
        put(self._make_url('ports/%s/notify' % (id)), {
            'device_id': device_id,
            'event': event})


class ComputeServiceAPI(GluonAPI):
    """ API for compute services such as Nova to use when talking to Gluon."""

    def __init__(self, svcurl, name):
        super(ComputeServiceAPI, self).__init__(svcurl)
        self._name = name

    def bind(self, id, zone, device_id, host,
             pci_profile=None, rxtx_factor=None):
        # TODO not fantastic we're using binding_profile unadulterated
        # from Neutron, but hey.

        data = {
            'device_owner': self._name,
            'zone': zone,
            'device_id': device_id,
            'host_id': host
        }
        profile = {}
        # TODO validate pci_profile
        if pci_profile is not None:
            profile['pci_profile'] = pci_profile

        if rxtx_factor is not None:
            profile['rxtx_factor'] = rxtx_factor
        if len(profile) > 0:
            data["profile"] = json.dumps(profile)
        put(self._make_url('ports/%s/bind' % id), json=data)

    def unbind(self, id):
        data = {}
        put(self._make_url('ports/%s/unbind' % id), json=data)

    def is_unbound(self, id):
        port = self._get_port(id)
        return port.get('device_owner', '') == ''

    def get_vnic_details(self, id):
        port = self.get_port(id)
        # Yes, changing the name from the over the wire name is a bit petty,
        # I'm just trying to track the dependencies a bit better
        # .. Should be using VNIC_TYPE_NORMAL as output, converted from the
        # protocol's own value
        return port.get('vnic_type', 'normal'), \
               {'physnet': port.get('provider:physical_network','')}

    def ports_by_device(self, id):
        # TODO: IJW: should return a list of ports owned by this
        # device in this service
        return []

    def get_port(self, id):
        # TODO Should sanitise
        return self._get_port(id)

    def list_ports(self, backend=None, owner=None, device=None):
        return self._list_ports(backend, owner, device)

    def port(self, id):
        return self._get_port(id)
