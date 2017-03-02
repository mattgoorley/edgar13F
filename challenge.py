from bs4 import BeautifulSoup
import requests
import re
import os
import csv
import sys



class EdgarCrawler:

    def __init__(self):
        self.Wrapper = Wrapper()

    def lookup(self):
        cik_or_ticker = input('Enter CIK number or Ticker Symbol:  ')
        if cik_or_ticker in ['Exit', 'exit', 'quit', 'Quit']:
            return 'Gone'
        filing_form = self.filings_13F(cik_or_ticker)

    def filings_13F(self, cik):

        r = self.Wrapper.browse_edgar(cik, type_='13F-HR')

        data = r.text
        doc = BeautifulSoup(data, 'xml')

        hidden_cik = doc.find('CIK')
        if not hidden_cik:
            print('Incorrect/Invalid. Please try again')
            return self.lookup()

        date_url_pair = {}
        filings = doc.find_all('filing')
        if not filings:
            print('No 13F-HR filings for this fund.')
            return self.lookup()

        for filing in filings:
            filing_type = filing.find('type').string
            date_filed = filing.find('dateFiled').string
            if not date_filed:
                print('No dates to choose from, please try new lookup')
                return self.lookup()

            # Check if ammendment, add A to date
            if filing_type != '13F-HR':
                date_filed = date_filed + 'A'
            print(date_filed)
            link = filing.find('filingHREF').string
            text_url = re.sub(r'-index.html?', '.txt', link)
            date_url_pair[date_filed] = text_url

        date = self.choose_date(date_url_pair)
        if date == None:
            self.lookup()
        go_to_url = date_url_pair[date]


        quarterly_xml = requests.get(go_to_url)
        self.xml_to_tab_delimited_text(quarterly_xml)

        return go_to_url

    def choose_date(self, date_url_pair):
        dates = date_url_pair.keys()
        date = input('Choose date (YYYY-MM-DD):  ')
        if date in ['Exit', 'exit', 'quit', 'Quit', 'back', 'Back']:
            return None
        if date not in dates:
            date = self.choose_date(date_url_pair)
        return date

    def xml_to_tab_delimited_text(self, xml_page):
        data = xml_page.text
        doc = BeautifulSoup(data, 'xml')

        # header = doc.find('form13FFileNumber').string
        info_tables = doc.findAll('infoTable')

        data = []
        cols = []
        for item in info_tables:
            d = {}
            for sub in item.descendants:
                if hasattr(sub, 'name'):
                    d[sub.name] = sub.string
            data.append(d)
            cols = list(d.keys())

        cw = csv.writer(sys.stdout, delimiter = '\t')
        cw.writerow(cols)
        for row in data:
            cw.writerow([row.get(k, 'N/A') for k in cols])

        return self.lookup()


class Wrapper:
    def __init__(self):
        self.base_url = 'https://www.sec.gov/'

    def get(self, path, **kwargs):
        params = kwargs['params']
        path = self.base_url + path

        return requests.get(path, params=params)

    def browse_edgar(self, cik, type_, dateb='', start='0', count='40'):
        params = {
            'action': 'getcompany',
            'CIK': cik,
            'type': type_,
            'dateb': dateb,
            'owner': 'exclude',
            'output': 'xml',
            'start': start,
            'count': count
        }
        return self.get('cgi-bin/browse-edgar', params=params)

    def company_search(self, company, type_):
        params = {
            'action': 'getcompany',
            'company': company,
            'type': type_,
            'owner': 'exclude',
            'Find': 'Search'
        }
        return self.get('cgi-bin/browse-edgar', params=params)
