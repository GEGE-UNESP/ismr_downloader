import requests
import urllib3


def create_session(verify_ssl: bool = True) -> requests.Session:
    session = requests.Session()
    session.headers.update({"accept": "application/json"})

    session.verify = verify_ssl
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return session