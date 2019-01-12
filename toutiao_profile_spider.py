# -*- coding:utf-8 -*-

import requests
from urllib.parse import urlencode
import sys
import time
import random
import json
import hashlib
import re
import redis
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from threading import Thread
from requests.packages.urllib3.exceptions import InsecureRequestWarning

#设置递归深度
sys.setrecursionlimit(100000)
#禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

'''
今日头条文章列表内容抓取,通过动态接口抓取
'''

class Toutiao(object):
    def __init__(self):
        self.n = 1
        self.count = 0
        self.end_time = 1
        self.max_cursor = 0
        self.redis_cli = redis.Redis(host='xxx', port=6379, db=0, password='xxx', charset='utf8', decode_responses=True)

        #获取号主列表详情页
    def get_page_list(self, uid, max_cursor, channel_id, mid):
        uid = int(uid)
        param_data = {
            'user_id': uid,
            'max_cursor': max_cursor,
        }
        headers = {
            'Host': 'i.snssdk.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://m.toutiao.com/profile/{}/'.format(uid),
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            #'Cookie': '_ga=GA1.2.1963582806.1544610567; odin_tt=26b222ab97fc241a74ddd23d695ddb42d9d3fce087b7bb4259fcda7ce53f15eae51bb191b3d9ba872cb516ac18ed1008; __utma=17725537.1963582806.1544610567.1544878375.1544878375.1; __utmc=17725537; __utmz=17725537.1544878375.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)'
        }
        start_url = 'https://i.snssdk.com/dongtai/list/v9/?' + urlencode(param_data)
        try:
            response = requests.get(start_url, timeout=3, headers=headers, verify=False)
            data = response.json()['data']
            time.sleep(random.randint(1, 2) / 4)
            self.parse_page_list(data, uid, channel_id, mid)
        except Exception as e:
            print('something is wrong!!!',e)
            return

    # 解析号主列表详情页
    def parse_page_list(self, data_list, uid, channel_id, mid):
        max_cursor = 0
        end_time = self.end_time
        data_info = data_list['data']
        if len(data_info) == 0:
            return
        for data in data_info:
            #当前请求Unix时间戳
            mt = int(time.time())
            #API签名字符串
            para = 'xxx' + 'xxx' + str(mt)
            sign = hashlib.md5(para.encode(encoding='UTF-8')).hexdigest()
            #媒体ID(即掘金资讯用户ID)
            mid = mid
            #频道ID
            channel_id = int(channel_id)
            #文章URL
            try:
                url = data['share_url']
            except:
                url = ''
            try:
                title = data['group']['title']
                item_id = data['group']['item_id']
                group_id = data['group']['group_id']
            except:
                title = ''
                item_id = 0
                group_id = 0
            #媒体号名称（文章作者名称）
            try:
                author = data['user']['screen_name']
            except:
                author = ''
            #文章阅读数
            try:
                read_count = data['read_count']
            except:
                read_count = 0
            #文章评论数
            try:
                comment_count = data['comment_count']
            except:
                comment_count = 0
            #发布时间 Unix时间戳
            try:
                publish_time = data['create_time']
            except:
                publish_time = int(time.time())

            #停止时间点
            if publish_time < end_time:
                return

            try:
                content = data['content']
            except:
                content = ''

            # 文章内容等其他信息抓取
            if content == '发布了文章':
                item = self.get_content(item_id)

                try:
                    content_info = item['content']
                    soup = BeautifulSoup(content_info, 'lxml').get_text().strip()
                    content_lengh = len(soup)
                except:
                    content_lengh = 0

                if content_lengh > 20:
                    items = {
                        'mt': mt,
                        'sign': sign,
                        'mid': mid,
                        'channel_id': channel_id,
                        'url': url,
                        'title': title,
                        'describe': item['describe'],
                        'img_url': item['img_url'],
                        'large_img_url': item['large_img_url'],
                        'author': author,
                        'read_count': read_count,
                        'comment_count': comment_count,
                        'publish_time': publish_time,
                        'content': item['content']
                    }

                    #文章信息存储
                    try:
                        url = 'http:xxx/spider/toutiao'
                        requests.post(url, data=items)
                        time.sleep(0.001)
                        jjb_url = 'http:xxx/spider/toutiao'
                        requests.post(jjb_url, data=items)
                        print('ok!!!!')
                    except Exception as e:
                        print('insert wrong!!!!', e)

                    if comment_count > 0:
                        offset = 0
                        self.get_comment(item_id,group_id,offset)
                    else:
                        save_time = int(time.time())
                        cid = {'item_id': item_id, 'group_id': group_id, 'save_time': save_time}
                        self.redis_cli.sadd('spider_toutiao_comment_zero_id', str(cid))
                else:
                    pass

            max_cursor = data_list['max_cursor']
        else:
            self.get_page_list(uid, max_cursor, channel_id, mid)

    def get_content(self, cid):
        url = "http://a6.pstatp.com/article/content/lite/14/1/{}/{}/1/".format(cid, cid)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36'
        }
        try:
            response = requests.get(url=url, headers=headers)
            resp = response.json()['data']
            con = resp['content']
            time.sleep(0.01)
            if con == '该内容已删除':
                content = '[]'
            else:
                content = str(con)
                content = content.strip()
        except:
            content = '[]'
        try:
            #小图
            img_url = json.dumps([url_list['url'] for url_list in resp['thumb_image']])
        except:
            img_url = '[]'
        try:
            # 大图
            large_img_url = json.dumps([url_list['url'] for url_list in resp['image_detail']])
        except:
            large_img_url = '[]'
        #文章描述
        try:
            r = re.sub(r'zip_src_path=".*?"', '', con)
            soup = BeautifulSoup(r, 'lxml')
            soup2 = str(soup.select("article")[0])
            desc_con = BeautifulSoup(soup2, 'lxml')
            desc_text = str(desc_con.select('p')[0].get_text())
            describe = desc_text.split('。')[0]
            if len(describe) == 0:
                describe = desc_text.split('。')[1]
        except:
            describe = ''

        item = {
            'img_url': img_url,
            'large_img_url': large_img_url,
            'describe': describe,
            'content': content
        }

        return item

    def run(self):
        while True:
            self.count = 0
            #获取当前时间戳
            now = time.time()

            data = self.redis_cli.rpop('spider_toutiao_user')
            print(type(data), data)
            data = eval(str(data))  # str转成dict

            uid = data['openid']
            #掘金咨询媒体ID
            mid = data['mid']
            toutiao_mid = data['toutiao_mid']
            channel_id = data['channel_id']
            #本次访问的断点
            self.end_time = data['next_time']
            base_time = 1545208554
            stop_time = self.end_time
            space_time = int(now) - stop_time

            try:
                self.get_page_list(uid, now, channel_id,mid)
                item = {}
                item['next_time'] = int(now)
                item['openid'] = uid
                item['mid'] = mid
                item['toutiao_mid'] = toutiao_mid
                item['channel_id'] = channel_id
                self.redis_cli.lpush('spider_toutiao_user', str(item))
            except:
                continue

            if base_time < stop_time and space_time < 3600:
                time.sleep(3600)

if __name__ == "__main__":
    for i in range(5):
        t = Toutiao()
        work_thread = Thread(target=t.run)
        work_thread.start()
