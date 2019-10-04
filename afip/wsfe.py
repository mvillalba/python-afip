# Implements an interface to the "WSFEV1" web service as described in:
# https://www.afip.gob.ar/facturadecreditoelectronica/documentos/manual_desarrollador_COMPG.pdf

from zeep.helpers import serialize_object
from .ws import WebServiceClient, WebServiceTool, WebServiceError


# TODO: move constructor, _check_errors, and _invoke to parent?
class WSFEClient(WebServiceClient):
    name = 'wsfe'
    wsdl_testing = 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
    wsdl_production = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    auth = None

    def __init__(self, credentials, zeep_cache=None, log_dir=None):
        super().__init__(credentials, zeep_cache, log_dir)
        auth_type = self.client.get_type('ns0:FEAuthRequest')
        self.auth = auth_type(Token=self.credentials.tickets['wsfe'].token,
                              Sign=self.credentials.tickets['wsfe'].signature,
                              Cuit=self.credentials.cuit)

    def _check_errors(self, ret, error_key='FEErr'):
        if error_key in ret and ret[error_key]['ErrCode'] != 0:
            raise WebServiceError(ret[error_key]['ErrCode'], ret[error_key]['ErrMsg'])

    def _invoke(self, endpoint, args=None, kwargs=None, auth=True, result_key='ResultGet'):
        args = list() if args is None else args
        args = ([self.auth] + args) if auth else args
        kwargs = dict() if kwargs is None else kwargs
        ret = getattr(self.client.service, endpoint)(*args, **kwargs)
        ret = serialize_object(ret)
        self._check_errors(ret)
        if result_key is None:
            return ret
        return ret[result_key]

    def get_status(self):
        return self._invoke('FEDummy', auth=False, result_key=None)

    def get_countries(self):
        ret = self._invoke('FEParamGetTiposPaises')['PaisTipo']
        return [(c['Id'], c['Desc']) for c in ret]


class WSFETool(WebServiceTool):
    name = 'wsfe'
    help = 'Facturación Electrónica - RG 4291'
    client_class = WSFEClient

    def __init__(self, parser):
        super().__init__(parser)
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
        subparsers.add_parser('status', help='get service status')
        subparsers.add_parser('countries', help='get list of acceptable countries')

    def status(self, args):
        for service, status in self.client.get_status().items():
            print(f'{service}: {status}')

    def countries(self, args):
        for identifier, name in self.client.get_countries():
            print(identifier, name)
