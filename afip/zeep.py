import os
import time
import json
from datetime import datetime
from lxml import etree
from zeep import Plugin


class TapeRecorderPlugin(Plugin):
    def __init__(self, prefix, log_dir):
        date = datetime.now().isoformat()
        log_name = f'{prefix}_{date}.jl'
        self.log_dir = log_dir
        self.log_path = os.path.join(log_dir, log_name)
        self.fp = None

    def __del__(self):
        self.close()

    def log(self, typ, data):
        data['type'] = typ
        data['timestamp'] = time.time()
        if self.fp is None:
            os.makedirs(self.log_dir, exist_ok=True)
            self.fp = open(self.log_path, 'w')
        self.fp.write(json.dumps(data) + '\n')
        self.fp.flush()

    def close(self):
        if self.fp is not None:
            self.fp.close()

    def ingress(self, envelope, http_headers, operation):
        entry = {
            'envelope': etree.tostring(envelope, pretty_print=True).decode('utf-8'),
            'headers': dict(http_headers),
            'operation': str(operation),
        }
        self.log("ingress", entry)
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        entry = {
            'envelope': etree.tostring(envelope, pretty_print=True).decode('utf-8'),
            'headers': dict(http_headers),
            'operation': str(operation),
            'binding_options': dict(binding_options),
        }
        self.log("egress", entry)
        return envelope, http_headers
