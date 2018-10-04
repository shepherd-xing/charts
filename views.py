import requests
from models import AssetsIndex

def get_index():
    '''获取索引数据'''
    url = 'https://api.cryptowat.ch/assets'
    response = requests.get(url)
    data = response.json() #所有数据
    allowance = data['allowance']
    result_list = data['result']
