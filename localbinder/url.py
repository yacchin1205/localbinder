import re
from urllib.parse import urlparse

def parse_binder_url(url):
    o = urlparse(url)
    m = re.match(r'^/v2/([a-z]+)/(.+)$', o.path)
    if m is None:
        return None
    provider = m.group(1)
    spec = m.group(2).rstrip()
    return (provider, spec)
