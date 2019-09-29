# Implements an interface to the "WSAA" web service as described in:
# http://www.afip.gob.ar/ws/WSAA/Especificacion_Tecnica_WSAA_1.2.2.pdf

import os
import time
import email
from datetime import datetime, timedelta, timezone
from M2Crypto import BIO, Rand, SMIME
from requests import Session
from zeep import Client
from zeep.transports import Transport
from lxml import etree
import dateutil.parser
import xml.etree.ElementTree as ET
from .zeep import TapeRecorderPlugin
from .ws import WebServiceTool

WSDL_URL_TESTING = 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl'
WSDL_URL_PRODUCTION = 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
TRA_TTL = 24 * 3600
TRA_DESTINATION_TESTING = "cn=wsaahomo,o=afip,c=ar,serialNumber=CUIT 33693450239"
TRA_DESTINATION_PRODUCTION = "cn=wsaa,o=afip,c=ar,serialNumber=CUIT 33693450239" 
TOKEN_EXPIRATION_OFFSET = -600


class LoginTicket:
    def __init__(self, xml, expiration_offset = TOKEN_EXPIRATION_OFFSET):
        self.xml = xml
        self.tree = None
        self.tree = ET.fromstring(self.xml)
        expires = self.tree.find('header/expirationTime').text
        self.expires = dateutil.parser.parse(expires).timestamp() + expiration_offset
        self.token = self.tree.find('credentials/token').text
        self.signature = self.tree.find('credentials/sign').text

    def is_expired(self):
        if time.time() >= self.expires:
            return True
        return False

    def __str__(self):
        return self.xml


class WSAAClient:
    def __init__(self, credentials, zeep_cache = None, log_dir = None):
        wsdl = WSDL_URL_PRODUCTION if credentials.production else WSDL_URL_TESTING
        session = Session()
        session.cert = (credentials.crt_path, credentials.key_path)
        transport = Transport(session=session, cache=zeep_cache)
        plugins = [TapeRecorderPlugin('wsaa', log_dir)] if log_dir is not None else []
        self.credentials = credentials
        self.client = Client(wsdl, transport=transport, plugins=plugins)

    def make_tra(self, service, source = None, destination = None, ttl = TRA_TTL):
        source = f"<source>{source}</source>" if source is not None else ""
        destination = f"<destination>{destination}</destination>" if destination else ""
        timestamp = int(time.time())
        unique_id = f"<uniqueId>{timestamp}</uniqueId>"
        created_at = datetime.now(timezone.utc).astimezone().isoformat()
        created_at = f"<generationTime>{created_at}</generationTime>"
        expires_at = (datetime.now(timezone.utc).astimezone() + timedelta(seconds=ttl)).isoformat()
        expires_at = f"<expirationTime>{expires_at}</expirationTime>"
        header = f"{source}{destination}{unique_id}{created_at}{expires_at}"
        body = f"<header>{header}</header><service>{service}</service>"
        return f'<?xml version="1.0" encoding="UTF­8"?><loginTicketRequest version="1.0">{body}</loginTicketRequest>'

    def sign_tra(self, tra):
        # Load cert and key
        s = SMIME.SMIME()
        s.load_key(self.credentials.key_path, self.credentials.crt_path)

        # Sign
        tra = BIO.MemoryBuffer(tra.encode('utf-8'))
        p7 = s.sign(tra)

        # Dump to e-Mail attachment format (don't ask)
        out = BIO.MemoryBuffer()
        s.write(out, p7)
        mail = out.read().decode('utf-8')

        # Unwrap signature
        msg = email.message_from_string(mail)
        for p in msg.walk():
            if p.get_filename() == "smime.p7m":
                return p.get_payload(decode=False)


    def authenticate(self, service):
        # Prepare TRA/CMS
        tra = self.make_tra(service)
        cms = self.sign_tra(tra)

        # Call service
        xml = self.client.service.loginCms(cms)

        # Parse and return
        return LoginTicket(xml)


class WSAATool(WebServiceTool):
    name = 'wsaa'
    help = 'WebService de Autenticación y Autorización'

    def __init__(self, parser):
        super().__init__(parser)
        self.token_dir = os.path.join(self.data_dir, 'tokens')
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand', required=True)
        subparsers.add_parser('show', help='print list of held tokens and expiration dates')
        auth = subparsers.add_parser('authorize', help='request token for a given service')
        auth.add_argument('service', help='name of service (WSN) to request a token for')

    def handle(self, args):
        if args.subcommand == 'show':
            return self.show(args)
        elif args.subcommand == 'authorize':
            return self.authorize(args)

    def show(self, args):
        pass
        # TODO:

    def authorize(self, args):
        pass # TODO