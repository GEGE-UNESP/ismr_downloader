import requests
import certifi


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"accept": "application/json"})
    session.verify = certifi.where()
    return session
