from yaml import load, Loader


def get_secret(key: str, base_url='', token='', cert="root_ca.pem") -> tuple:
    """
    :param key: The ID of the secret to retrieve
    :param base_url: The base URL of the Vault server (default is VAULT_ADDR)
    :param token: The token to authenticate with the Vault server (default is TOKEN)
    :param cert: The path to the certificate file to verify the Vault server's SSL certificate (default is "root_ca.pem")
    :return: A tuple containing the key-value pairs of the secret (None, None) if the secret retrieval fails

    This method retrieves a secret from a Vault server using the provided ID. It sends a GET request to the Vault server with the necessary headers and authentication token. If the request is successful (status code 200), the method extracts the key-value pairs from the response JSON and returns them as a tuple. If the request fails, the method prints an HTTP error message and returns (None, None).
    """
    import requests
    try:
        secrets = load(open('secrets.yml', 'r'), Loader=Loader)
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
    resp = requests.get(url, headers=headers, verify=cert)
    if resp.status_code == 200:
        secret = resp.json()["data"]["data"]
        for username, password in secret.items():
            return username, password
    else:
        print(f"http error {resp.status_code}")
        return None, None

