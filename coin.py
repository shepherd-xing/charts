"""爬取信息"""
import requests
from json import loads
from bs4 import BeautifulSoup as bs
from threading import Thread
from time import time, sleep
from pprint import pprint
from config import db, headers
from bson import json_util

def get_coin_api_data(url, num):
    """调用cmc的api得到coin list数据，num表示获取多少条数据"""
    url = url + str(num)
    response = requests.get(url, headers=headers).json()
    data = response['data']
    return (item for item in data)

def get_all_coin_data(url, num, data_base_data):
    """融合api数据和数据库的数据"""
    list1 = []
    for item in get_coin_api_data(url, num):
        obj = {}
        obj['rank'] = item['cmc_rank']
        try:
            obj['icon_src'] = data_base_data[item['symbol']]['icon_src']
            obj['url'] = data_base_data[item['symbol']]['url']
        except KeyError:
            pass
        obj['name'] = item['name']
        obj['symbol'] = item['symbol']
        obj['price'] = item['quote']['USD']['price']
        obj['cap'] = item['quote']['USD']['market_cap']
        obj['change'] = round(item['quote']['USD']['percent_change_24h'], 2)
        obj['id'] = item['id']
        list1.append(obj)
    return list1

def get_rows(url):
    """获取页面上coin列表的信息，每一行表示单个coin的信息，返回一页中所有的coin"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/69.0.3497.100 Safari/537.36',
        'Connection': 'close'
    }
    response = requests.get(url, headers=headers)
    soup = bs(response.text, 'lxml')
    rows = soup.tbody.find_all('tr')  # 得到所有行
    return (row for row in rows)

def get_coin_rows(url, num):
    """获取给定页数的所有的coin信息，返回一个列表，每一行包含单个coin的信息"""
    rows = []
    for i in range(1, num+1):
        url = url + str(i)
        rows = rows + list(get_rows(url))
        url = url.rstrip(str(i))
    return (row for row in rows)

def crawl_all_coin_data(url, num):
    """爬取所有coin的信息，num表示想要获取多少页，返回一个列表，每一项代表单个coin的信息"""
    print('爬取coin列表')
    coin_info = {}      #存入数据库
    last_time = time()
    for row in get_coin_rows(url, num):      #把单个coin的信息汇集到一个字典中
        data = {}
        cols = row.find_all('td')
        data['icon_src'] = cols[1].img.get('data-src') if cols[1].img.get('data-src') else cols[1].img.get('src')
        data['url'] = url.rstrip('/') + cols[1].a.get('href')
        coin_info[cols[1].find_all('a')[0].string] = data
    coin_info['time'] = last_time
    db.coin_info.delete_many({})
    db.coin_info.insert(coin_info)
    coin_info.pop('time')
    coin_info.pop('_id')
    save_details(coin_info)  # 爬取coin详细信息并保存到数据库

def crawl_and_save_coin(url, num):
    """定时爬取coin数据并保存到数据库"""
    while True:
        try:
            last_time = loads(json_util.dumps(db.coin_info.find()))[0]['time']
        except (IndexError, KeyError):
            last_time = time()
            crawl_all_coin_data(url, num)
        now_time = time()
        time_delta = now_time - last_time
        if time_delta > 7200:
            crawl_all_coin_data(url, num)

def get_coin_detail(url):
    """获取单个coin详情页面的信息，url为coin详情页面url"""
    print('爬取coin详细信息~~~~~~')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/69.0.3497.100 Safari/537.36',
        'Connection': 'close'
    }
    response = requests.get(url, headers=headers)
    soup = bs(response.text, 'lxml')
    info = {}
    link_dict = {}
    ul = soup.find(class_='details-panel-item--links')
    li_list = ul.find_all(attrs={'target': '_blank'})
    for li in li_list:
        link_dict[li.string] = li.get('href')
    info['links'] = link_dict
    divs = soup.find_all(class_='details-text-medium')
    supply_dict = {}
    for div in divs:
        header = div.parent.find('h5').string
        supply = div.contents[1].string.strip() + ' ' + div.contents[-1].string.strip()
        supply_dict[header] = supply
    info['supplies'] = supply_dict
    rows = soup.tbody.find_all('tr')
    return info, (row for row in rows)


def loop_detail(coin_info, details, symbols, start, end, length):
    """分段抓取信息，把详细信息和symbol关联起来"""
    for i in range(start, min(end, length)):
        symbol = symbols[i]
        print('symbol:', symbol)
        url = coin_info[symbol]['url']
        details[symbol], rows_gen = get_coin_detail(url)
        trade_info = []
        for row in rows_gen:
            row_info = {}
            cols = row.find_all('td')
            pair = cols[2].string
            if pair.split('/')[1] != symbol:
                row_info['icon_src'] = cols[1].img.get('data-src')
                row_info['ex_name'] = cols[1].a.string
                row_info['pair'] = pair
                row_info['volume'] = cols[3].span.string.strip()
                row_info['price'] = cols[4].span.string.strip()
                trade_info.append(row_info)
        details[symbol]['trade_info'] = trade_info
        sleep(2)

def save_details(coin_info):
    """获取所有的coin的详细信息"""
    symbols = list(coin_info.keys())
    length = len(symbols)
    details = {}
    last_time = time()
    details['time'] = last_time
    s_time = time()
    threads = []
    for i in range(0, length, length):
        thread_obj = Thread(target=loop_detail, args=(coin_info, details, symbols, i, i+length, length))
        threads.append(thread_obj)
        thread_obj.start()
    for th in threads:
        th.join()

    db.coin_detail.delete_many({})
    db.coin_detail.insert(details)  # 保存到数据库
    e_time = time()
    print('抓取coin详细信息花费时间：{}'.format(e_time-s_time))

def get_details():
    """从数据库获取coin详细信息"""
    details = db.coin_detail.find()
    details = loads(json_util.dumps(details))[0]
    details.pop('_id')
    return details

