
class AFIPCredentials:
    def __init__(self, crt_path, key_path, production = False):
        self.crt_path = crt_path
        self.key_path = key_path
        self.production = production
