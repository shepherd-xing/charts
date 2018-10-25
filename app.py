from flask import render_template, jsonify
from coin import crawl_all_coin_data, save_details, get_details, timer, get_coin_api_data, get_all_coin_data
from exchange import get_all_ex, save_ex_content, get_ex_content
from pprint import pprint
from config import DEBUG, CustomFlask, db, headers
from json import loads
from bson import json_util


app = CustomFlask(__name__)


base_url = 'https://coinmarketcap.com/'
ex_url = 'https://coinmarketcap.com/rankings/exchanges/reported/'
api_coin_list_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?sort=market_cap&start=1&limit='

crawl_all_coin_data(base_url, 2)    #获取2页的所有coin信息，得到由单个coin信息字典组成的列表

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/coins')
def show_all_coins():
    #获取coin信息
    db_data = db.coin_info.find()     #从数据库获取数据
    db_data = loads(json_util.dumps(db_data))[0]
    db_data.pop('_id')
    api_data = get_coin_api_data(api_coin_list_url, 200)     #从api获取数据， 获取200条数据
    all_coins = get_all_coin_data(api_data, db_data)
    data = {}
    data['coins'] = all_coins
    return jsonify(data)
@app.route('/api/coindetail')
def show_coin_detail():
    timer(get_details, save_details)     #抓取详情页面信息，保存到数据库
    details = get_details()         #从数据库取得coin详细信息
    data = {}
    data['details'] = details
    return jsonify(data)

@app.route('/api/ex')
def show_all_ex():
    # 抓取交易所数据
    exchanges = get_all_ex(ex_url, base_url)
    data = {}
    data['ex'] = exchanges
    return jsonify(data)

@app.route('/api/exinfo')
def show_ex_info():
    timer(get_ex_content, save_ex_content)        #抓取交易所详情页面信息存入数据库
    ex_content = get_ex_content()       #从数据库获取交易所详细信息
    data = {}
    data['ex_content'] = ex_content
    return jsonify(data)

@app.route('/stocks')
def show_stocks():
    return render_template('stocks.html')

@app.route('/chart')
def get_chart():
    return render_template('chart.html')

if __name__ == '__main__':
    app.run(debug=DEBUG)
