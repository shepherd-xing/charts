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
    return data

def get_all_coin_data(api_data_list, data_base_data):
    """融合api数据和数据库的数据"""
    list1 = []
    for item in api_data_list:
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
    coin_info = {}      #存入数据库
    for row in get_coin_rows(url, num):      #把单个coin的信息汇集到一个字典中
        data = {}
        cols = row.find_all('td')
        data['icon_src'] = cols[1].img.get('data-src') if cols[1].img.get('data-src') else cols[1].img.get('src')
        data['url'] = url.rstrip('/') + cols[1].a.get('href')
        coin_info[cols[1].find_all('a')[0].string] = data

    db.coin_info.delete_many({})
    db.coin_info.insert(coin_info)

def get_coin_detail(url):
    """获取单个coin详情页面的信息，url为coin详情页面url"""
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
        sleep(0.5)

def save_details():
    """获取所有的coin的详细信息"""
    coin_info = db.coin_info.find()
    coin_info = loads(json_util.dumps(coin_info))[0]
    coin_info.pop('_id')
    symbols = list(coin_info.keys())
    length = len(symbols)
    details = {}
    last_time = time()
    details['time'] = last_time
    s_time = time()
    threads = []
    for i in range(0, length, 60):
        thread_obj = Thread(target=loop_detail, args=(coin_info, details, symbols, i, i+60, length))
        threads.append(thread_obj)
        thread_obj.start()
    for th in threads:
        th.join()

    db.coin_detail.delete_many({})
    db.coin_detail.insert(details)  # 保存到数据库
    e_time = time()
    print('抓取coin详细信息花费时间：{}'.format(e_time-s_time))
    return details

def get_details():
    """从数据库获取coin详细信息"""
    details = db.coin_detail.find()
    details = loads(json_util.dumps(details))[0]
    details.pop('_id')
    return details

def timer(get_func, save_func):
    """判断何时抓取数据并存入数据库"""
    last_time = time()
    now_time = time()
    flag = False
    try:
        details = get_func()
        last_time = details['time']
    except IndexError:
        flag = True
    time_delta = now_time - last_time
    print('获取数据相隔时间：{}'.format(time_delta))
    if flag or time_delta > 10000:
        save_func()
        print('保存数据到数据库')

