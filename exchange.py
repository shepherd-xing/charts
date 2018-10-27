import requests
from bs4 import BeautifulSoup as bs
from coin import get_rows
from pprint import pprint
from time import time, sleep
from threading import Thread
from config import db
from json import loads
from bson import json_util

def save_all_ex(ex_url, base_url):
    """爬取交易所信息并保存到数据库"""
    exchanges = []      #安装交易量排名保存所有交易所信息
    ex_info = {}
    ex_listing = {}     #构建一个字典保存排名信息到数据库
    last_time = time()
    for row in get_rows(ex_url):
        ex = {}         #每一个交易所的信息，用于交易所排名
        info = {}       #每一个交易所的信息，用于爬取各个交易所详细信息
        cols = row.find_all('td')
        ex['rank'] = cols[0].string.strip()
        ex['icon_src'] = cols[1].img.get('data-src') if cols[1].img.get('data-src') else cols[1].img.get('src')
        ex['name'] = cols[1].a.string
        ex['volume'] = cols[2].a.string
        ex['pairs'] = cols[5].a.string
        ex['change'] = cols[6].string
        exchanges.append(ex)

        info['rank'] = ex['rank']
        info['icon_src'] = ex['icon_src']
        info['url'] = base_url.rstrip('/') + cols[1].a.get('href')
        ex_info[ex['name'].split('.')[0]] = info
    ex_listing['time'] = last_time
    ex_listing['ex'] = exchanges
    db.ex_listing.delete_many({})
    db.ex_listing.insert(ex_listing)
    save_ex_content(ex_info)  # 爬取交易所详细信息保存到数据库

def loop_ex_listing(ex_url, base_url):
    """定时爬取交易所排名信息"""
    while True:
        try:
            last_time = loads(json_util.dumps(db.ex_listing.find()))[0]['time']
        except (IndexError, KeyError):
            last_time = time()
            save_all_ex(ex_url, base_url)
        now_time = time()
        time_delta = now_time - last_time
        if time_delta > 15000:
            save_all_ex(ex_url, base_url)

def get_all_ex():
    """从数据库获取交易所排名等信息"""
    ex_listing = db.ex_listing.find()
    ex_listing = loads(json_util.dumps(ex_listing))[0]
    ex_listing.pop('_id')
    return ex_listing

def get_ex_info(url):
    """获取单个交易所的信息"""
    print('抓取交易所详细信息')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',
        'Connection': 'close'
    }
    response = requests.get(url, headers=headers)
    soup = bs(response.text, 'lxml')
    ul = soup.find(class_='list-unstyled')
    link_tags = ul.find_all('li')
    links = {}
    for tag in link_tags:
        if tag.a:
            links[tag.span.get('title')] = tag.a.get('href')
    rows = soup.tbody.find_all('tr')
    trade_info = []
    for row in rows:
        info = {}
        cols = row.find_all('td')
        info['icon_src'] = cols[1].img.get('data-src')
        info['coin_name'] = cols[1].a.string
        info['pair'] = cols[2].string
        info['pair_link'] = cols[2].a.get('href')
        info['volume'] = cols[3].span.string.strip()
        info['price'] = cols[4].span.string.strip()
        trade_info.append(info)
    info = {}
    info['links'] = links
    info['trade_info'] = trade_info
    return info

def loop_ex(ex_info, ex_content, ex_names, start, end, length):
    for i in range(start, min(end, length)):
        key = ex_names[i]
        url = ex_info[key]['url']
        ex_content[key] = get_ex_info(url)
        sleep(2)

def save_ex_content(ex_info):
    """获取交易所详情页面信息"""
    threads = []
    ex_content = {}
    s_time = time()
    ex_names = list(ex_info.keys())
    length = len(ex_names)
    for i in range(0, length, length):
        thread_obj = Thread(target=loop_ex, args=(ex_info, ex_content, ex_names, i, i+length, length))
        threads.append(thread_obj)
        thread_obj.start()
    for th in threads:
        th.join()
    db.ex_content.delete_many({})
    db.ex_content.insert(ex_content)
    e_time = time()
    print('抓取交易所详细信息花费时间：{}'.format(e_time-s_time))

def get_ex_content():
    """从数据库获取交易所详情页面信息"""
    ex_content = db.ex_content.find()
    ex_content = loads(json_util.dumps(ex_content))[0]
    ex_content.pop('_id')
    return ex_content