from flask import Flask
from pymongo import MongoClient

class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string = '%%',
        variable_end_string = '%%'
    ))

DEBUG = True

client = MongoClient()
db = client.crypto
coin_detail = db.coin_detail
coin_info = db.coin_info        #coin的基本信息，symbol，name等
slugs = db.slugs
ex_info = db.ex_info            #exchange的基本信息，url， name等
ex_content = db.ex_content