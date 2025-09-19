import requests
import urllib3


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"accept": "application/json"})

    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return session
