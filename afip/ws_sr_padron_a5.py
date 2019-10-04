# Implements an interface to the "ws_sr_padron_a13" web service as described in:
# http://www.afip.gob.ar/ws/ws-padron-a13/manual-ws-sr-padron-a13-v1.2.pdf

import re
from collections import OrderedDict
from zeep.helpers import serialize_object
from .ws import WebServiceClient, WebServiceTool, WebServiceError


class WSSRPadronA5Client(WebServiceClient):
    name = 'ws_sr_padron_a5'
    wsdl_testing = 'https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA5?WSDL'
    wsdl_production = 'https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA5?WSDL'

    def get_status(self):
        return serialize_object(self.client.service.dummy())

    def _kill_camels(self, name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _normalize(self, data):
        ret = dict()
        for k, v in data.items():
            sk = self._kill_camels(k)
            if type(v) == OrderedDict:
                v = self._normalize(v)
            elif type(v) == list:
                nv = list()
                for e in v:
                    if type(e) == OrderedDict:
                        e = self._normalize(e)
                    nv.append(e)
                v = nv
            ret[sk] = v
        return ret

    # The response from this WS is pretty readable so it's sanitized into a normal dict with snake_cased
    # keys for consistency. They are left untranslated as I'm not sure about the universe of possible
    # key names.
    def query(self, cuit):
        ticket = self.credentials.tickets[self.name]
        ret = self.client.service.getPersona(token=ticket.token, sign=ticket.signature,
                                             cuitRepresentada=self.credentials.cuit, idPersona=cuit)
        return self._normalize(serialize_object(ret))


class WSSRPadronA5Tool(WebServiceTool):
    name = 'ws_sr_padron_a5'
    help = 'Consulta a Padrón Alcance 5'
    client_class = WSSRPadronA5Client

    def __init__(self, parser):
        super().__init__(parser)
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
        subparsers.add_parser('status', help='get service status')
        query = subparsers.add_parser('query', help='query information for a given CUIT')
        query.add_argument('cuit', help='CUIT number to query information about')

    def _kill_snakes(self, name):
        name = name.replace('_', ' ')
        return name[0].upper() + name[1:]

    def _dump(self, data, tabs=0):
        p = ' ' * tabs * 2
        for k, v in data.items():
            k = self._kill_snakes(k)
            if type(v) == dict:
                print(f'{p}{k}:')
                self._dump(v, tabs + 1)
            elif type(v) == list and len(v):
                print(f'{p}{k}:')
                for e in v:
                    if type(e) == dict:
                        print(f'{p}- {k}:')
                        self._dump(e, tabs + 2)
                    else:
                        print(f'{p}- {k}: {v}')
            else:
                print(f'{p}{k}: {v}')

    def status(self, args):
        for service, status in self.client.get_status().items():
            print(f'{service}: {status}')

    def query(self, args):
        self._dump(self.client.query(args.cuit))
