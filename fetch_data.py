#-*- coding: utf-8 -*-
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import datetime
import argparse
import numpy as np
from collections import defaultdict

gd_city = ["广州", "深圳", "清远", "韶关", "河源", \
        "梅州", "潮州", "肇庆", "云浮", "佛山", "东莞", \
        "惠州", "汕尾", "揭阳", "汕头", "湛江", \
        "茂名", "阳江", "江门", "中山", "珠海"]
gd_city = set(gd_city)

def sentence_split(lines):
    for line in lines:
        for sen in line.split("。"):
            yield sen

class GdData(object):
    """DataFetcher for Guangdong Province
    """
    def __init__(self, url="http://wsjkw.gd.gov.cn/zwyw_yqxx/"):
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
        pattern = re.compile(r"\d*年\d*月\d*日广东省新型冠状病毒感染的肺炎疫情情况")
        url_list = []
        count = 1
        page = "index.html"
        while True:
            html = requests.get(url + page)
            flag = False
            for line in html.text.split('\n'):
                line = line.strip()
                ret = pattern.search(line, re.S)
                if ret is not None:
                    flag = True
                    href = re.search(r"href=\"(.*?)\"", line)
                    href = href.group(1)
                    date = re.search(r"(\d*)年(\d*)月(\d*)日", line)
                    year = int(date.group(1))
                    month = int(date.group(2))
                    day = int(date.group(3))
                    date = datetime.date(year=year, month=month, day=day)
                    date = date - datetime.timedelta(days=1)
                    url_list.append((href, date))

            if not flag:
                break
            else:
                count += 1
                page = "index_%s.html" % count
        return url_list

    def fetch_daily_pages(self, url_list):
        citys = []
        delta_confirmeds = []
        dates = []
        city_confirmeds = defaultdict(lambda : 0)
        confirmeds = []
        for url, date in url_list[::-1]:
            for city, confirmed in self.fetch_daily_page(url):
                citys.append(city)
                delta_confirmeds.append(confirmed - city_confirmeds[city])
                city_confirmeds[city] = confirmed
                confirmeds.append(city_confirmeds[city])
                dates.append(date)
        data_frame = pd.DataFrame(data={"city": citys, "confirmed": confirmeds, "delta_confrimed": delta_confirmeds, "date": dates})
        return data_frame

    def fetch_daily_page(self, url):
        html = requests.get(url)
        soup = BeautifulSoup(html.text, features="html.parser")
        city_confirmed = defaultdict(lambda : 0)
        mode = ""
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            for line in sentence_split(text.split("\n")):
                if re.search(r"新增", line) is not None:
                    mode = "delta"
                elif re.search(r"累计", line) is not None:
                    mode = "acc"

                if re.search(r"确诊", line) is not None:
                    rets = re.findall(r"(..)市?(\d+)例", line)
                    for city, confirmed in rets:
                        if city not in gd_city:
                            continue
                        confirmed = int(confirmed)
                        if mode == 'acc':
                            city_confirmed[city] = max(city_confirmed[city], confirmed)
        return list(city_confirmed.items())

    def view_city(self, city):
        return self.data_frame[self.data_frame.city == city]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Estimate R0 2019-ncov')
    parser.add_argument('--city', type=str, default="广州",
                        help='input a city in Guangdong Province')
    args = parser.parse_args()

    data = GdData()
    print(data.view_city(args.city))
