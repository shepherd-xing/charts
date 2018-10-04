from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests, os, re, pprint
from bs4 import BeautifulSoup as bs
from json import loads, dumps
from models import test
from time import time
from crawl import get_coin_detail, read_file, get_all_ex, get_all_coin_data, save_slugs, get_all_coin_detail,\
    write_file
from crawl_coinhills import get_hills_single_data, get_hills_all_data
from pprint import pprint


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string = '%%',
        variable_end_string = '%%'
    ))
app = CustomFlask(__name__)

@app.route('/')
def index():
    listings_api_url = 'https://api.coinmarketcap.com/v2/listings/'
    coin_list_url = 'https://coinmarketcap.com/'
    coin_detail_url = 'https://coinmarketcap.com/currencies/'
    all_coins = get_all_coin_data(coin_list_url, 2)  # 获取2页的所有coin信息，得到由单个coin信息字典组成的列表
    coinhills_url = 'https://www.coinhills.com/api/internal/market_read.php?pri_code={}' \
                    '&sec_code=&src_code=&order=sec_type-desc%2Csec_code-asc%2Cvolume_btc-desc'  # coinhills的url

    # save_slugs(listings_api_url)       #保存slug到json文件

    # get_all_coin_detail(coin_detail_url, all_coins)     #抓取所有coin详细信息
    coin_detail = read_file('coin_detail.json')  # 从文件读取coin详细信息
    hills_data = read_file('formated_hills_data.json')  # 读取coin法币交易信息
    for item in hills_data['BTC']:
        if item['sec_code'] == 'USD':
            print(item['src_code'])

    # 抓取交易所数据
    ex_url = 'https://coinmarketcap.com/rankings/exchanges/reported/'
    exchanges = get_all_ex(ex_url)
    data = {}  # 构造一个字典提供给模板
    data['coins'] = all_coins
    data['ex'] = exchanges
    data['details'] = coin_detail
    data['hills_data'] = hills_data
    #return render_template('main.html', data=data)
    return render_template('index.html')

@app.route('/api/coins')
def show_all_coins():
    #获取coin信息
    listings_api_url = 'https://api.coinmarketcap.com/v2/listings/'     #主要获取slug
    coin_list_url = 'https://coinmarketcap.com/'
    all_coins = get_all_coin_data(coin_list_url, 2)        #获取2页的所有coin信息，得到由单个coin信息字典组成的列表
    coinhills_url = 'https://www.coinhills.com/api/internal/market_read.php?pri_code={}' \
                    '&sec_code=&src_code=&order=sec_type-desc%2Csec_code-asc%2Cvolume_btc-desc'        #coinhills的url

    #save_slugs(listings_api_url)       #保存slug到json文件
    data = {}       #构造一个字典提供给模板
    data['coins'] = all_coins
    #return render_template('main.html', data=data)
    return jsonify(data)
@app.route('/api/coindetail')
def show_coin_detail():
    coin_detail_url = 'https://coinmarketcap.com/currencies/'
    # get_all_coin_detail(coin_detail_url, all_coins)     #抓取cmc所有coin详细信息
    coin_detail = read_file('coin_detail.json')  # 从文件读取coin详细信息
    hills_data = read_file('formated_hills_data.json')  # 读取coin法币交易信息

    data = {}  # 构造一个字典提供给模板
    data['details'] = coin_detail
    data['hills_data'] = hills_data
    return jsonify(data)

@app.route('/api/ex')
def show_all_ex():
    # 抓取交易所数据
    ex_url = 'https://coinmarketcap.com/rankings/exchanges/reported/'
    exchanges = get_all_ex(ex_url)
    data = {}  # 构造一个字典提供给模板
    data['ex'] = exchanges
    return jsonify(data)

@app.route('/stocks')
def show_stocks():
    return render_template('stocks.html')

@app.route('/chart')
def get_chart():
    return render_template('chart.html')

if __name__ == '__main__':
    app.run()
