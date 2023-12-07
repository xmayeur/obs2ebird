from yaml import load, Loader
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64encode, b64decode
from os.path import join, exists
from os import getenv, makedirs


class RSAcipher:
    """

    Example:
        create_keyset('test', '~/.ssl')
        rsa = RSAcipher('pub_test.pem')
        encrypted_msg = rsa.encrypt(text)
        rsa = RSAcipher('priv_test.pem')
        msg = rsa.decrypt(encrypted_msg)

    """

    def __init__(self, key=None, directory='~/.ssl', create_keys=False):
        if directory[0] == '~':
            self.directory = join(getenv('HOME'), directory[2:])
        else:
            self.directory = directory

        if key is not None and create_keys:
            self.create_keyset(key)
        if key is not None:
            _key = RSA.importKey(open(join(self.directory, 'pub_' + key + '.pem')).read())
            self.e_rsa = PKCS1_OAEP.new(_key)
            _key = RSA.importKey(open(join(self.directory, 'priv_' + key + '.pem')).read())
            self.d_rsa = PKCS1_OAEP.new(_key)

    def encrypt(self, text):
        return b64encode(self.e_rsa.encrypt(text.encode())).decode()

    def decrypt(self, msg):
        try:
            return self.d_rsa.decrypt(b64decode(msg)).decode()
        except Exception:
            return None

    def create_keyset(self, name='key'):
        key = RSA.generate(2048)
        with open(join(self.directory, 'priv_' + name + '.pem'), 'wb') as f:
            f.write(key.exportKey('PEM'))
        pubkey = key.publickey()
        with open(join(self.directory, 'pub_' + name + '.pem'), 'wb') as f:
            f.write(pubkey.exportKey())


def get_secret(key: str, base_url='', token='', cert="root_ca.pem") -> tuple:
    """
    :param key: The ID of the secret to retrieve
    :param base_url: The base URL of the Vault server (default is VAULT_ADDR)
    :param token: The token to authenticate with the Vault server (default is TOKEN)
    :param cert: The path to the certificate to verify the Vault server's SSL certificate (default is "root_ca.pem")
    :return: A tuple containing the key-value pairs of the secret (None, None) if the secret retrieval fails

    This method retrieves a secret from a Vault server using the provided ID.
    It sends a GET request to the Vault server with the necessary headers and authentication token.
    If the request is successful (status code 200), the method extracts the key-value pairs from the response JSON
    and returns them as a tuple. If the request fails, the method prints an HTTP error message and returns (None, None).
    """
    import requests

    try:
        directory = join(getenv('HOME'), '.config')
        if not exists(directory):
            makedirs(directory)
        secret_file = join(getenv('HOME'), '.config', 'secrets.bin')
        if not exists(join(getenv('HOME'), '.ssl/priv_o2eb.pem')):
            rsa = RSAcipher('o2eb', create_keys=True)
            # We assume that a secrets.bin file exists with a yaml structure containing the secrets
            data = open(secret_file, 'r').read()
            # This file will be encrypted and overwritten with the created keys
            enc_data = rsa.encrypt(data)
            open(secret_file, 'w').write(enc_data)
        rsa = RSAcipher('o2eb')
        enc_data = open(secret_file, 'r').read()
        data = rsa.decrypt(enc_data)
        secrets = load(data, Loader=Loader)
        if token == '':
            token = secrets['db']['TOKEN']
        if base_url == '':
            base_url = secrets['db']['VAULT_ADDR']
    except IOError:
        return None, None
    except KeyError:
        return None, None

    headers = {"X-Vault-Token": token}
    uri = "/v1/secret/data/"
    url = f"{base_url}{uri}{key}"
    resp = requests.get(url, headers=headers, verify=join(getenv('HOME'), '.ssl', cert))
    if resp.status_code == 200:
        secret = resp.json()["data"]["data"]
        for username, password in secret.items():
            return username, password
    else:
        print(f"http error {resp.status_code}")
        return None, None
