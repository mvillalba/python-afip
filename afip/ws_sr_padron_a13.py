# Implements an interface to the "ws_sr_padron_a13" web service as described in:
# http://www.afip.gob.ar/ws/ws-padron-a13/manual-ws-sr-padron-a13-v1.2.pdf

from zeep.helpers import serialize_object
from .ws import WebServiceClient, WebServiceTool, WebServiceError
from .ws_sr_padron_a5 import WSSRPadronA5Client, WSSRPadronA5Tool


class WSSRPadronA13Client(WSSRPadronA5Client):
    name = 'ws_sr_padron_a13'
    wsdl_testing = 'https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA13?WSDL'
    wsdl_production = 'hhttps://aws.afip.gov.ar/sr-padron/webservices/personaServiceA13?WSDL'
    # TODO


class WSSRPadronA13Tool(WSSRPadronA5Tool):
    name = 'ws_sr_padron_a13'
    help = 'Consulta a Padrón Alcance 13'
    client_class = WSSRPadronA5Client
    # TODO
