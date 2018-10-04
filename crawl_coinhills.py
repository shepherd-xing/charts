import requests, os
from bs4 import BeautifulSoup as bs
from pprint import pprint
from threading import Thread
from time import time, sleep


def get_hills_single_data(url, symbol):
    headers = {
        #'Connection': 'close',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/69.0.3497.100 Safari/537.36',
    }
    url = url.format(symbol)
    res = requests.get(url, headers=headers).json()
    data = []
    if res['success']:
        data = res['data']      #这是一个字典列表
    return data
#url = 'https://www.coinhills.com/api/internal/market_read.php?pri_code={}&sec_code=&src_code=&order=sec_type-desc%2Csec_code-asc%2Cvolume_btc-desc'

def get_hills_all_data(url, symbols):
    data = {}
    start = time()
    for symbol in symbols:
        print(symbol)
        get_hills_single_data(url, symbol)
        #single_data = get_hills_single_data(url, symbol)
        #data[symbol] = single_data
        sleep(2)
    end = time()
    print('花费时间：{}'.format(end-start))
    return data