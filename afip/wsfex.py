# Implements an interface to the "WSFEXV1" web service as described in:
# https://www.afip.gob.ar/ws/documentacion/manuales/WSFEX-Manualparaeldesarrollador_V1_6_0.pdf

import zeep.exceptions
from zeep.helpers import serialize_object
from .ws import WebServiceClient, WebServiceTool, WebServiceError
from .credentials import LoginTicket


class WSFEXClient(WebServiceClient):
    name = 'wsfex'
    wsdl_testing = 'https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL'
    wsdl_production = 'https://servicios1.afip.gov.ar/wsfexv1/service.asmx?WSDL'
    auth = None

    def __init__(self, credentials, zeep_cache=None, log_dir=None):
        super().__init__(credentials, zeep_cache, log_dir)
        auth_type = self.client.get_type('ns0:ClsFEXAuthRequest')
        self.auth = auth_type(Token=self.credentials.tickets['wsfex'].token,
                              Sign=self.credentials.tickets['wsfex'].signature,
                              Cuit=self.credentials.cuit)

    def check_errors(self, ret, error_key = 'FEXErr'):
        if error_key in ret and ret[error_key]['ErrCode'] != 0:
            raise WebServiceError(ret[error_key]['ErrCode'], ret[error_key]['ErrMsg'])

    def get_status(self):
        return serialize_object(self.client.service.FEXDummy())

    def get_country_cuits(self):
        ret = serialize_object(self.client.service.FEXGetPARAM_DST_CUIT(self.auth))
        self.check_errors(ret)
        countries = ret['FEXResultGet']['ClsFEXResponse_DST_cuit']
        return [(c['DST_CUIT'], c['DST_Ds']) for c in countries]


class WSFEXTool(WebServiceTool):
    name = 'wsfex'
    help = 'Facturación Electrónica - Factura de exportación'
    client = None

    def __init__(self, parser):
        super().__init__(parser)
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand', required=True)
        subparsers.add_parser('status', help='get service status')
        subparsers.add_parser('country_cuits', help='get country CUIT numbers')

    def handle(self, args):
        self.client = WSFEXClient(self.credentials, zeep_cache=self.zeep_cache, log_dir=self.log_dir)
        if args.subcommand == 'status':
            return self.status(args)
        if args.subcommand == 'country_cuits':
            return self.country_cuits(args)

    def status(self, args):
        for service, status in self.client.get_status().items():
            print(f'{service}: {status}')

    def country_cuits(self, args):
        print(self.client.get_country_cuits())
