# -*- coding:utf-8 -*-

import requests
import time
from urllib.parse import urlencode
import json
import hashlib
import re
from bs4 import BeautifulSoup
import math
import random
import sys
from threading import Thread
import redis
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from media import *

#设置递归深度
sys.setrecursionlimit(100000)
#禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

'''
今日头条号主文章列表抓取、文章内容抓取
'''

class Toutiao(object):
    def __init__(self):
        self.redis_cli = redis.Redis(host='xxx', port=6379, db=1, password='xxx',charset='utf8', decode_responses=True)
        self.n = 0
        self.start_time = int(time.time())
        self.end_time = 1544612400 #2018-12-12 19:00:00
        self.next_over_time = 0
        self.max_behot_time = 0
        self.count = 0 #IP失效次数

    #获取AS、CP值
    def get_ascp(self):
        t = int(math.floor(time.time()))
        e = hex(t).upper()[2:]
        m = hashlib.md5()
        m.update(str(t).encode(encoding='utf-8'))
        i = m.hexdigest().upper()

        if len(e) != 8:
            AS = "479BB4B7254C150"
            CP = "7E0AC8874BB0985"
            return AS, CP
        n = i[0:5]
        a = i[-5:]
        s = ''
        r = ''
        for o in range(5):
            s += n[o] + e[o]
            r += e[o + 3] + a[o]
        AS = 'A1' + s + e[-3:]
        CP = e[0:3] + r + 'E1'
        return AS, CP

    #获取号主列表详情页
    def get_page_list(self,uid, mid, max_behot_time, channel_id):
        AS,CP = self.get_ascp()
        uid = int(uid)
        mid = int(mid)
        param_data = {
            'max_behot_time': max_behot_time,
            'media_id': mid,
            'uid': uid,
            'page_type': '1',
            'count': '20',
            'version': '2',
            'output': 'json',
            'is_json': '1',
            'from': 'user_profile_app',
            'as': AS,
            'cp': CP,
        }

        headers = {
            'authority': 'www.toutiao.com',
            'method': 'GET',
            'path': '/pgc/ma/?page_type=1&max_behot_time={}&uid={}&media_id={}&output=json&is_json=1&count=20&from=user_profile_app&version=2&as={}&cp={}&callback=jsonp3'.format(max_behot_time, uid, mid, AS, CP),
            'scheme': 'https',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': 'WEATHER_CITY=%E5%8C%97%E4%BA%AC; UM_distinctid=164f2e4566c8ed-0693c7885b105c-54103515-1fa400-164f2e4566d748; csrftoken=6d0fdf3691ff6e4ac1575d100ac867a3; uuid="w:29a5d9e754344060a20a90082ceb4599"; login_flag=d461fb3548072626676113b9bbf54942; sessionid=8eb83236138f04903d93d277c1a02e99; sid_tt=8eb83236138f04903d93d277c1a02e99; tt_webid=75434708680; tt_webid=75434708680; uid_tt=ff2345fc8b853b31a0a4080dc2b95d6e; sso_login_status=1; sid_guard="8eb83236138f04903d93d277c1a02e99|1533096712|15552000|Mon\054 28-Jan-2019 04:11:52 GMT"; __utma=24953151.1361631348.1533097169.1533097169.1533097169.1; __utmc=24953151; __utmz=24953151.1533097169.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _ba=BA0.2-20180801-51234-IzEK6feRUqnELW5bhqGi; __tasessionId=tmav31gev1533109967006; cp={}; CNZZDATA1259612802=481932984-1533078471-https%253A%252F%252Fwww.baidu.com%252F%7C1533105485'.format(CP),
            'referer': 'https://m.toutiao.com/profile/{}/'.format(uid),
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Mobile Safari/537.36',
            #'user-agent': self.UserAgent.random,
        }
        start_url = 'https://www.toutiao.com/pgc/ma/?' + urlencode(param_data)
        ip = self.redis_cli.srandmember('IP') #代理池获取ip
        if ip == 'None':
            ip = self.redis_cli.srandmember('IP')
        proxies = {
            "https": "https://{}".format(ip),
        }

        time.sleep(random.randint(1, 2) / 4)
        try:
            response = requests.get(start_url, headers=headers, proxies=proxies, timeout=3, verify=False)
            data = response.json()['data']
            self.parse_page_list(data, uid, mid, channel_id)
        except Exception as e:
            if self.count < 2:
                self.count += 1
                self.redis_cli.srem("IP", ip)
                self.get_page_list(uid=uid, mid=mid, max_behot_time=max_behot_time, channel_id=channel_id)
                time.sleep(random.randint(1, 2) / 4)
            else:
                return

    #解析号主列表详情页
    def parse_page_list(self, data_list, uid, media_id, channel_id):
        now1 = 0
        for data in data_list:
            #当前请求Unix时间戳
            mt = int(time.time())
            #API签名字符串
            para = 'xxx' + 'xxx' + str(mt)
            sign = hashlib.md5(para.encode(encoding='UTF-8')).hexdigest()
            #媒体ID(即用户ID)
            mid = uid
            #频道ID
            channel_id = int(channel_id)
            #文章URL
            url = data['source_url']
            #文章标题
            title = data['title']
            #文章描述
            try:
                describe = data['abstract']
            except:
                describe = ''
            #文章图片json格式字符串
            try:
                # 小图
                img_url = json.dumps([url_list['url'] for url_list in data['thumb_image']])
            except:
                img_url = '[]'
            try:
                #大图
                large_img_url = json.dumps([url_list['url'] for url_list in data['image_detail']])
            except:
                large_img_url = '[]'
            #媒体号名称（文章作者名称）
            author = data['source']
            #文章阅读数
            try:
                read_count = data['total_read_count']
            except:
                # 站外阅读数
                try:
                    external = data2['external_visit_count']
                except:
                    external = 0
                # 站内阅读数
                try:
                    internal = data2['internal_visit_count']
                except:
                    internal = 0
                read_count = external + internal
            #文章评论数
            try:
                comment_count = data['comment_count']
            except:
                comment_count = 0
            #发布时间 Unix时间戳
            try:
                publish_time = data['publish_time']
            except:
                publish_time = data['create_time']

            pattern = re.compile(r'\d+')
            cid = re.findall(pattern, url)[0]

            try:
                if data['has_video']:
                    content = '["视频"]'
                elif data['has_gallery']:
                    content = '["图集"]'
                else:
                    content = self.get_content(cid)
            except:
                content = self.get_content(cid)

            now1 = data['behot_time']

            if self.end_time == 0:
                end_time = 1544612400  #2018-12-12 19:00:00
            else:
                end_time = self.end_time
            if int(now1) < end_time:  # 指定时间戳(抓取文章停止时间)
                return
            else:
                pass

            if len(content) > 20:
                items = {
                    'mt': mt,
                    'sign': sign,
                    'mid': mid,
                    'channel_id': channel_id,
                    'url': url,
                    'title': title,
                    'describe': describe,
                    'img_url': img_url,
                    'author': author,
                    'read_count': read_count,
                    'comment_count': comment_count,
                    'publish_time': publish_time,
                    'content': content
                }
                #文章信息存储
                try:
                    url = 'http://xxx/index/spider/toutiao'
                    requests.post(url, data=items)
                except Exception as e:
                    url = 'http://xxx/index/spider/toutiao'
                    requests.post(url, data=items)
                    print('insert wrong!!!!',e)
            else:
                pass

        else:
            self.get_page_list(uid, media_id, now1, channel_id)

    #文章内容抓取
    def get_content(self, cid):
        url = "http://a6.pstatp.com/article/content/lite/14/1/{}/{}/1/".format(cid, cid)
        print(url)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36'
        }

        try:
            response = requests.get(url=url, headers=headers)
            con = response.json()['data']['content']
            if con == '该内容已删除':
                content = '[]'
            else:
                r = re.sub(r'zip_src_path=".*?"', '', con)
                soup = BeautifulSoup(r,'lxml')
                content = str(soup.select("article")[0])
        except:
            content = '[]'

        return content

    def run(self):
        flag = 1
        while flag:
            self.count = 0
            #获取当前时间戳
            now = int(time.time())

            data = self.redis_cli.rpop('spider_toutiao_user')
            data = eval(data) #str转成dict

            uid = data['openid']
            mid = data['toutiao_mid']
            channel_id = data['channel_id']
            #本次访问的断点
            self.end_time = data['next_time']
            stop_time = self.end_time

            try:
                self.get_page_list(uid,mid,now,channel_id)
                item = {}
                item['next_time'] = now
                item['openid'] = uid
                item['toutiao_mid'] = mid
                item['channel_id'] = channel_id
                self.redis_cli.lpush('spider_toutiao_user', str(item))
            except:
                continue

            if stop_time > 1544835600:  #启动爬虫的前一秒(每次启动时需要手动输入）
                flag = 0

if __name__ == "__main__":
    for i in range(5):
        t = Toutiao()
        work_thread = Thread(target=t.run)
        work_thread.start()
