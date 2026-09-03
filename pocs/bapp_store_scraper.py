import re
import time
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

BApp_URL = "https://portswigger.net/bappstore"
awesome_extension_url = "https://github.com/snoopysecurity/awesome-burp-extensions/blob/master/README.md"
awesome_burp_list = []
bapp_store_list = []

def _get_soup(url):
    """
    Sends a request to a provided URL and returns beautiful soup parsed content
    """
    response = requests.get(url)
    return BeautifulSoup(response.content, "html.parser")


def awesome_burp_list_parse():
    print "[+] Fetching Extension List from Awesome Burp Extensions List"
    soup = _get_soup(awesome_extension_url)
    awesome_burp_list_titles = ["scanners","custom-features","beautifiers-and-decoders","cloud-security","scripting","oauth-and-sso","information-gathering","vulnerability-specific-extensions","cross-site-scripting","server-side-request-forgery","broken-access-control","cross-site-request-forgery","deserialization","sensitive-data-exposure","sql-injection","xxe","insecure-file-uploads","directory-traversal","session-management","command-injection","template-injection","web-application-firewall-evasion","logging-and-notes","payload-generators-and-fuzzers","cryptography","web-services","tool-integration","misc"]
    for list_heading in awesome_burp_list_titles:
      for url_heading in soup.find_all("a", {"id": "user-content-" + str(list_heading)}):
        tbl = url_heading.find_next("ul")
        for link in tbl.findAll('a'):
          awesome_burp_list.append(link.text)

def bapp_store_scrape():
    print "[+] Fetching Extension List from PortSwigger BApp Store"
    soup = _get_soup(BApp_URL)
    for url_heading in soup.find_all("a", {"class": "bapp-label"}):
      bapp_store_list.append(url_heading.text)

def main():
    awesome_burp_list_parse()
    bapp_store_scrape()
    extension_result = set(bapp_store_list) - set(awesome_burp_list)
    print '[+] List of extensions missing from Awesome Burp Extension List'
    print sorted(extension_result)





if __name__ == "__main__":
    main()
