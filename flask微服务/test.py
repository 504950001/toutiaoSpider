# coding=utf-8

import requests

def test4():
    data = {
        'keyword': '盗梦空间'
    }
    url = 'http://xxx:xx/index/'
    body = requests.post(url,data=data)
    print(body.content.decode())

if __name__ == "__main__":
    test()
