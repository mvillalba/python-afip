import os
import re
import json
from appdirs import user_data_dir
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.cache import SqliteCache
from .credentials import AFIPCredentials, LoginTicket
from .zeep import TapeRecorderPlugin

ZEEP_CACHE_TIMEOUT = 24 * 3600


class WebServiceError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f'{self.code}: {self.message}'


class WebServiceClient:
    name = None
    wsdl_testing = None
    wsdl_production = None
    needs_ticket = True

    def __init__(self, credentials, zeep_cache=None, log_dir=None):
        if self.needs_ticket and self.name not in credentials.tickets:
            raise Exception(f'Ticket for "{self.name}" service not found in credentials object.')
        wsdl = self.wsdl_production if credentials.production else self.wsdl_testing
        session = Session()
        session.cert = (credentials.crt_path, credentials.key_path)
        transport = Transport(session=session, cache=zeep_cache)
        plugins = [TapeRecorderPlugin(self.name, log_dir)] if log_dir is not None else []
        self.credentials = credentials
        self.client = Client(wsdl, transport=transport, plugins=plugins)


class WebServiceTool:
    name = None
    help = None
    needs_profile = True
    client = None
    client_class = None

    def __init__(self, parser):
        self.data_dir = user_data_dir('afip', 'martinvillalba.com')
        zeep_cache = os.path.join(self.data_dir, 'zeep.db')
        self.zeep_cache = SqliteCache(path=zeep_cache, timeout=ZEEP_CACHE_TIMEOUT)
        self.log_dir = os.path.join(self.data_dir, 'logs')
        self.token_dir = os.path.join(self.data_dir, 'tokens')
        self.credentials_dir = os.path.join(self.data_dir, 'credentials')
        self.credentials = None
        self.profile = None
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.credentials_dir, exist_ok=True)
        os.makedirs(self.token_dir, exist_ok=True)

    def run(self, args):
        # Pick profile
        profile = args.profile if args.profile is not None else None
        if profile is None:
            profile = [e.split('.')[0] for e in os.listdir(self.credentials_dir) if e.endswith('.json')]
            profile = profile[0] if len(profile) == 1 else None
        if profile is None and self.needs_profile:
            print('Could not find a default profile. Please add one.')
            return

        # Load profile
        if profile is not None:
            self.profile = profile
            path = self.get_profile_path(profile)
            if not os.path.exists(path):
                print("Profile not found:", profile)
                return
            with open(path) as fp:
                profile = json.load(fp)
            tickets = self.get_tickets()
            self.credentials = AFIPCredentials(profile['cuit'], profile['crt_path'], profile['key_path'],
                                               profile['environment'] == 'production', tickets)

        # Call sub-class handler
        return self.handle(args)

    def get_profile_path(self, profile, extension='json'):
        return os.path.join(self.credentials_dir, profile + '.' + extension)

    def get_tickets(self):
        tickets = dict()
        tokens = {t.split('.')[1]: t for t in os.listdir(self.token_dir) if t.startswith(self.profile + '.')}
        for service, path in tokens.items():
            ticket = self.get_ticket(service)
            if ticket is None:
                continue
            tickets[service] = ticket
        return tickets

    def get_ticket(self, service):
        path = os.path.join(self.token_dir, self.profile + '.' + service + '.xml')
        with open(path) as fp:
            ticket = LoginTicket(fp.read())
        if ticket.is_expired():
            os.unlink(path)
            return
        return ticket

    def handle(self, args):
        self.client = self.client_class(self.credentials, zeep_cache=self.zeep_cache, log_dir=self.log_dir)
        if hasattr(args, 'subcommand'):
            getattr(self, args.subcommand)(args)
        else:
            raise NotImplementedError()


class ProfileTool(WebServiceTool):
    name = 'profile'
    help = 'manage credentials'
    needs_profile = False

    def __init__(self, parser):
        super().__init__(parser)
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand', required=True)

        subparsers.add_parser('show', help='print list of profiles')

        remove = subparsers.add_parser('remove', help='delete profile by name')
        remove.add_argument('name', help='name of the profile to delete')

        add = subparsers.add_parser('add', help='add profile')
        add.add_argument('name', help='name for the profile (e.g "martin_testing")')
        add.add_argument('cuit', help='CUIT number for tax payer')
        add.add_argument('crt_path', help='path to X.509 certificate')
        add.add_argument('key_path', help='path to certificate private key')
        add.add_argument('environment', help='either "testing" or "production"')

    def handle(self, args):
        if args.subcommand == 'show':
            return self.show(args)
        if args.subcommand == 'add':
            return self.add(args)
        if args.subcommand == 'remove':
            return self.remove(args)

    def get_env(self, p):
        with open(self.get_profile_path(p), 'r') as fp:
            return json.load(fp)['environment']

    def show(self, args):
        profiles = [f.split('.')[0] for f in os.listdir(self.credentials_dir) if f.endswith('.json')]
        profiles = {p: self.get_env(p) for p in profiles}
        for p, e in profiles.items():
            print(f'{p} [{e}]')

    def add(self, args):
        # Check args
        if re.match(r'^[a-zA-Z_\-0-9]+$', args.name) is None:
            print(r'Name must follow regex: ^[a-zA-Z_\-0-9]+$')
            return
        if args.environment not in ('testing', 'production'):
            print('Environment must be one of: testing, production.')
            return

        # Does it exist?
        path = self.get_profile_path(args.name)
        if os.path.exists(path):
            print('Profile already exists. To replace it, delete it first.')
            return

        # Save
        crt_path = self.get_profile_path(args.name, 'crt')
        with open(args.crt_path) as ifp:
            with open(crt_path, 'w') as ofp:
                ofp.write(ifp.read())

        key_path = self.get_profile_path(args.name, 'key')
        with open(args.key_path) as ifp:
            with open(key_path, 'w') as ofp:
                ofp.write(ifp.read())

        data = dict(cuit=args.cuit, crt_path=crt_path, key_path=key_path, environment=args.environment)
        with open(self.get_profile_path(args.name), 'w') as fp:
            json.dump(data, fp)

    def remove(self, args):
        if re.match(r'^[a-zA-Z_\-0-9]+$', args.name) is None:
            print(r'Name must follow regex: ^[a-zA-Z_\-0-9]+$')
            return
        json_path = self.get_profile_path(args.name)
        crt_path = self.get_profile_path(args.name, 'crt')
        key_path = self.get_profile_path(args.name, 'key')
        if os.path.exists(json_path):
            os.unlink(json_path)
        if os.path.exists(crt_path):
            os.unlink(crt_path)
        if os.path.exists(key_path):
            os.unlink(key_path)
