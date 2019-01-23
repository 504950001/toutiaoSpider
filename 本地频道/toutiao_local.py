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
        self.redis_cli = redis.Redis(host='192.168.0.21', port=6379, db=1, password='123456', charset='utf8', decode_responses=True)
        self.max_behot_time = int(time.time())
        self.count = 1
        self.times = 0

    def get_5u_ip(self):
        url = 'http://api.ip.data5u.com/api/get.shtml?order=bdddb9aa1464b48111975bf2f846b54c&num=1&area=%E8%8E%AB%E6%A1%91%E6%AF%94%E5%85%8B,%E5%A1%94%E5%90%89%E5%85%8B%E6%96%AF%E5%9D%A6,%E9%A9%AC%E9%87%8C,%E7%BD%97%E9%A9%AC%E5%B0%BC%E4%BA%9A,%E5%B0%BC%E6%97%A5%E5%88%A9%E4%BA%9A,%E6%8D%B7%E5%85%8B,%E5%93%A5%E6%96%AF%E8%BE%BE%E9%BB%8E%E5%8A%A0,%E5%88%9A%E6%9E%9C%E5%B8%83,%E5%A7%94%E5%86%85%E7%91%9E%E6%8B%89,%E6%91%A9%E5%B0%94%E5%A4%9A%E7%93%A6,%E6%B3%A2%E5%85%B0,%E6%B4%A5%E5%B7%B4%E5%B8%83%E9%9F%A6,%E9%A9%AC%E8%80%B3%E4%BB%96,%E5%86%88%E6%AF%94%E4%BA%9A,%E7%A7%91%E7%B4%A2%E6%B2%83,%E5%8D%B1%E5%9C%B0%E9%A9%AC%E6%8B%89,%E5%8D%A2%E6%A3%AE%E5%A0%A1,%E5%B0%BC%E6%B3%8A%E5%B0%94,%E6%96%AF%E5%A8%81%E5%A3%AB%E5%85%B0,%E5%9D%A6%E6%A1%91%E5%B0%BC%E4%BA%9A,%E5%87%A0%E5%86%85%E4%BA%9A,%E7%A7%98%E9%B2%81,%E5%8F%99%E5%88%A9%E4%BA%9A,%E5%90%89%E5%B8%83%E6%8F%90,%E8%80%81%E6%8C%9D,%E5%9C%A3%E9%A9%AC%E4%B8%81,%E9%A9%AC%E8%BE%BE%E5%8A%A0%E6%96%AF%E5%8A%A0,%E5%A1%9E%E6%B5%A6%E8%B7%AF%E6%96%AF,%E7%91%9E%E5%A3%AB,%E5%AE%89%E5%93%A5%E6%8B%89,%E6%BE%B3%E5%A4%A7%E5%88%A9%E4%BA%9A,%E8%8B%8F%E4%B8%B9,%E6%AF%94%E5%88%A9%E6%97%B6,%E5%B8%83%E9%9A%86%E8%BF%AA,%E6%B3%B0%E5%9B%BD,%E5%88%A9%E6%AF%94%E4%BA%9A,%E8%82%AF%E5%B0%BC%E4%BA%9A,%E5%A1%9E%E8%88%8C%E5%B0%94,%E5%B8%83%E5%9F%BA%E7%BA%B3%E6%B3%95%E7%B4%A2,%E6%96%B0%E5%8A%A0%E5%9D%A1,%E6%8B%89%E8%84%B1%E7%BB%B4%E4%BA%9A,%E8%90%A8%E6%91%A9%E4%BA%9A,%E8%8A%AC%E5%85%B0,%E6%B3%95%E5%9B%BD,%E4%BC%8A%E6%8B%89%E5%85%8B,%E9%BB%8E%E5%B7%B4%E5%AB%A9,%E5%A2%A8%E8%A5%BF%E5%93%A5,%E8%8E%B1%E7%B4%A2%E6%89%98,%E6%B2%99%E7%89%B9%E9%98%BF%E6%8B%89%E4%BC%AF,%E4%B9%8D%E5%BE%97,%E9%98%BF%E5%B0%94%E5%8F%8A%E5%88%A9%E4%BA%9A,%E9%98%BF%E6%A0%B9%E5%BB%B7,%E5%A5%A5%E5%9C%B0%E5%88%A9,%E5%9F%83%E5%8F%8A,%E7%91%9E%E5%85%B8,%E4%B8%B9%E9%BA%A6,%E4%B9%8C%E5%85%B9%E5%88%AB%E5%85%8B%E6%96%AF%E5%9D%A6,%E5%B7%B4%E5%B7%B4%E5%A4%9A%E6%96%AF,%E9%98%BF%E8%81%94%E9%85%8B,%E7%88%B1%E6%B2%99%E5%B0%BC%E4%BA%9A,%E8%8B%B1%E5%9B%BD,%E5%A4%9A%E7%B1%B3%E5%B0%BC%E5%8A%A0,%E8%8D%B7%E5%85%B0,%E5%AE%89%E9%81%93%E5%B0%94,%E5%AD%9F%E5%8A%A0%E6%8B%89,%E7%AB%8B%E9%99%B6%E5%AE%9B,%E6%B3%A2%E9%BB%91,%E4%B8%9C%E5%B8%9D%E6%B1%B6,%E6%97%A5%E6%9C%AC,%E7%88%B1%E5%B0%94%E5%85%B0,%E5%8D%9A%E8%8C%A8%E7%93%A6%E7%BA%B3,%E5%8A%A0%E8%93%AC,%E9%98%BF%E5%A1%9E%E6%8B%9C%E7%96%86,%E5%B8%8C%E8%85%8A,%E9%A9%AC%E6%8B%89%E7%BB%B4,%E5%88%9A%E6%9E%9C%E9%87%91,%E6%84%8F%E5%A4%A7%E5%88%A9,%E9%98%BF%E5%B0%94%E5%B7%B4%E5%B0%BC%E4%BA%9A,%E7%8E%BB%E5%88%A9%E7%BB%B4%E4%BA%9A,%E8%B6%8A%E5%8D%97,%E5%B7%B4%E5%93%88%E9%A9%AC,%E8%92%99%E5%8F%A4,%E6%B3%BD%E8%A5%BF%E5%B2%9B,%E5%96%80%E9%BA%A6%E9%9A%86,%E5%93%88%E8%90%A8%E5%85%8B%E6%96%AF%E5%9D%A6,%E7%89%99%E4%B9%B0%E5%8A%A0,%E6%96%AF%E6%B4%9B%E4%BC%90%E5%85%8B,%E6%9F%AC%E5%9F%94%E5%AF%A8,%E6%8C%AA%E5%A8%81,%E5%8D%A2%E6%97%BA%E8%BE%BE,%E5%BE%B7%E5%9B%BD,%E5%B7%B4%E5%8B%92%E6%96%AF%E5%9D%A6,%E4%B9%8C%E5%85%8B%E5%85%B0,%E5%88%A9%E6%AF%94%E9%87%8C%E4%BA%9A,%E5%8A%A0%E7%BA%B3,%E9%A9%AC%E6%9D%A5%E8%A5%BF%E4%BA%9A,%E7%BA%B3%E7%B1%B3%E6%AF%94%E4%BA%9A,%E5%9C%AD%E4%BA%9A%E9%82%A3,%E9%9F%A9%E5%9B%BD,%E5%A1%9E%E5%B0%94%E7%BB%B4%E4%BA%9A,%E6%96%B0%E8%A5%BF%E5%85%B0,%E6%B4%AA%E9%83%BD%E6%8B%89%E6%96%AF,%E9%BB%91%E5%B1%B1,%E4%B9%8C%E5%B9%B2%E8%BE%BE,%E4%BC%8A%E6%9C%97,%E4%BA%9A%E7%BE%8E%E5%B0%BC%E4%BA%9A,%E4%BF%84%E7%BD%97%E6%96%AF,%E5%85%8B%E7%BD%97%E5%9C%B0%E4%BA%9A,%E7%B4%A2%E9%A9%AC%E9%87%8C,%E4%BF%9D%E5%8A%A0%E5%88%A9%E4%BA%9A,%E8%B4%9D%E5%AE%81,%E8%8F%B2%E5%BE%8B%E5%AE%BE,%E5%B7%B4%E8%A5%BF,%E6%96%AF%E6%B4%9B%E6%96%87%E5%B0%BC%E4%BA%9A,%E8%A5%BF%E7%8F%AD%E7%89%99,%E8%91%A1%E8%90%84%E7%89%99,%E5%8C%88%E7%89%99%E5%88%A9,%E5%93%A5%E4%BC%A6%E6%AF%94%E4%BA%9A,%E5%B7%B4%E6%8B%BF%E9%A9%AC,%E5%8D%B0%E5%BA%A6%E5%B0%BC%E8%A5%BF%E4%BA%9A,%E5%B0%BC%E6%97%A5%E5%B0%94,%E5%90%89%E5%B0%94%E5%90%89%E6%96%AF%E6%96%AF%E5%9D%A6,%E4%BC%AF%E5%88%A9%E5%85%B9,%E7%BE%8E%E5%9B%BD,%E5%B0%BC%E5%8A%A0%E6%8B%89%E7%93%9C,%E5%A1%9E%E6%8B%89%E5%88%A9%E6%98%82,%E7%BC%85%E7%94%B8,%E6%B3%A2%E5%A4%9A%E9%BB%8E%E5%90%84,%E8%B5%A4%E9%81%93%E5%87%A0%E5%86%85%E4%BA%9A,%E7%99%BD%E4%BF%84%E7%BD%97%E6%96%AF,%E5%8E%84%E7%93%9C%E5%A4%9A%E5%B0%94,%E9%A9%AC%E5%85%B6%E9%A1%BF,%E6%A0%BC%E9%B2%81%E5%90%89%E4%BA%9A,%E5%9C%9F%E8%80%B3%E5%85%B6,%E6%99%BA%E5%88%A9,%E6%B5%B7%E5%9C%B0,%E4%BB%A5%E8%89%B2%E5%88%97,%E5%8A%A0%E6%8B%BF%E5%A4%A7,%E5%8D%97%E9%9D%9E,%E9%A9%AC%E5%B0%94%E4%BB%A3%E5%A4%AB,%E7%A7%91%E5%A8%81%E7%89%B9,%E5%B7%B4%E5%9F%BA%E6%96%AF%E5%9D%A6,%E5%B7%B4%E6%8B%89%E5%9C%AD,%E9%98%BF%E5%AF%8C%E6%B1%97,%E6%96%AF%E9%87%8C%E5%85%B0%E5%8D%A1,%E5%8D%B0%E5%BA%A6&carrier=0&protocol=1&an1=1&an2=2&sp1=1&sp2=2&sort=1&system=1&distinct=0&rettype=0&seprator=%0D%0A'
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