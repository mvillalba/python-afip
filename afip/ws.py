import os
import re
import json
from appdirs import user_data_dir


class WebServiceTool:
    name = None
    help = None

    def __init__(self, parser):
        self.data_dir = user_data_dir('afip', 'martinvillalba.com')
        self.credentials_dir = os.path.join(self.data_dir, 'credentials')
        os.makedirs(self.credentials_dir, exist_ok=True)

    def run(self, args):
        # TODO: check profile args, or select default
        return self.handle(args)

    def handle(self, args):
        raise NotImplementedError()


class ProfileTool(WebServiceTool):
    name = 'profile'
    help = 'manage credentials'

    def __init__(self, parser):
        super().__init__(parser)
        # TODO: add, remove, list commands
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand', required=True)

        subparsers.add_parser('show', help='print list of profiles')

        remove = subparsers.add_parser('remove', help='delete profile by name')
        remove.add_argument('name', help='name of the profile to delete', type=str, nargs=1)

        add = subparsers.add_parser('add', help='add profile')
        add.add_argument('name', help='name for the profile (e.g "martin_testing")', type=str, nargs=1)
        add.add_argument('crt_path', help='path to X.509 certificate', type=str, nargs=1)
        add.add_argument('key_path', help='path to certificate private key', type=str, nargs=1)
        add.add_argument('environment', help='either "testing" or "production"', type=str, nargs=1)

    def handle(self, args):
        if args.subcommand == 'show':
            return self.show(args)
        if args.subcommand == 'add':
            return self.add(args)
        if args.subcommand == 'remove':
            return self.remove(args)

    def get_path(self, profile, extension='json'):
        return os.path.join(self.credentials_dir, profile + '.' + extension)

    def get_env(self, p):
        with open(self.get_path(p), 'r') as fp:
            return json.load(fp)['environment']

    def show(self, args):
        profiles = [f.split('.')[0] for f in os.listdir(self.credentials_dir) if f.endswith('.json')]
        profiles = {p: self.get_env(p) for p in profiles}
        for p, e in profiles.items():
            print(f'{p} [{e}]')

    def add(self, args):
        # Check args
        if re.match(r'^[a-zA-Z_\-0-9]+$', args.name[0]) is None:
            print(r'Name must follow regex: ^[a-zA-Z_\-0-9]+$')
            return
        if args.environment[0] not in ('testing', 'production'):
            print('Environment must be one of: testing, production.')
            return

        # Does it exist?
        path = self.get_path(args.name[0])
        if os.path.exists(path):
            print('Profile already exists. To replace it, delete it first.')
            return

        # Save
        crt_path = self.get_path(args.name[0], 'crt')
        with open(args.crt_path[0]) as ifp:
            with open(crt_path, 'w') as ofp:
                ofp.write(ifp.read())

        key_path = self.get_path(args.name[0], 'key')
        with open(args.key_path[0]) as ifp:
            with open(key_path, 'w') as ofp:
                ofp.write(ifp.read())

        data = dict(crt_path=crt_path, key_path=key_path, environment=args.environment[0])
        with open(self.get_path(args.name[0]), 'w') as fp:
            json.dump(data, fp)

    def remove(self, args):
        if re.match(r'^[a-zA-Z_\-0-9]+$', args.name[0]) is None:
            print(r'Name must follow regex: ^[a-zA-Z_\-0-9]+$')
            return
        json_path = self.get_path(args.name[0])
        crt_path = self.get_path(args.name[0], 'crt')
        key_path = self.get_path(args.name[0], 'key')
        if os.path.exists(json_path):
            os.unlink(json_path)
        if os.path.exists(crt_path):
            os.unlink(crt_path)
        if os.path.exists(key_path):
            os.unlink(key_path)
