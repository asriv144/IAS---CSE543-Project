# src/features.py
from urllib.parse import urlparse
import tldextract
import re

SUSPICIOUS_KEYWORDS = ['login','secure','verify','account','update','bank','confirm','signin','admin','wp-login']

def count_digits(s: str) -> int:
    return sum(c.isdigit() for c in s)

def count_char(s: str, ch: str) -> int:
    return s.count(ch)

def has_ip(host: str) -> int:
    # quick IPv4 check
    return 1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else 0

# # The order here must be stable and used when training & predicting.
# FEATURE_ORDER = [
#     'url_length',
#     'hostname_length',
#     'path_length',
#     'count_digits',
#     'count_dots',
#     'count_dash',
#     'num_subdomains',
#     'has_https',
#     'has_ip',
#     'suspicious_keywords',
#     'count_at',
#     'count_question',
#     'count_ampersand',
#     'count_percent',
#     'count_equals',
#     'count_underscore',
#     'contains_ip_port',
#     'has_www',
#     'tld_length',
#     'path_depth',
#     'ends_with_slash',
#     'num_parameters'
# ]

FEATURE_ORDER = [
    'url_length',
    'hostname_length',
    'count_digits',
    'count_dots',
    'count_dash',
    'num_subdomains',
    'has_https',
    'has_ip',
    'suspicious_keywords',
    'count_at',
    'count_question',
    'count_ampersand',
    'count_percent',
    'count_equals',
    'count_underscore',
    'contains_ip_port',
    'has_www',
    'tld_length',
    'num_parameters'
]

def extract_features(url: str) -> dict:
    parsed = urlparse(url)
    host = parsed.netloc or ""
    path = parsed.path or ""
    query = parsed.query or ""
    full = url or ""
    ext = tldextract.extract(url)
    registered = ext.registered_domain or ""
    features = {}
    features['url_length'] = len(full)
    features['hostname_length'] = len(host)
    features['path_length'] = len(path)
    features['count_digits'] = count_digits(full)
    features['count_dots'] = count_char(host, '.')
    features['count_dash'] = count_char(host, '-')
    # subdomain count: parts before domain
    subdomains = host.replace(registered, '').strip('.')
    features['num_subdomains'] = subdomains.count('.') + (1 if subdomains else 0) if subdomains else 0
    features['has_https'] = 1 if parsed.scheme == 'https' else 0
    features['has_ip'] = has_ip(host)
    features['suspicious_keywords'] = int(any(k in full.lower() for k in SUSPICIOUS_KEYWORDS))
    features['count_at'] = count_char(full, '@')
    features['count_question'] = count_char(full, '?')
    features['count_ampersand'] = count_char(full, '&')
    features['count_percent'] = count_char(full, '%')
    features['count_equals'] = count_char(full, '=')
    features['count_underscore'] = count_char(full, '_')
    # contains ip:port
    features['contains_ip_port'] = 1 if re.search(r'\d+\.\d+\.\d+\.\d+:\d+', full) else 0
    features['has_www'] = 1 if host.startswith('www.') else 0
    features['tld_length'] = len(ext.suffix or '')
    features['path_depth'] = len([p for p in path.split('/') if p])
    features['ends_with_slash'] = 1 if full.endswith('/') else 0
    features['num_parameters'] = 1 if query else 0

    # ensure all features in FEATURE_ORDER exist
    out = {k: int(features.get(k, 0)) if isinstance(features.get(k,0), bool) or isinstance(features.get(k,0), int) else features.get(k,0)
           for k in FEATURE_ORDER}
    return out
