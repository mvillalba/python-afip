# Implements an interface to the "WSFEXV1" web service as described in:
# https://www.afip.gob.ar/ws/documentacion/manuales/WSFEX-Manualparaeldesarrollador_V1_6_0.pdf

import json
import time
from decimal import Decimal
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
    cuit = None
    cae = None
    cae_date = None  # Only returned on 'get invoice' operations, and appears to be set to a nil value.
    cae_expiration_date = None

    def __init__(self, dict_or_path=None):
        self.items = list()
        self.associated_invoices = list()
        self.extras = list()
        self.permits = list()
        if dict_or_path is not None:
            if type(dict_or_path) == str:
                self.from_json(dict_or_path)
            elif 'Id' in dict_or_path:
                self.from_afip_dict(dict_or_path)
            else:
                self.from_dict(dict_or_path)

    def generate_id(self):
        self.id = int(time.time() * 1000)
        return self.id

    def get_barcode_digits(self):
        # Barcode proper
        cuit = str(self.cuit)
        invoice_type = str(self.invoice_type).zfill(3)
        pos = str(self.pos).zfill(5)
        cae = str(self.cae).zfill(14)
        date = unparse_date(self.cae_expiration_date)  # TODO: unsure? invoice date?
        barcode = cuit + invoice_type + pos + cae + date

        # Verification digit
        odd = sum([int(d) for i, d in enumerate(barcode) if not i % 2])
        even = sum([int(d) for i, d in enumerate(barcode) if i % 2])
        digit = even + odd * 3
        digit = 10 - (digit - (int(digit / 10) * 10))
        digit = digit % 10
        return barcode + str(digit)

    def add_extra(self, identifier, value):
        self.extras.append((identifier, value,))

    def add_permit(self, identifier, destination):
        self.permits.append((identifier, destination,))

    def add_associated_invoice(self, typ, pos, number, cuit):
        self.associated_invoices.append((typ, pos, number, cuit,))

    def add_item(self, code, description, quantity, measurement_unit, unit_price, discount, total_amount):
        self.items.append((code, description, quantity, measurement_unit, unit_price, discount, total_amount,))

    def set_incoterms(self, code, description):
        self.incoterms = (code, description,)

    def _null(self, value):
        if value is None:
            return ''
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
            if typ == 'Decimal':
                value = str(value)
            data[el] = value
        return data

    def from_dict(self, data):
        for k, v in data.items():
            if 'date' in k:
                v = parse_date(v)
            setattr(self, k, v)

    def to_json(self, path):
        with open(path, 'w') as fp:
            json.dump(self.to_dict(), fp)

    def from_json(self, path):
        with open(path) as fp:
            self.from_dict(json.load(fp))

    def _item_to_afip(self, item):
        ret = dict()
        ret['Pro_ds'] = item[1]
        ret['Pro_umed'] = item[3]
        ret['Pro_bonificacion'] = Decimal(item[5] if item[5] is not None else '0')
        ret['Pro_total_item'] = Decimal(item[6])
        if item[4] is not None:
            ret['Pro_precio_uni'] = Decimal(item[4])
        if item[2] is not None:
            ret['Pro_qty'] = Decimal(item[2])
        if item[0] is not None:
            ret['Pro_codigo'] = item[0]
        ret = dict(Item=ret)
        return ret

    def to_afip_dict(self):
        permits = [dict(Permiso=dict(Id_permiso=p[0], Dst_merc=p[1])) for p in self.permits]
        assoc_invoices = [dict(Cmp_asoc=dict(Cbte_tipo=i[0], Cbte_punto_vta=i[1], Cbte_nro=i[2], Cbte_cuit=i[3]))
                          for i in self.associated_invoices]
        items = [self._item_to_afip(i) for i in self.items]
        extras = [dict(Optional=dict(Id=e[0], Valor=e[1])) for e in self.extras]
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

    def from_afip_dict(self, data):
        self.id = data['Id']
        self.date = parse_date(data['Fecha_cbte'])
        self.invoice_type = data['Cbte_tipo']
        self.pos = data['Punto_vta']
        self.number = data['Cbte_nro']
        self.export_type = data['Tipo_expo']
        self.existing_permit = data['Permiso_existente']
        self.permits = [(p['Id_permiso'], p['Dst_merc'],) for p in data['Permisos']] if data['Permisos'] else list()
        self.destination = data['Dst_cmp']
        self.client_name = data['Cliente']
        self.client_country_cuit = data['Cuit_pais_cliente']
        self.client_address = data['Domicilio_cliente']
        self.client_tax_id = data['Id_impositivo']
        self.currency_id = data['Moneda_Id']
        self.currency_quote = data['Moneda_ctz']
        self.commercial_comments = data['Obs_comerciales']
        self.total_amount = data['Imp_total']
        self.comments = data['Obs']
        if data['Cmps_asoc'] is not None:
            self.associated_invoices = [(i['Cbte_tipo'], i['Cbte_punto_vta'], i['Cbte_nro'], i['Cbte_cuit'])
                                        for i in data['Cmps_asoc']['Cmp_asoc']]
        self.payment_method = data['Forma_pago']
        if data['Incoterms'] is not None:
            self.incoterms = (data['Incoterms'], data['Incoterms_Ds'],)
        self.language = data['Idioma_cbte']
        items = [(i['Pro_codigo'], i['Pro_ds'], i['Pro_qty'], i['Pro_umed'], i['Pro_precio_uni'],
                  i['Pro_bonificacion'], i['Pro_total_item'], ) for i in data['Items']['Item']]
        self.items = items
        if 'Fecha_cbte_cae' in data:
            self.cae_date = parse_date(data['Fecha_cbte_cae'])
        self.cae_expiration_date = parse_date(data['Fch_venc_Cae'])
        self.cae = data['Cae']
        if data['Opcionales'] is not None:
            self.extras = [(e['Id'], e['Valor'],) for e in data['Opcionales']['Opcional']]


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

    def _check_errors(self, ret, error_key='FEXErr'):
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
        return Invoice(self._invoke('FEXGetCMP', kwargs=dict(Cmp=cmp)))

    def authorize(self, invoice):
        ret = self._invoke('FEXAuthorize', kwargs=dict(Cmp=invoice.to_afip_dict()), result_key='FEXResultAuth')
        if 'Cae' in ret:
            invoice.cae = ret['Cae']
        if 'Fch_venc_Cae' in ret:
            invoice.cae_expiration_date = parse_date(ret['Fch_venc_Cae'])
        if 'Cuit' in ret:
            invoice.cuit = ret['Cuit']
        return ret['Resultado'], ret['Reproceso'] == 'S', ret['Motivos_Obs']


class WSFEXTool(WebServiceTool):
    name = 'wsfex'
    help = 'Facturación Electrónica - Factura de exportación'
    client_class = WSFEXClient

    def __init__(self, parser):
        super().__init__(parser)
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
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
        subparsers.add_parser('last_invoice_id',
                              help='get last invoice ID (used to authorize an invoice, not invoice number)')
        invoice = subparsers.add_parser('invoice', help='get invoice details')
        invoice.add_argument('pos', help='point of sale identifier')
        invoice.add_argument('type', help='type of invoice')
        invoice.add_argument('number', help='invoice number (not ID)')
        authorize = subparsers.add_parser('authorize',
                                          help='send invoice to AFIP for authorization (and CAE issuance) [IRREVERSIBLE!]')
        authorize.add_argument('path', help='path to valid invoice serialized from an Invoice instance (no interactive interface, sorry)')

    def make_label(self, field):
        words = field.lower().split('_')
        label = list()
        for word in words:
            if word in ('cuit', 'cae'):
                word = word.upper()
            else:
                word = word[0].upper() + word[1:]
            label.append(word)
        return ' '.join(label)

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
        l = None
        for k, v in invoice.to_dict().items():
            if 'date' in k:
                v = parse_date(v)
            if type(v) == list and len(v):
                l = v
                v = ''
            print('{}: {}'.format(self.make_label(k), v))
            if l is not None:
                for i in l:
                    print(' -', i)
                l = None

    def authorize(self, args):
        invoice = Invoice(args.path)
        result, reprocessed, comments = self.client.authorize(invoice)
        print('Result:', result)
        print('Reprocessed:', reprocessed)
        print('Comment:', comments)
        print('CUIT:', invoice.cuit)
        print('CAE:', invoice.cae)
        print('CAE Expiration:', invoice.cae_expiration_date)
        invoice.to_json(args.path)
