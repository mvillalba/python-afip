import sys
import argparse
import zeep.exceptions
from .version import __version__
from .wsaa import WSAATool
from .wsfex import WSFEXTool
from .wsfe import WSFETool
from .ws_sr_padron_a5 import WSSRPadronA5Tool
from .ws_sr_padron_a13 import WSSRPadronA13Tool
from .ws import ProfileTool

COMMAND_CLASSES = (
    ProfileTool,
    WSAATool,
    WSFEXTool,
    WSFETool,
    WSSRPadronA5Tool,
    WSSRPadronA13Tool,
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
        self.parser.add_argument('--profile', '-p', help='profile to use (when there is more than one)')
        # Not passing required=True to add_subparsers to allow for pre Python 3.7 compatibility.
        self.subparsers = self.parser.add_subparsers(title='commands', dest='command')

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
        if self.args.command is None:
            print('Error: command not given. Use the -h flag for a list.')
            return
        try:
            return self.commands[self.args.command].run(self.args)
        except zeep.exceptions.Fault as e:
            print('Error: {}: {}'.format(e.code, e.message))


# Run tool
if __name__ == '__main__':
    CLITool(sys.argv).run()
