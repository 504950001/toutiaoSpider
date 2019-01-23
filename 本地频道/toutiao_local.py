# -*- coding:utf-8 -*-

import requests
import time
import json
import re
import random
import hashlib
import redis
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from city import *
from apscheduler.schedulers.background import BackgroundScheduler
from requests.packages.urllib3.exceptions import InsecureRequestWarning
#禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import sys  #设置递归深度
sys.setrecursionlimit(100000)

class Local(object):
    def __init__(self):
        self.redis_cli = redis.Redis(host='xxx', port=6379, db=1, password='xxx', charset='utf8', decode_responses=True)
        self.max_behot_time = int(time.time())
        self.count = 1
        self.times = 0

    def get_5u_ip(self):
        url = '代理API接口'
        res = requests.get(url).json()
        p = res['data'][0]['ip']
        h = res['data'][0]['port']
        if p == '':
            self.get_5u_ip()
        ip = str(p) + ':' + str(h)

        return ip

    def get_toutiao_local(self,user_city):
        city_info = ['北京市', '深圳市', '广州市', '上海市', '杭州市', '南京市', '武汉市', '成都市', '重庆市']
        city = random.choice(city_info)
        param_data = {
            'category':'news_local',
            'city': city,
            'user_city': user_city,
            'max_behot_time': self.max_behot_time
        }
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random
        }
        url = 'http://is.snssdk.com/api/news/feed/v88/?' + urlencode(param_data)
        ip = self.get_5u_ip()
        '''
        ip = self.redis_cli.lpop('5u_ip')
        if ip == 'None':
            time.sleep(5)
            ip = self.redis_cli.lpop('5u_ip')
        '''
        proxies = {
            "http": "http://{}".format(ip),
        }
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=5).json()
            time.sleep(random.randint(1, 2) / 16)
            data = response['data']
            self.parse_local_article(data, user_city)
            self.redis_cli.lpush('5u_ip', ip)
        except Exception as e:
            print('response is wrong!!!', e)
            self.times += 1
            if self.times > 50:
                return
            self.get_toutiao_local(user_city)

        self.count += 1
        if self.count > 5:
            return
        self.get_toutiao_local(user_city)

    def parse_local_article(self,data_list,user_city):
        for data in data_list:
            article_info = data['content']
            article_info = json.loads(article_info)
            #文章摘要
            describe = article_info['abstract']
            if describe == "": #判断是否为广告
                continue
            try:
                label = article_info['label']  #判断是否为广告
                print(label)
                continue
            except:
                pass
            try:
                article_url = article_info['article_url']
            except Exception as e:
                print('文章的URL没有：', e)
                continue
            if article_url.startswith('https://www.wukong.com/question'):
                print('该文章为悟空问答')
                continue
            elif article_url.startswith('sslocal'):
                print('该文章为微头条')
                continue
            else:
                pass
            print('style: ', article_url)
            #当前请求Unix时间戳
            mt = int(time.time())
            #API签名字符串
            para = 'b#28ac3c1abc' + 'juejinchain.com' + str(mt)
            sign = hashlib.md5(para.encode(encoding='UTF-8')).hexdigest()
            #媒体ID(即用户ID)
            mid = 0
            #频道ID
            channel_id = 88888   #88888表示本地
            #文章URL
            group_id = article_info['group_id']
            url = 'http://toutiao.com/group/' + str(group_id) + '/'
            #文章标题
            try:
                title = article_info['title']    #判断是否为头条寻人
            except Exception as e:
                print('该内容不是文章：',e)
                continue
            #媒体号名称（文章作者名称）
            try:
                author = article_info['media_info']['name']
            except Exception as e:
                print('内容估计是悟空问答：', e)
                continue
            #作者logo
            try:
                avatar = article_info['media_info']['avatar_url']
            except Exception as e:
                print('我也不知道为啥头像为空：', e)
                avatar = ''
            #文章阅读数
            try:
                read_count = article_info['read_count']
            except Exception as e:
                print('阅读数为0：', e)
                read_count = 0
            #文章评论数
            try:
                comment_count = article_info['comment_count']
            except Exception as e:
                print('评论数为0：', e)
                comment_count = 0
            #文章发布时间
            publish_time = article_info['publish_time']
            #文章图片json格式字符串
            try:
                img_url = json.dumps([url_list['url'] for url_list in article_info['image_list']])
            except Exception as e:
                print('该文章没有图片：', e)
                img_url = '[]'
            #创建时间
            create_time = int(time.time())
            #城市
            city = user_city

            #文章内容
            content = self.get_toutiao_article(group_id)

            print('content: ', content)
            print('describe: ', describe)
            print('img_url: ', img_url)
            print('title: ', title)
            print('url: ', url)
            print('author: ', author)
            print('avatar: ', avatar)
            print('publish_time: ', publish_time)
            print('read_count: ', read_count)
            print('comment_count: ', comment_count)
            print('city: ', city)
            print('content: ', content)

            items = {
                'mt': mt,
                'sign': sign,
                'mid': mid,
                'channel_id': channel_id,
                'url': url,
                'title': title,
                'img_url': img_url,
                'author': author,
                'author_logo': avatar,
                'read_count': read_count,
                'comment_count': comment_count,
                'publish_time': publish_time,
                'describe': describe,
                'content': content,
                'create_time': create_time
            }

            if len(content) > 50:
                #文章信息存储
                try:
                    url = 'http://dev.api.juejinchain.cn/index/spider/toutiao'
                    res = requests.post(url, data=items)
                    print(res.text)
                except Exception as e:
                    print('insert wrong!!!!', e)

            self.max_behot_time = article_info['behot_time']

    def get_toutiao_article(self, cid):
        url = "http://a6.pstatp.com/article/content/lite/14/1/{}/{}/1/".format(cid, cid)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }
        try:
            response = requests.get(url=url, headers=headers, timeout=3)
            resp = response.json()['data']
            con = resp['content']
            time.sleep(random.randint(1, 2) / 16)
            if con == '该内容已删除':
                content = '[]'
            else:
                r = re.sub(r'zip_src_path=".*?"', '', con)
                soup = BeautifulSoup(r, 'lxml')
                content = str(soup.select("article")[0])
        except:
            content = '[]'

        return content

    def project_start(self):
        city_info_list = city_info
        for city_inf in city_info_list:
            self.count = 1
            self.times = 0
            self.max_behot_time = int(time.time())
            city = city_inf[0]
            try:
                self.get_toutiao_local(city)
            except Exception as e:
                print('get_toutiao_local is wrong!!!', e)

    def run_task(self):
        #创建后台执行的 schedulers
        scheduler = BackgroundScheduler()
        #添加调度任务
        scheduler.add_job(self.project_start, 'interval', hours=24, start_date='2019-1-23 18:36:00')
        #启动调度任务
        scheduler.start()

        while True:
            time.sleep(100)
            print('ok')

if __name__ == "__main__":
    l = Local()
    l.run_task()
