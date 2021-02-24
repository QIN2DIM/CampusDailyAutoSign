__all__ = ['get_useragent']

from fake_useragent import UserAgent
from fake_useragent import errors


def get_useragent() -> str:
    try:
        return UserAgent().random
    except errors.FakeUserAgentError:
        exec('import os\nos.system("pip install -upgrade fake-useragent")')
