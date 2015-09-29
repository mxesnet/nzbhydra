import logging
import re

import arrow
from bs4 import BeautifulSoup

from furl import furl

from exceptions import ProviderIllegalSearchException
from nzb_search_result import NzbSearchResult
from search_module import SearchModule

logger = logging.getLogger('root')


# todo: disable for external api or implement nzb downloading because it doesnt have direct nzb links
# also doesn't close its <td> tags which makes it veeeery hard to parse with BS
class Binsearch(SearchModule):
    # TODO init of config which is dynmic with its path

    def __init__(self, provider):
        super(Binsearch, self).__init__(provider)
        self.module = "nzbclub"
        self.name = "NZBClub"

        self.supports_queries = True  # We can only search using queries
        self.needs_queries = True
        self.category_search = False
        # https://www.nzbclub.com/nzbrss.aspx

    @property
    def max_results(self):

        return self.settings.get("max_results", 250)

    def build_base_url(self):
        url = furl(self.query_url).add({"max": "250", "adv_g": self.max_results, "adv_age": 2500, "postdate": "date"})
        return url

    def get_search_urls(self, query, categories=None):
        return [self.build_base_url().add({"q": query}).tostr()]

    def get_showsearch_urls(self, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
        if query is None:
            raise ProviderIllegalSearchException("Attempted to search without a query although this provider only supports query-based searches", self)
        return self.get_search_urls(query, categories)

    def get_moviesearch_urls(self, query, identifier_key, identifier_value, categories):
        if query is None:
            raise ProviderIllegalSearchException("Attempted to search without a query although this provider only supports query-based searches", self)
        return self.get_search_urls(query, categories)

    def process_query_result(self, html):
        entries = []
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find("table", attrs = {'id': 'r2'})
        for tr in table.find_all("tr"):
            entry = NzbSearchResult()
            
                
            title = tr.find('span', attrs = {'class': 's'})
            if not title: 
                continue
            
            entry.guid = tr.find("checkbox", attrs={'type': 'checkbox'})["name"]
            entry.url = "https://www.binsearch.info/fcgi/nzb.fcgi?q=%s" & entry.guid
        
            title = tr.find("span").getText()
            p = re.compile(r'"(.*)\.(rar|nfo|mkv|par2|001|nzb|url|zip|r[0-9]{2})"')
            m = p.search(title)
            if m:
                title = m.group(1)
            entry.title = title
            print(entry.title)
            p = re.compile(r"size: ([0-9]+\.[0-9]+).(GB|MB)")
            description = tr.find_all("span")[1].getText()
            m = p.search(description)
            if not m:
                logger.debug("Unable to find size information in %s" % description)
                continue
            size = float(m.group(1))
            unit = m.group(2)
            if unit == "MB":
                size = size * 1024 * 1024
            else:
                size = size * 1024 * 1024 * 1024
            entry.size = int(size)
            print(size)

            p = re.compile(r"(\d{2}\-\w{3}\-\d{4})")
            m = p.search(tr.getText())
            if m:
                pubdate = arrow.get(m.group(1), '"DD-MMM-YYYY')
                entry.epoch = pubdate.timestamp
                entry.pubdate_utc = str(pubdate)
                entry.age_days = (arrow.utcnow() - pubdate).days
                entry.age_precise = False
                
            entries.append(entry)

        return entries


def get_instance(provider):
    return Binsearch(provider)
