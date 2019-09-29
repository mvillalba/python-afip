import sys
import argparse
from .version import __version__
from .wsaa import WSAATool
from .ws import ProfileTool

COMMAND_CLASSES = (
    ProfileTool,
    WSAATool,
)


class CLITool:
    def __init__(self, argv, command_classes = COMMAND_CLASSES):
        self.parser = None
        self.subparsers = None
        self.argv = argv
        self.args = None
        self.commands = dict()
        self.setup(command_classes)

    def setup(self, command_classes):
        # Base parser
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--profile', )
        self.subparsers = self.parser.add_subparsers(title='commands', dest='command', required=True)

        # Internal commands
        self.subparsers.add_parser('version', help='print out version number')

        # External commands
        for cls in command_classes:
            subparser = self.subparsers.add_parser(cls.name, help=cls.help)
            self.commands[cls.name] = cls(subparser)

    def command_version(self):
        print("afip", __version__)

    def run(self):
        # Run parser
        self.args = self.parser.parse_args(self.argv[1:])

        # Handle internal commands
        internal = [s.split('_')[1] for s in dir(self) if s.startswith('command_')]
        if self.args.command in internal:
            return getattr(self, 'command_' + self.args.command)()

        # Handle external commands
        return self.commands[self.args.command].run(self.args)


# Run tool
if __name__ == '__main__':
    CLITool(sys.argv).run()


# from zeep.cache import SqliteCache
# from afip.credentials import AFIPCredentials
# from afip.wsaa import WSAAClient
#
# CACHE_PATH = 'zeep.db'
# CACHE_TIMEOUT = 24 * 3600
# CERT_PEM_PATH = 'certs/testing.pem'
# CERT_KEY_PATH = 'certs/privkey'
# LOG_DIR = 'logs'
#
#
# # Call
# cache = SqliteCache(path=CACHE_PATH, timeout=CACHE_TIMEOUT)
# creds = AFIPCredentials(CERT_PEM_PATH, CERT_KEY_PATH, production=False)
# client = WSAAClient(creds, zeep_cache=cache, log_dir=LOG_DIR)
# r = client.authenticate('wsfe')
#
#
# # Dump raw response
# print ("=== BEGIN RAW RESPONSE ===")
# print(r)
# print ("=== END RAW RESPONSE ===")
#
# # Dump parsed response
# print ("=== BEGIN PARSED RESPONSE ===")
# print("Expires:", r.expires)
# print("Token:", r.token)
# print("Signature:", r.signature)