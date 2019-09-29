import os
import re
import json
from appdirs import user_data_dir
from zeep.cache import SqliteCache
from .credentials import AFIPCredentials, LoginTicket

ZEEP_CACHE_TIMEOUT = 24 * 3600


class WebServiceTool:
    name = None
    help = None
    needs_profile = True

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
            self.credentials = AFIPCredentials(profile['crt_path'], profile['key_path'], profile['environment'] == 'production')

        # Call sub-class handler
        return self.handle(args)

    def get_profile_path(self, profile, extension='json'):
        return os.path.join(self.credentials_dir, profile + '.' + extension)

    def get_ticket(self, service):
        path = os.path.join(self.token_dir, self.profile + '.' + service + '.xml')
        with open(path) as fp:
            ticket = LoginTicket(fp.read())
        if ticket.is_expired():
            os.unlink(path)
            return
        return ticket

    def handle(self, args):
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

        data = dict(crt_path=crt_path, key_path=key_path, environment=args.environment)
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
