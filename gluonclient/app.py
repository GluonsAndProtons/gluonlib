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

import argparse
import sys
import gluonclient.api
import gluonclient.exceptions as exc
import pprint

# TODO should be a keystone lookup or an env var
client=gluonclient.api.ClientAPI('http://0:2704/')



parser = argparse.ArgumentParser( \
    description='Connect to a Gluon server and retrieve information.')

subparsers = parser.add_subparsers(help='sub-command help')

def show_port(args):
    result = client.port(args.port_id)
    pprint.pprint(result)

sp = subparsers.add_parser('port-show', help='Show the details of one port.')
sp.add_argument('port_id', metavar='port-id', help='The UUID of the port.')
sp.set_defaults(function=show_port)


def is_unbound(args):
    result = client.is_unbound(args.port_id)
    pprint.pprint(result)

sp = subparsers.add_parser('port-unbound', 
                           help='Show if a port is not bound to a VM.')
sp.add_argument('port_id', metavar='port-id', help='The UUID of the port.')
sp.set_defaults(function=is_unbound)


def list_ports(args):
    result = client.list_ports(backend=args.backend, owner=args.owner)
    pprint.pprint(result)

sp = subparsers.add_parser('port-list', 
    help='List all the ports in the system or for one backend.')
sp.add_argument('--backend', help='The name of the backend.')
sp.add_argument('--owner', help='The name of the owner (for bound ports).')
sp.set_defaults(function=list_ports)
    

def show_backend(args):
    result = client.backend(args.backend)
    pprint.pprint(result)

sp = subparsers.add_parser('backend-show', 
                           help='Show the details of a backend.')
sp.add_argument('backend', help='The name of the backend.')
sp.set_defaults(function=show_backend)
    

def list_backends(args):
    result = client.list_backends()
    pprint.pprint(result)

sp = subparsers.add_parser('backend-list', 
    help='List all the backends registered with the system.')
sp.set_defaults(function=list_backends)
    

def main():
    args = parser.parse_args()
    try:
	args.function(args)
	sys.exit(0)
    except exc.GluonClientException as e:
	print e
	print 'Gluon request failed: %s ' % str(e)
	sys.exit(1)

if __name__ == '__main__':
    main()

