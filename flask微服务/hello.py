# coding=utf-8

from flask import Flask
from flask import request
from toutiao_movie_search_test import *

app = Flask(__name__)

@app.route('/index/spider/toutiao/search/', methods=['GET', 'POST'])
def spider():
    if request.method == 'POST':
        keyword = request.values.get('keyword')
        m = Movie()
        m.movie_page_search(keyword)
        return '您所要搜索的电影名称：{}'.format(keyword)
    else:
        return 'other requests'

if __name__ == '__main__':
    app.run(port=8006,debug=True,host='0.0.0.0')