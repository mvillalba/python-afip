# Implements an interface to the "WSFEV1" web service as described in:
# https://www.afip.gob.ar/facturadecreditoelectronica/documentos/manual_desarrollador_COMPG.pdf

from zeep.helpers import serialize_object
from .ws import WebServiceClient, WebServiceTool, WebServiceError
from .utils import *


# TODO: move constructor and _invoke to parent?
# TODO: missing: FECAEASinMovimientoConsultar, FECAEARegInformativo, FECAEARegInformativo,
# TODO: FECAEASinMovimientoInformar, FECAEAConsultar, FECAEASolicitar, FECAESolicitar,
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

    def _check_errors(self, ret):
        if ret.get('Errors') is None or 'Err' not in ret['Errors']:
            return
        errors = ret['Errors']['Err']
        raise WebServiceError(errors[0]['Code'], errors[0]['Msg'])

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

    def get_invoice(self, pos, typ, number):
        cmp = dict(FeCompConsReq=dict(PtoVta=pos, CbteNro=number, CbteTipo=typ))
        # TODO: return an Invoice, but for now we don't know if fields are different and we don't want
        # TODO: to have 2 Invoice classes for the same god damn thing.
        return self._invoke('FECompConsultar', kwargs=cmp)

    def get_last_invoice_number(self, pos, typ):
        args = dict(PtoVta=pos, CbteTipo=typ)
        ret = self._invoke('FECompUltimoAutorizado', kwargs=args, result_key=None)
        return ret['CbteNro'], None  # Second param is a date on WSFEX, returned here as None for compatibility

    def get_currency_quote(self, identifier):
        ret = self._invoke('FEParamGetCotizacion', kwargs=dict(MonId=identifier))
        return parse_date(ret['FchCotiz']), ret['MonCotiz']

    def get_points_of_sale(self):
        ret = self._invoke('FEParamGetPtosVenta')
        if ret is None:
            return list()
        ret = ret['PtoVenta']
        return [(c['Nro'], c['EmisionTipo'], c['Bloqueado'] != 'N', parse_date(c['FchBaja'])) for c in ret]

    def get_currencies(self):
        ret = self._invoke('FEParamGetTiposMonedas')['Moneda']
        return [(c['Id'], c['Desc'], parse_date(c['FchDesde']), parse_date(c['FchHasta'])) for c in ret]

    def get_invoice_types(self):
        ret = self._invoke('FEParamGetTiposCbte')['CbteTipo']
        return [(c['Id'], c['Desc'], parse_date(c['FchDesde']), parse_date(c['FchHasta'])) for c in ret]

    def get_optional_data_types(self):
        ret = self._invoke('FEParamGetTiposOpcional')['OpcionalTipo']
        return [(c['Id'], c['Desc'], parse_date(c['FchDesde']), parse_date(c['FchHasta'])) for c in ret]

    def get_iva_types(self):
        ret = self._invoke('FEParamGetTiposIva')['IvaTipo']
        return [(c['Id'], c['Desc'], parse_date(c['FchDesde']), parse_date(c['FchHasta'])) for c in ret]

    def get_document_types(self):
        ret = self._invoke('FEParamGetTiposDoc')['DocTipo']
        return [(c['Id'], c['Desc'], parse_date(c['FchDesde']), parse_date(c['FchHasta'])) for c in ret]

    def get_sale_types(self):
        ret = self._invoke('FEParamGetTiposConcepto')['ConceptoTipo']
        return [(c['Id'], c['Desc'], parse_date(c['FchDesde']), parse_date(c['FchHasta'])) for c in ret]

    def get_tax_types(self):
        ret = self._invoke('FEParamGetTiposTributos')['TributoTipo']
        return [(c['Id'], c['Desc'], parse_date(c['FchDesde']), parse_date(c['FchHasta'])) for c in ret]


# TODO: maybe make this inherit from WSFEXTool as most methods are copies of each other?
class WSFETool(WebServiceTool):
    name = 'wsfe'
    help = 'Facturación Electrónica - RG 4291'
    client_class = WSFEClient

    def __init__(self, parser):
        super().__init__(parser)
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
        subparsers.add_parser('status', help='get service status')
        subparsers.add_parser('countries', help='get list of acceptable countries')
        invoice = subparsers.add_parser('invoice', help='get invoice details')
        invoice.add_argument('pos', help='point of sale identifier')
        invoice.add_argument('type', help='type of invoice')
        invoice.add_argument('number', help='invoice number (not ID)')
        last_invoice_number = subparsers.add_parser('last_invoice_number', help='get last invoice number (not ID)')
        last_invoice_number.add_argument('pos', help='point of sale identifier')
        last_invoice_number.add_argument('type', help='type of invoice')
        quote = subparsers.add_parser('quote', help='get quote for a given currency')
        quote.add_argument('currency', help='currency identifier')
        subparsers.add_parser('pos', help='get registered points of sale')
        subparsers.add_parser('currencies', help='get list of accepted foreign currencies')
        subparsers.add_parser('invoice_types', help='get list of valid invoice types')
        subparsers.add_parser('optional', help='get optional data types')

        subparsers.add_parser('iva', help='get list of valid IVA (VAT) types')
        subparsers.add_parser('documents', help='get list of valid document types')
        subparsers.add_parser('sale_types', help='get list of valid sale/operation types (i.e. good, services, both)')
        subparsers.add_parser('tax_types', help='get list of valid tax ("tributos") types')

    # NOTE: verbatim
    def status(self, args):
        for service, status in self.client.get_status().items():
            print(f'{service}: {status}')

    # NOTE: verbatim
    def countries(self, args):
        for identifier, name in self.client.get_countries():
            print(identifier, name)

    # NOTE: verbatim (soon!)
    def invoice(self, args):
        invoice = self.client.get_invoice(args.pos, args.type, args.number)
        from pprint import pprint; pprint(invoice)
        # TODO: real code from WSFEXTool analog method below, use once get_invoice returns an Invoice instance
        # l = None
        # for k, v in invoice.to_dict().items():
        #     if 'date' in k:
        #         v = parse_date(v)
        #     if type(v) == list and len(v):
        #         l = v
        #         v = ''
        #     print('{}: {}'.format(self.make_label(k), v))
        #     if l is not None:
        #         for i in l:
        #             print(' -', i)
        #         l = None

    # NOTE: verbatim
    def last_invoice_number(self, args):
        number, date = self.client.get_last_invoice_number(args.pos, args.type)
        print("Number:", number)
        print("Date:", date)

    # NOTE: verbatim
    def quote(self, args):
        date, quote = self.client.get_currency_quote(args.currency)
        print('{}: {} ARS'.format(date, quote))

    # NOTE: verbatim
    def pos(self, args):
        for identifier, etype, blocked, closed_on in self.client.get_points_of_sale():
            print(identifier, f'"{etype}"', blocked, closed_on)

    # NOTE: verbatim
    def currencies(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_currencies():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    # NOTE: verbatim
    def invoice_types(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_invoice_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    # NOTE: verbatim
    def optional(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_optional_data_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def iva(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_iva_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def documents(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_document_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def sale_types(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_sale_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def tax_types(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_tax_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))
