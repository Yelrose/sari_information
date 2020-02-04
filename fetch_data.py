#-*- coding: utf-8 -*-
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
import datetime

class GdData(object):
    """DataFetcher for Guangdong Province
    """
    def __init__(self, url="http://wsjkw.gd.gov.cn/zwyw_yqxx/index.html"):
        self.url = url
        url_list = self.fetch_daily_page_list(self.url)
        self.data_frame = self.fetch_daily_pages(url_list)

    def fetch_daily_page_list(self, url):
        """
            Args:
                url: cdc information pages

            Return:
                list of tuple [(url, date) ]
        """
        html = requests.get(url)
        pattern = re.compile(r"\d*年\d*月\d*日广东省新型冠状病毒感染的肺炎疫情情况")
        url_list = []
        for line in html.text.split('\n'):
            line = line.strip()
            ret = pattern.search(line, re.S)
            if ret is not None:
                href = re.search(r"href=\"(.*?)\"", line)
                href = href.group(1)
                date = re.search(r"(\d*)年(\d*)月(\d*)日", line)
                year = int(date.group(1))
                month = int(date.group(2))
                day = int(date.group(3))
                date = datetime.date(year=year, month=month, day=day)
                date = date - datetime.timedelta(days=1)
                url_list.append((href, date))
        return url_list

    def fetch_daily_pages(self, url_list):
        citys = []
        confirmeds = []
        dates = []
        for url, date in url_list[::-1]:
            for city, confirmed in self.fetch_daily_page(url):
                citys.append(city)
                confirmeds.append(confirmed)
                dates.append(date)
        data_frame = pd.DataFrame(data={"city": citys, "confrimed": confirmeds, "date": dates})
        return data_frame

    def fetch_daily_page(self, url):
        html = requests.get(url)
        soup = BeautifulSoup(html.text)
        city_confirmed = []
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if re.search(r"新增", text) is not None:
                rets = re.findall(r"(..)市(\d*)例", text)
                for city, confirmed in rets:
                    confirmed = int(confirmed)
                    city_confirmed.append((city, confirmed))
        return city_confirmed

    def city(self, city):
        return self.data_frame[self.data_frame.city == city]

if __name__ == '__main__':
    data = GdData()
    print(data.city("广州"))
