import time
import dateutil.parser
import xml.etree.ElementTree as ET

TOKEN_EXPIRATION_OFFSET = -600


class AFIPCredentials:
    def __init__(self, cuit, crt_path, key_path, production=False, tickets=None):
        self.cuit = cuit
        self.crt_path = crt_path
        self.key_path = key_path
        self.production = production
        self.tickets = dict() if tickets is None else tickets


class LoginTicket:
    def __init__(self, xml, expiration_offset=TOKEN_EXPIRATION_OFFSET):
        self.xml = xml
        self.tree = None
        self.tree = ET.fromstring(self.xml)
        self.expires_str = self.tree.find('header/expirationTime').text
        self.expires = dateutil.parser.parse(self.expires_str).timestamp() + expiration_offset
        self.token = self.tree.find('credentials/token').text
        self.signature = self.tree.find('credentials/sign').text

    def is_expired(self):
        if time.time() >= self.expires:
            return True
        return False

    def __str__(self):
        return self.xml
