"""爬取信息"""
import requests, os
from json import loads, dumps
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
from threading import Thread
from time import time
from multiprocessing import Pool


def get_rows(url):
    """获取页面上coin列表的信息，每一行表示单个coin的信息，返回一页中所有的coin"""
    html = requests.get(url).text
    soup = bs(html, 'lxml')
    rows = soup.tbody.find_all('tr')  # 得到所有行
    return rows

def get_coin_rows(url, num):
    """获取给定页数的所有的coin信息，返回一个列表，每一行包含单个coin的信息"""
    coin_rows = []
    for i in range(1, num+1):
        url = url + str(i)
        coin_rows = coin_rows + get_rows(url)
        url = url.rstrip(str(i))
    return coin_rows

def get_img_srcs(list, num):
    """获取icon的地址，num表示第几列"""
    list1 = []
    for row in list:
        cols = row.find_all('td')
        if cols[num-1].img.get('data-src'):
            list1.append(cols[num-1].img.get('data-src'))
        else:
            list1.append(cols[num-1].img.get('src'))

    return list1

def get_all_coin_data(url, num):
    """获取所有coin的信息，num表示想要获取多少页，返回一个列表，每一项代表单个coin的信息"""
    list = get_coin_rows(url, num)  # 获取两页数据 ，得到200行
    coins = [{} for i in range(len(list))]     #构造一个列表
    coin_icon_srcs = get_img_srcs(list, 2)  # 得到所有icon的地址，icon在第2列
    for row in list:      #把单个coin的信息汇集到一个字典中
        coin_info = {}
        i = list.index(row)
        cols = row.find_all('td')
        coin_info['rank'] = cols[0].string.strip()
        coin_info['src'] = coin_icon_srcs[i]
        coin_info['symbol'] = cols[1].find_all('a')[0].string
        coin_info['name'] = cols[1].find_all('a')[1].string
        coin_info['cap'] = cols[2].string.strip()
        coin_info['price'] = cols[3].a.string
        coin_info['change'] = cols[6].string
        coins[i] = coin_info
    return coins

def save_slugs(url):
    """调用api，获取coin概要信息，主要用来获取coin的slug信息，并保存到本地文件"""
    response = requests.get(url).json()
    listings = response['data']
    slug_dict = {}
    for i in range(len(listings)):
        slug_dict[listings[i]['symbol']] = listings[i]['website_slug']
    write_file(slug_dict, 'slugs.json')

def get_coin_detail(url):
    """获取单个coin详情页面的信息，url为coin详情页面url"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,
        }
    }
    chrome_options.add_experimental_option('prefs', prefs)
    #chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(url)
    link_dict = {}      #构造存放链接的字典
    html = driver.page_source
    soup = bs(html, 'lxml')
    ul = soup.find(class_='details-panel-item--links')
    lis = ul.find_all(attrs={'target': '_blank'})
    for li in lis:
        link_dict[li.string] = li.get('href')
    divs = soup.find_all(class_='details-text-medium')
    suply_dict = {}
    for div in divs:
        header = div.parent.find('h5').string
        suply = div.contents[1].string + ' ' + div.contents[-1].string.strip()
        suply_dict[header] = suply
    return link_dict, suply_dict
def get_all_coin_detail(url, list):
    """获取所有coin的详情，并保存到本地，list为所有的coin列表，texts为要查找的文本列表"""
    slug_dict = read_file('slugs.json')     #读取slug
    s_time = time()
    length = len(list)
    detail_dict = {}
    threads = []
    for i in range(0, length, 55):
        thread_obj = Thread(target=loop_data, args=(url, slug_dict, list, i, i+55, detail_dict))
        threads.append(thread_obj)
        thread_obj.start()
    for th in threads:
        th.join()
    e_time = time()
    print('运行时间：{}'.format(e_time-s_time))
    print(detail_dict.get('BTC'))
    #write_file(detail_dict, 'coin_detail.json')        #写到本地文件
    return detail_dict
def loop_data(url, slug_dict, list, start, end, detail_dict):
    length = len(list)
    for i in range(start, min(end, length)):
        coin_info = {}
        symbol = list[i]['symbol']
        slug = slug_dict.get(symbol)
        url = url + slug        #构造单个coin详情页面的url
        print(symbol, ': ', url)
        link_dict, suply_dict = get_coin_detail(url)
        url = url[0:(-len(slug))]
        coin_info['links'] = link_dict
        coin_info['supplies'] = suply_dict
        detail_dict[symbol] = coin_info
        #print(symbol, ': ', detail_dict[symbol])
    #return detail_dict

def write_file(data, name):
    """把下载的数据存储到本地文件"""
    path = os.getcwd()       #当前工作目录
    path = os.path.join(path, 'data', name)
    with open(path, 'w') as f:
        f.write(dumps(data))
        print('写入文件中......')

def read_file(name):
    """读取文件"""
    path = os.getcwd()
    path = os.path.join(path, 'data', name)
    with open(path) as f:
        content = loads(f.read())
    return content

def get_all_ex(url):
    ex_rows = get_rows(url)
    ex_srcs = get_img_srcs(ex_rows, 2)
    exchanges = [{} for i in range(100)]        #单个交易所信息组成的列表
    for row in ex_rows:
        ex = {}
        i = ex_rows.index(row)
        cols = row.find_all('td')
        ex['rank'] = cols[0].string.strip()
        ex['src'] = ex_srcs[i]
        ex['name'] = cols[1].a.string
        ex['volume'] = cols[2].a.string
        ex['pairs'] = cols[5].a.string
        ex['change'] = cols[6].string
        exchanges[i] = ex
    return exchanges