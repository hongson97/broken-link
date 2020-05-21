import requests
import json
import re
import sys
import itertools
import operator
from urllib.parse import urlparse
from multiprocessing import Pool

template_data_extract = {
    "domain":"",
    "urls":[]
}
def get_source(domain):
    source_text = ""
    req = requests.get(domain)
    if(req.status_code == 200):
        source_text = req.text
    return source_text

def extract_url_3rdparty(content,your_domain):
    reg_ex = """https?://[^\s<>\"]+|www\.[^\s<>\"]+"""

    result_list = []
    list_url = re.findall(reg_ex,content)
    your_domain = urlparse(your_domain).netloc
    for url in list_url:
        url_parsed = urlparse(url)
        domain_3rd_party = url_parsed.scheme + "://"+ url_parsed.netloc
        if(your_domain not in domain_3rd_party and url not in result_list):
            result_list.append((domain_3rd_party,url_parsed.path))

    beautify_3rd_party = []
    it = itertools.groupby(result_list, operator.itemgetter(0))
    for key, subiter in it:
        urls = (list(item[1] for item in subiter))
        data = template_data_extract.copy()
        data["domain"] = key
        data["urls"] = urls
        beautify_3rd_party.append(data)
    return beautify_3rd_party
                

def check_broken_link(url_3rdparty):
    stt_success = ' \033[92m %s \033[0m '
    stt_fail = ' \033[91m %s \033[0m '

    domain = url_3rdparty["domain"]
    list_urls =  url_3rdparty["urls"]

    output = """ """
    try:
        req = requests.get(domain,timeout=10)
        status_code     = (stt_success%str(req.status_code))
        broken_status   = (stt_success%"OK")
        if(req.status_code >= 400):
            status_code     = (stt_fail%str(req.status_code))      
            broken_status   = (stt_fail%"BROKEN")
        result =  status_code  + domain + broken_status + "\n"
    except Exception as e:
        result = (stt_fail%(" [-] Check manual:%s\n"%domain))

    for uri in list_urls:
        if(uri == "" or uri == "/" ):
            continue
        url = domain + uri
        try:
            req = requests.get(url,timeout=10)
            status_code     = (stt_success%str(req.status_code))
            broken_status   = (stt_success%"OK")
            if(req.status_code >= 400):
                status_code     = (stt_fail%str(req.status_code))      
                broken_status   = (stt_fail%"BROKEN")
            result +=  status_code  + url + broken_status + "\n"
        except Exception as e:
            result = (stt_fail%(" [-] Check manual:%s\n"%domain))
    
    print(result)
        
if __name__ == "__main__":
    domain = sys.argv[1]

    print("[+] Checking url broken:" , domain)
    source = get_source(domain)
    list_url_3rd_party = extract_url_3rdparty(source,domain)
    with Pool(10) as p:
        p.map(check_broken_link,list_url_3rd_party)
