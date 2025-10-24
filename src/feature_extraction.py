#feature_extraction
import re
from urllib.parse import urlparse
import tldextract

SHORTENERS = [
    "bit.ly", "tinyurl.com", "ow.ly", "t.co", "goo.gl", "is.gd",
    "buff.ly", "adf.ly", "bitly.com", "lc.chat", "shorturl.at"
]

SUSPICIOUS_WORDS = [
    "login", "signin" , "secure", "account", "update", "verify", "bank", "ebay", "paypal"
]

def extract_url_features(url:str) -> dict:
    #Return a dic of url based features for a single url string
    if not isinstance(url,str):
        url=str(url)
    
    parsed=urlparse(url)
    te=tldextract.extract(url)
    domain=te.top_domain_under_public_suffix or te.registered_domain or ""
    path=parsed.path or ""
    query=parsed.query or ""

    features={}
    features['url']=url
    features['scheme']=parsed.scheme or ''
    features['has_https']=int(parsed.scheme=='https')

    features['url_length']=len(url)
    features['hostname_length']=len(parsed.netloc)
    features['path_length']=len(path)
    features['query_length']=len(query)

    features['count_dots']=url.count('.')
    features['count_slash']=url.count('/')
    features['count_at']=url.count('@')
    features['count_dash']=url.count('-')
    features['count_underscore']=url.count('_')
    features['count_equals']=url.count('=')

    features['count_digits']=sum(c.isdigit() for c in url)
    features['num_subdomains']=domain.count('.') if domain else (te.subdomain.count('.')+1 if te.subdomain else 0)

    #IP address in hostname
    features['has_ip']=int(bool(re.search(r'(^|//)(\d{1,3}\.){3}\d{1,3}(:\d+)?', url)))

    #shortner detection (hostname or full url)
    host=parsed.netloc.lower()
    features['uses_shortner']=int(any(s in host for s in SHORTENERS) or any(s in url.lower() for s in SHORTENERS))

    #suspicious words in path or query
    low=url.lower()
    features['has_suspicious_word']=int(any(w in low for w in SUSPICIOUS_WORDS))

    #count of toplevel path tokens
    try:
        features['num_path_tokens']=len([p for p in path.split('/') if p])
    except Exception:
        features['num_path_tokens'] = 0

    #basic heuristic features
    features['long_hostname']=int(len(parsed.netloc)>30)
    features['many_digits']=int(features['count_digits']>5)

    return features


if __name__ == "__main__":
    samples = [
        "http://example.com/test",
        "https://bit.ly/xyz",
        "http://192.168.0.1/login",
        "https://www.paypal.com/signin",
    ]
    for u in samples:
        print(extract_url_features(u))


