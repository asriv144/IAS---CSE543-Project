# src/features.py
from urllib.parse import urlparse, unquote
import tldextract
import re
import os

# Use the same extractor you used earlier
_cache_dir = os.path.join(os.path.dirname(__file__), "tld_cache")
os.makedirs(_cache_dir, exist_ok=True)
extractor = tldextract.TLDExtract(cache_dir=_cache_dir, fallback_to_snapshot=True)


SUSPICIOUS_KEYWORDS = ['login','secure','verify','account','update','bank','confirm','signin','admin','wp-login']

def count_digits(s: str) -> int:
    return sum(c.isdigit() for c in s)

def count_char(s: str, ch: str) -> int:
    return s.count(ch)

def has_ip(host: str) -> int:
    return 1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else 0

FEATURE_ORDER = [
    'url_length',
    'hostname_length',
    'path_length',
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
    'path_depth',
    'ends_with_slash',
    'num_parameters'
]

def canonicalize_url(raw_url: str) -> str:
    # ensure scheme and host; remove fragments; lower host; decode percent-encoding
    if not raw_url:
        return ""
    u = raw_url.strip()
    if not u.startswith(("http://","https://")):
        u = "http://" + u
    parsed = urlparse(u)
    # remove fragment
    parsed = parsed._replace(fragment="")
    # normalize path: remove redundant // and collapse
    path = unquote(parsed.path or "")
    # remove trailing slash for canonicalization except keep empty path
    if path == "/":
        path = ""
    # rebuild canonical URL without query and fragment
    canonical = f"{parsed.scheme}://{parsed.netloc.lower()}{path}"
    return canonical

def extract_features(url: str) -> dict:
    # canonicalize here so features are consistent
    raw = str(url or "")
    try:
        parsed_raw = urlparse(raw)
    except Exception:
        parsed_raw = urlparse("http://" + raw)

    # Use canonical URL for features (no fragments, preserve path)
    canonical = canonicalize_url(raw)
    parsed = urlparse(canonical)
    host = parsed.netloc or ""
    path = parsed.path or ""            # path without trailing slash ('' for root)
    query = parsed_raw.query or ""      # original query (not used in many features)
    ext = extractor(canonical)
    registered = ext.registered_domain or ""

    # host+path combined for safer substring checks (avoid query noise)
    host_path = (host + path).lower()

    features = {}
    # url_length: exclude scheme to reduce noise from http/https differences
    features['url_length'] = len(host + path)
    features['hostname_length'] = len(host)
    # path_length uses stripped segments so root becomes 0
    features['path_length'] = len(path.strip('/'))
    features['count_digits'] = count_digits(host + path)
    features['count_dots'] = count_char(host, '.')
    features['count_dash'] = count_char(host, '-')
    # number of subdomains = number of labels before registered domain
    if registered and registered in host:
        prefix = host.replace(registered, '').strip('.')
        features['num_subdomains'] = prefix.count('.') + (1 if prefix else 0) if prefix else 0
    else:
        features['num_subdomains'] = max(0, host.count('.') - 1)

    features['has_https'] = 1 if parsed.scheme == 'https' else 0
    features['has_ip'] = has_ip(host)
    # suspicious keywords only checked in host+path (not query) to reduce false positives
    features['suspicious_keywords'] = int(any(k in host_path for k in SUSPICIOUS_KEYWORDS))

    features['count_at'] = count_char(host + path, '@')
    features['count_question'] = count_char(host + path, '?')
    features['count_ampersand'] = count_char(host + path, '&')
    features['count_percent'] = count_char(host + path, '%')
    features['count_equals'] = count_char(host + path, '=')
    features['count_underscore'] = count_char(host + path, '_')
    features['contains_ip_port'] = 1 if re.search(r'\d+\.\d+\.\d+\.\d+:\d+', host) else 0
    features['has_www'] = 1 if host.startswith('www.') else 0
    features['tld_length'] = len(ext.suffix or '')
    features['path_depth'] = len([p for p in path.split('/') if p])
    features['ends_with_slash'] = 1 if raw.endswith('/') and path != "" else 0
    # num_parameters: number of query params (0 if none)
    features['num_parameters'] = len([p for p in (query.split('&') if query else []) if p])

    # ensure stable order
    out = {k: int(features.get(k, 0)) if isinstance(features.get(k,0), (bool,int)) else features.get(k,0)
           for k in FEATURE_ORDER}
    return out
