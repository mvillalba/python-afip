# Implements an interface to the "WSFEXV1" web service as described in:
# https://www.afip.gob.ar/ws/documentacion/manuales/WSFEX-Manualparaeldesarrollador_V1_6_0.pdf

import json
import time
from zeep.helpers import serialize_object
from .ws import WebServiceClient, WebServiceTool, WebServiceError
from .utils import *


class Invoice:
    id = None
    date = None
    invoice_type = None
    pos = None
    number = None
    export_type = None
    existing_permit = None
    destination = None
    client_name = None
    client_country_cuit = None
    client_address = None
    client_tax_id = None
    currency_id = None
    currency_quote = None
    commercial_comments = None
    total_amount = None
    comments = None
    payment_method = None
    incoterms = None
    language = None
    payment_date = None
    permits = None
    associated_invoices = None
    items = None
    extras = None

    def __init__(self, data=None):
        self.items = list()
        self.associated_invoices = list()
        self.extras = list()
        self.permits = list()
        if data is not None:
            if 'Id' in data:
                self.from_afip_dict(data)
            else:
                self.from_dict(data)

    def generate_id(self):
        self.id = int(time.time() * 1000)
        return self.id

    def add_extra(self, identifier, value):
        self.extras.append((identifier, value,))

    def add_permit(self, identifier, destination):
        self.permits.append((identifier, destination,))

    def add_associated_invoice(self, typ, pos, number, cuit):
        self.associated_invoices.append((typ, pos, number, cuit,))

    def add_item(self, code, description, quantity, measurement_unit, unit_price, discount, total_amount):
        self.items.append((code, description, quantity, measurement_unit, unit_price, discount, total_amount,))

    def _null(self, value):
        if value is None or value == '':
            return 'NULL'
        return value

    def to_dict(self):
        data = dict()
        for el in dir(self):
            value = getattr(self, el)
            typ = type(value).__name__
            if typ == 'method' or el.startswith('_'):
                continue
            if typ == 'date':
                value = unparse_date(value)
            data[el] = value
        return data

    def from_dict(self, data):
        for k, v in data.items():
            if 'date' in k:
                v = parse_date(v)
            setattr(self, k, v)

    def to_afip_dict(self):
        permits = [dict(Id_permiso=p[0], Dst_merc=p[1]) for p in self.permits]
        assoc_invoices = [dict(Cbte_tipo=i[0], Cbte_punto_vta=i[1], Cbte_nro=i[2], Cbte_cuit=i[3])
                         for i in self.associated_invoices]
        items = [dict(Pro_codigo=i[0], Pro_ds=i[1], Pro_qty=i[2], Pro_umed=i[3], Pro_precio_uni=i[4],
                      Pro_bonification=i[5], Pro_total_item=i[6]) for i in self.items]
        extras = [dict(Id=e[0], Valor=e[1]) for e in self.extras]
        invoice = {
            'Id': self.id,
            'Cbte_Tipo': self.invoice_type,
            'Punto_vta': self.pos,
            'Cbte_nro': str(self.number).zfill(8) if self.number is not None else None,
            'Tipo_expo': self.export_type,
            'Permiso_existente': self._null(self.existing_permit),
            'Dst_cmp': self.destination,
            'Cliente': self.client_name,
            'Domicilio_cliente': self.client_address,
            'Moneda_Id': self.currency_id,
            'Moneda_ctz': self.currency_quote,
            'Imp_total': self.total_amount,
            'Idioma_cbte': self.language,
            'Items': items,
        }
        if self.date is not None:
            invoice['Fecha_cbte'] = unparse_date(self.date)
        if len(permits):
            invoice['Permisos'] = permits
        if self.client_country_cuit is not None:
            invoice['Cuit_pais_cliente'] = self.client_country_cuit
        if self.client_tax_id is not None:
            invoice['Id_impositivo'] = self.client_tax_id
        if self.commercial_comments is not None:
            invoice['Obs_comerciales'] = self.commercial_comments
        if self.comments is not None:
            invoice['Obs'] = self.commercial_comments
        if self.payment_method is not None:
            invoice['Forma_pago'] = self.payment_method
        if self.incoterms is not None:
            invoice['Incoterms'] = self.incoterms[0]
            invoice['Incoterms_Ds'] = self.incoterms[1]
        if len(assoc_invoices):
            invoice['Cmps_asoc'] = assoc_invoices
        if len(extras):
            invoice['Opcionales'] = extras
        if self.payment_date is not None:
            invoice['Fecha_pago'] = unparse_date(self.payment_date)
        return invoice
        # < Id > long < / Id >
        # < Fecha_cbte > string < / Fecha_cbte >
        # < Cbte_Tipo > short < / Cbte_Tipo >
        # < Punto_vta > int < / Punto_vta >
        # < Cbte_nro > long < / Cbte_nro >
        # < Tipo_expo > short < / Tipo_expo >
        # < Permiso_existente > string < / Permiso_existente >
        # < Permisos >
            # < Permiso >
                # < Id_permiso > string < / Id_permiso >
                # < Dst_merc > int < / Dst_merc >
            # < / Permiso >
            # < Permiso >
                # < Id_permiso > string < / Id_permiso >
                # < Dst_merc > int < / Dst_merc >
            # < / Permiso >
        # < / Permisos >
        # < Dst_cmp > short < / Dst_cmp >
        # < Cliente > string < / Cliente >
        # < Cuit_pais_cliente > long < / Cuit_pais_cliente >
        # < Domicilio_cliente > string < / Domicilio_cliente >
        # < Id_impositivo > string < / Id_impositivo >
        # < Moneda_Id > string < / Moneda_Id >
        # < Moneda_ctz > decimal < / Moneda_ctz >
        # < Obs_comerciales > string < / Obs_comerciales >
        # < Imp_total > decimal < / Imp_total >
        # < Obs > string < / Obs >
        # < Cmps_asoc >
            # < Cmp_asoc >
                # < Cbte_tipo > short < / Cbte_tipo >
                # < Cbte_punto_vta > int < / Cbte_punto_vta >
                # < Cbte_nro > long < / Cbte_nro >
                # < Cbte_cuit > long < / Cbte_cuit >
            # < / Cmp_asoc >
            # < Cmp_asoc >
                # < Cbte_tipo > short < / Cbte_tipo >
                # < Cbte_punto_vta > int < / Cbte_punto_vta >
                # < Cbte_nro > long < / Cbte_nro >
                # < Cbte_cuit > long < / Cbte_cuit >
            # < / Cmp_asoc >
        # < / Cmps_asoc >
        # < Forma_pago > string < / Forma_pago >
        # < Incoterms > string < / Incoterms >
        # < Incoterms_Ds > string < / Incoterms_Ds >
        # < Idioma_cbte > short < / Idioma_cbte >
        # < Items >
            # < Item >
                # < Pro_codigo > string < / Pro_codigo >
                # < Pro_ds > string < / Pro_ds >
                # < Pro_qty > decimal < / Pro_qty >
                # < Pro_umed > int < / Pro_umed >
                # < Pro_precio_uni > decimal < / Pro_precio_uni >
                # < Pro_bonificacion > decimal < / Pro_bonificacion >
                # < Pro_total_item > decimal < / Pro_total_item >
            # < / Item >
            # < Item >
                # < Pro_codigo > string < / Pro_codigo >
                # < Pro_ds > string < / Pro_ds >
                # < Pro_qty > decimal < / Pro_qty >
                # < Pro_umed > int < / Pro_umed >
                # < Pro_precio_uni > decimal < / Pro_precio_uni >
                # < Pro_bonificacion > decimal < / Pro_bonificacion >
                # < Pro_total_item > decimal < / Pro_total_item >
            # < / Item >
        # < / Items >
        # < Opcionales >
        #     < Opcional >
        #         < Id > string < / Id >
        #         < Valor > string < / Valor >
        #     < / Opcional >
        # < / Opcionales >
        # < Fecha_pago > string < / Fecha_pago >

    def from_afip_dict(self, data):
        # TODO
        pass


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

    def _check_errors(self, ret, error_key ='FEXErr'):
        if error_key in ret and ret[error_key]['ErrCode'] != 0:
            raise WebServiceError(ret[error_key]['ErrCode'], ret[error_key]['ErrMsg'])

    def _invoke(self, endpoint, args=None, kwargs=None, auth=True, result_key='FEXResultGet'):
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
        return self._invoke('FEXDummy', auth=False, result_key=None)

    def get_country_cuits(self):
        ret = self._invoke('FEXGetPARAM_DST_CUIT')['ClsFEXResponse_DST_cuit']
        return [(c['DST_CUIT'], c['DST_Ds']) for c in ret]

    def get_currencies(self):
        ret = self._invoke('FEXGetPARAM_MON')['ClsFEXResponse_Mon']
        return [(c['Mon_Id'], c['Mon_Ds'], parse_date(c['Mon_vig_desde']),
                parse_date(c['Mon_vig_hasta'])) for c in ret]

    def get_invoice_types(self):
        ret = self._invoke('FEXGetPARAM_Cbte_Tipo')['ClsFEXResponse_Cbte_Tipo']
        return [(c['Cbte_Id'], c['Cbte_Ds'].strip(), parse_date(c['Cbte_vig_desde']),
                parse_date(c['Cbte_vig_hasta'])) for c in ret]

    def get_languages(self):
        ret = self._invoke('FEXGetPARAM_Idiomas')['ClsFEXResponse_Idi']
        return [(l['Idi_Id'], l['Idi_Ds']) for l in ret]

    def get_countries(self):
        ret = self._invoke('FEXGetPARAM_DST_pais')['ClsFEXResponse_DST_pais']
        return [(c['DST_Codigo'], c['DST_Ds']) for c in ret]

    def get_incoterms(self):
        ret = self._invoke('FEXGetPARAM_Incoterms')['ClsFEXResponse_Inc']
        return [(c['Inc_Id'], c['Inc_Ds'], parse_date(c['Inc_vig_desde']),
                parse_date(c['Inc_vig_hasta'])) for c in ret]

    def get_export_types(self):
        ret = self._invoke('FEXGetPARAM_Tipo_Expo')['ClsFEXResponse_Tex']
        return [(c['Tex_Id'], c['Tex_Ds'], parse_date(c['Tex_vig_desde']),
                parse_date(c['Tex_vig_hasta'])) for c in ret]

    def get_measurement_units(self):
        ret = self._invoke('FEXGetPARAM_UMed')['ClsFEXResponse_UMed']
        ret = [(c['Umed_Id'], c['Umed_Ds'], parse_date(c['Umed_vig_desde']),
                parse_date(c['Umed_vig_hasta'])) for c in ret]
        ret = [r for r in ret if not all([e is None for e in r])]
        ret.sort(key=lambda x: x[0])
        return ret

    def get_currency_quote(self, identifier):
        ret = self._invoke('FEXGetPARAM_Ctz', kwargs=dict(Mon_id=identifier))
        return parse_date(ret['Mon_fecha']), ret['Mon_ctz']

    def get_currency_quotes(self, date):
        ret = self._invoke('FEXGetPARAM_MON_CON_COTIZACION', kwargs=dict(Fecha_CTZ=unparse_date(date)))
        if ret is None:
            return list()
        ret = ret['ClsFEXResponse_Mon_CON_Cotizacion']
        return [(q['Mon_Id'], q['Mon_Ds'], q['Mon_ctz'], parse_date(q['Fecha_ctz'])) for q in ret]

    def get_points_of_sale(self):
        ret = self._invoke('FEXGetPARAM_PtoVenta')
        if ret is None:
            return list()
        ret = ret['ClsFEXResponse_PtoVenta']
        return [(c['Pve_Nro'], c['Pve_Bloqueado'], parse_date(c['Pve_FchBaja'])) for c in ret]

    def get_optional_data_types(self):
        ret = self._invoke('FEXGetPARAM_Opcionales')['ClsFEXResponse_Opc']
        return [(c['Opc_Id'], c['Opc_Ds'], parse_date(c['Opc_vig_desde']),
                parse_date(c['Opc_vig_hasta'])) for c in ret]

    def check_customs_permit(self, identifier, destination):
        return self._invoke('FEXCheck_Permiso', kwargs=dict(ID_Permiso=identifier, Dst_merc=destination))['Status']

    def get_last_invoice_number(self, pos, typ):
        args = dict(Auth=dict(Pto_venta=pos, Cbte_Tipo=typ, Token=self.auth.Token,
                              Sign=self.auth.Sign, Cuit=self.auth.Cuit))
        ret = self._invoke('FEXGetLast_CMP', kwargs=args, auth=False, result_key='FEXResult_LastCMP')
        return ret['Cbte_nro'], parse_date(ret['Cbte_fecha'])

    def get_last_invoice_id(self):
        ret = self._invoke('FEXGetLast_ID')
        if ret is not None:
            return ret['Id']

    def get_invoice(self, pos, typ, number):
        cmp = dict(Cbte_tipo=typ, Punto_vta=pos, Cbte_nro=number)
        # TODO: need an actual invoice to test!
        return self._invoke('FEXGetCMP', kwargs=dict(Cmp=cmp))

    def authorize(self, invoice):
        ret = self._invoke('FEXAuthorize', kwargs=dict(Cmp=invoice.to_afip_dict()), result_key='FEXAuthorizeResult')
        # TODO: process response. Maybe add info to 'invoice' so it can be persisted?
        return ret


class WSFEXTool(WebServiceTool):
    name = 'wsfex'
    help = 'Facturación Electrónica - Factura de exportación'
    client = None

    def __init__(self, parser):
        super().__init__(parser)
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand', required=True)
        subparsers.add_parser('status', help='get service status')
        subparsers.add_parser('country_cuits', help='get list of country CUIT numbers')
        subparsers.add_parser('currencies', help='get list of accepted foreign currencies')
        subparsers.add_parser('invoice_types', help='get list of valid invoice types')
        subparsers.add_parser('languages', help='get list of acceptable foreign languages')
        subparsers.add_parser('countries', help='get list of acceptable countries')
        subparsers.add_parser('incoterms', help='get list of acceptable incoterms')
        subparsers.add_parser('export_types', help='get list of types of exports')
        subparsers.add_parser('units', help='get list of acceptable measurement units')
        quote = subparsers.add_parser('quote', help='get quote for a given currency')
        quote.add_argument('currency', help='currency identifier')
        quotes = subparsers.add_parser('quotes', help='get all quotes for all currencies for a given date')
        quotes.add_argument('date', help='date in YYYY-MM-DD format')
        subparsers.add_parser('pos', help='get registered points of sale')
        subparsers.add_parser('optional', help='get optional data types')
        check_permit = subparsers.add_parser('check_permit', help='check validity of customs (aduana) permit')
        check_permit.add_argument('identifier', help='permit ID')
        check_permit.add_argument('destination', help='destination country ID')
        last_invoice_number = subparsers.add_parser('last_invoice_number', help='get last invoice number (not ID)')
        last_invoice_number.add_argument('pos', help='point of sale identifier')
        last_invoice_number.add_argument('type', help='type of invoice')
        subparsers.add_parser('last_invoice_id', help='get last invoice ID (used to authorize an invoice, not invoice number)')
        invoice = subparsers.add_parser('invoice', help='get invoice details')
        invoice.add_argument('pos', help='point of sale identifier')
        invoice.add_argument('type', help='type of invoice')
        invoice.add_argument('number', help='invoice number (not ID)')
        authorize = subparsers.add_parser('authorize', help='send invoice to AFIP for authorization (and CAE issuance) [IRREVERSIBLE!]')
        authorize.add_argument('path', help='path to valid invoice serialized from an Invoice instance (no interactive interface, sorry)')

    def handle(self, args):
        self.client = WSFEXClient(self.credentials, zeep_cache=self.zeep_cache, log_dir=self.log_dir)
        getattr(self, args.subcommand)(args)

    def status(self, args):
        for service, status in self.client.get_status().items():
            print(f'{service}: {status}')

    def country_cuits(self, args):
        for cuit, name in self.client.get_country_cuits():
            print(cuit, name)

    def currencies(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_currencies():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def languages(self, args):
        for identifier, name in self.client.get_languages():
            print(identifier, name)

    def countries(self, args):
        for identifier, name in self.client.get_countries():
            print(identifier, name)

    def incoterms(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_incoterms():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def invoice_types(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_invoice_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def export_types(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_export_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def units(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_measurement_units():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def quote(self, args):
        date, quote = self.client.get_currency_quote(args.currency)
        print('{}: {} ARS'.format(date, quote))

    def quotes(self, args):
        for identifier, description, rate, date in self.client.get_currency_quotes(self.parse_date(args.date)):
            print(str(date) + ':', identifier, description, rate, 'ARS')

    def pos(self, args):
        for identifier, blocked, closed_on in self.client.get_points_of_sale():
            print(identifier, blocked, closed_on)

    def optional(self, args):
        for identifier, name, valid_from, valid_until in self.client.get_optional_data_types():
            print(identifier, name, '[valid: from {}, until {}]'.format(valid_from, valid_until))

    def check_permit(self, args):
        print(self.client.check_customs_permit(args.identifier, args.destination))

    def last_invoice_number(self, args):
        number, date = self.client.get_last_invoice_number(args.pos, args.type)
        print("Number:", number)
        print("Date:", date)

    def last_invoice_id(self, args):
        print("Identifier:", self.client.get_last_invoice_id())

    def invoice(self, args):
        invoice = self.client.get_invoice(args.pos, args.type, args.number)
        # TODO: need an actual invoice to test!
        from pprint import pprint
        pprint(invoice)

    def authorize(self, args):
        with open(args.path) as fp:
            invoice = json.load(fp)
        invoice = Invoice(invoice)
        print(self.client.authorize(invoice))
        # TODO: pretty-print
