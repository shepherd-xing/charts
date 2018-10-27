from flask import Flask
from pymongo import MongoClient

class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string = '%%',
        variable_end_string = '%%'
    ))

DEBUG = True

URI = 'mongodb://shepherd:wangxing123@ds031847.mlab.com:31847/cryptocharts'
client = MongoClient(URI)
db = client.cryptocharts
coin_detail = db.coin_detail
coin_info = db.coin_info        #coin的基本信息，symbol，name等
ex_info = db.ex_info            #exchange的基本信息，url， name等
ex_listing = db.ex_listing
ex_content = db.ex_content

APIKEY = '71c79a6d-928a-4400-817d-f2c1d750e925'
headers = {
    'X-CMC_PRO_API_KEY': APIKEY
}
