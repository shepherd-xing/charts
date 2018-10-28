from flask import render_template, jsonify
from coin import crawl_and_save_coin, get_details, get_all_coin_data
from exchange import get_all_ex, get_ex_content, loop_ex_listing
from pprint import pprint
from config import DEBUG, CustomFlask, db
from json import loads
from bson import json_util
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(2)
app = CustomFlask(__name__)


base_url = 'https://coinmarketcap.com/'
ex_url = 'https://coinmarketcap.com/rankings/exchanges/reported/'
api_coin_list_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest' \
                    '?sort=market_cap&start=1&limit='


@app.route('/')
def index():
    executor.submit(loop_ex_listing, ex_url, base_url)      #定时爬取交易所信息保存到数据库
    executor.submit(crawl_and_save_coin, base_url, 2)            #定时爬取coin信息并保存到数据库
    return render_template('index.html')

@app.route('/api/coins')
def show_all_coins():
    #获取coin信息
    all_coins = {}
    try:
        db_data = db.coin_info.find()     #从数据库获取数据
        db_data = loads(json_util.dumps(db_data))[0]
        db_data.pop('_id')
        all_coins = get_all_coin_data(api_coin_list_url, 200, db_data)
    except IndexError:
        print('数据库还没有数据')
    data = {}
    data['coins'] = all_coins
    return jsonify(data)

@app.route('/api/coins/<symbol>')
def show_coin(symbol):
    details = get_details()  # 从数据库取得coin详细信息
    detail = details[symbol]
    data = {}
    data['detail'] = detail
    return jsonify(data)

@app.route('/api/ex')
def show_all_ex():
    data = get_all_ex()
    return jsonify(data)

@app.route('/api/ex/<name>')
def show_ex(name):
    ex_infos = get_ex_content()  # 从数据库获取交易所详细信息
    ex_info = ex_infos[name]
    data = {}
    data['ex_info'] = ex_info
    return jsonify(data)

@app.route('/stocks')
def show_stocks():
    return render_template('stocks.html')

@app.route('/chart')
def get_chart():
    return render_template('chart.html')

if __name__ == '__main__':
    app.run(debug=DEBUG)
