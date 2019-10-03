# Implements an interface to the "ws_sr_padron_a5" web service as described in:
# http://www.afip.gob.ar/ws/ws_sr_padron_a5/manual_ws_sr_padron_a5_v1.0.pdf

from zeep.helpers import serialize_object
from .ws import WebServiceClient, WebServiceTool, WebServiceError


class WSSRPadronA5Client(WebServiceClient):
    name = 'ws_sr_padron_a5'
    wsdl_testing = 'https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA5?WSDL'
    wsdl_production = 'https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA5?WSDL'

    def get_status(self):
        return serialize_object(self.client.service.dummy())

    def query(self, cuit):
        ticket = self.credentials.tickets[self.name]
        ret = self.client.service.getPersona(token=ticket.token, sign=ticket.signature,
                                             cuitRepresentada=self.credentials.cuit, idPersona=cuit)
        # TODO: process return data
        return serialize_object(ret)


class WSSRPadronA5Tool(WebServiceTool):
    name = 'ws_sr_padron_a5'
    help = 'Consulta a Padrón Alcance 5'
    client_class = WSSRPadronA5Client

    def __init__(self, parser):
        super().__init__(parser)
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand', required=True)
        subparsers.add_parser('status', help='get service status')
        query = subparsers.add_parser('query', help='query information for a given CUIT')
        query.add_argument('cuit', help='CUIT number to query information about')

    def status(self, args):
        for service, status in self.client.get_status().items():
            print(f'{service}: {status}')

    def query(self, args):
        from pprint import pprint; pprint(self.client.query(args.cuit))  # TODO
