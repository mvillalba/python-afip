from zeep.cache import SqliteCache
from afip.credentials import AFIPCredentials
from afip.wsaa import WSAAClient

CACHE_PATH = 'zeep.db'
CACHE_TIMEOUT = 24 * 3600
CERT_PEM_PATH = 'certs/testing.pem'
CERT_KEY_PATH = 'certs/privkey'
LOG_DIR = 'logs'


# Call
cache = SqliteCache(path=CACHE_PATH, timeout=CACHE_TIMEOUT)
creds = AFIPCredentials(CERT_PEM_PATH, CERT_KEY_PATH, production=False)
client = WSAAClient(creds, zeep_cache=cache, log_dir=LOG_DIR)
r = client.authenticate('wsfe')


# Dump raw response
print ("=== BEGIN RAW RESPONSE ===")
print(r)
print ("=== END RAW RESPONSE ===")

# Dump parsed response
print ("=== BEGIN PARSED RESPONSE ===")
print("Expires:", r.expires)
print("Token:", r.token)
print("Signature:", r.signature)
