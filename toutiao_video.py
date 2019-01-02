# -*- coding:utf-8 -*-

import time
import json
import redis
import requests
import random
import hashlib
from threading import Thread
from fake_useragent import UserAgent
from urllib.parse import urlencode

from requests.packages.urllib3.exceptions import InsecureRequestWarning
#禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import sys  # 设置递归深度
sys.setrecursionlimit(100000)

'''
今日头条视频频道抓取：推荐、影视、游戏、音乐、社会、综艺等
'''

class Video(object):
    def __init__(self):
        self.redis_cli = redis.Redis(host='secret', port=6379, db=1, password='secret',charset='utf8', decode_responses=True)
        self.count = 1
        self.behot_time = 1

    def get_toutiao_video(self,category_ch,category_en):
        ts = time.time()
        param_data = {
            'category': category_en,
            'max_behot_time': self.behot_time,
            'last_refresh_sub_entrance_interval': int(ts),
            '_rticket': int(ts*1000),
            'ts': int(ts),
        }
        headers = {
            'Host': 'is-dyn9.snssdk.com',
            'Accept-Encoding': 'gzip',
            'X-SS-REQ-TICKET': str(int(ts * 1000)),
            'Cookie': 'odin_tt=4cf1dc90f2bc360affac8edfa7a11a9077199135929284709f90fc2a019d77b29f960724c8256860e038edee9ab25420; UM_distinctid=167ba3afceb12c-0e1356667-1d575105-64140-167ba3afcece3; qh[360]=1; alert_coverage=81; CNZZDATA1264530760=1766365590-1545017435-%7C1545620602; install_id=54485955739; ttreq=1$d2511451b78b05fd445e2287c976f1690d4e18b3',
            'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.2; OPPO R11 Build/NMF26X) NewsArticle/6.7.4 cronet/58.0.2991.0@59592eaa'
        }

        url = 'https://is-dyn9.snssdk.com/api/news/feed/v82/?' + urlencode(param_data)
        try:
            response = requests.get(url,headers=headers,timeout=3,verify=False)
            data = response.json()['data']
            time.sleep(random.randint(1, 2) / 4)
            self.parse_video(category_ch,category_en,data)
        except Exception as e:
            print('something is wrong!',e)

    def parse_video(self,category_ch,category_en,data_list):
        for data in data_list:
            try:
                content = data['content']
                content = json.loads(content)
            except:
                continue
            try:
                label = content['label']
                print('广告内容！！！',label)
                continue
            except:
                pass
            group_id = content['group_id']
            url = 'http://toutiao.com/group/' + str(group_id) + '/'
            title = content['title']
            try:
                author = content['user_info']['name']
            except:
                author = ''
            try:
                author_logo = content['user_info']['avatar_url']
            except:
                author_logo = ''
            publish_time = content['publish_time']
            try:
                img_url = content['middle_image']['url']
                large_img_url = content['video_detail_info']['detail_video_large_image']['url']
            except:
                continue
            try:
                video_watch_count = content['video_detail_info']['video_watch_count']
            except:
                video_watch_count = 0
            try:
                video_like_count = content['video_like_count']
            except:
                video_like_count = 0
            try:
                comment_count = content['comment_count']
            except:
                comment_count = 0
            try:
                video_id = content['video_id']
            except:
                continue
            try:
                abstract = content['abstract']
            except Exception as e:
                abstract = ''
                print('abstract is wrong!',e)

            #视频时长
            video_duration = content['video_duration']

            # 当前请求Unix时间戳
            mt = int(time.time())
            # API签名字符串
            para = 'b#28ac3c1abc' + 'juejinchain.com' + str(mt)
            sign = hashlib.md5(para.encode(encoding='UTF-8')).hexdigest()

            print('url: ',url)
            print('title: ',title)
            print('video_id: ',video_id)
            print('comment_count: ',comment_count)

            items = {
                'mt': mt,
                'sign': sign,
                'url': url,
                'title': title,
                'author': author,
                'author_logo': author_logo,
                'publish_time': publish_time,
                'source': '今日头条',
                'create_time': int(time.time()),
                'category_en': category_en,
                'category_cn': category_ch,
                'img_url': img_url,
                'large_img_url': large_img_url,
                'video_watch_count': video_watch_count,
                'video_like_count': video_like_count,
                'comment_count': comment_count,
                'video_id': video_id,
                'abstract': abstract,
                'video_duration': video_duration
            }

            try:
                url = 'http://xxx/xxx/spider/video'
                requests.post(url, data=items)
                print('comment ok!!!!')
            except Exception as e:
                print('insert db wrong!!!!', e)

            if comment_count > 0:
                offset = 0
                item_id = group_id
                self.get_comment(item_id, group_id, offset)

            self.behot_time = content['behot_time']

        self.count += 1
        if self.count > 25: #25
            return
        self.get_toutiao_video(category_ch,category_en)

    def run(self):
        while True:
            self.count = 1
            self.behot_time = int(time.time())
            now = int(time.time())
            data = self.redis_cli.lpop('spider_toutiao_video')
            data = eval(data)
            print(data)
            #time.sleep(10)
            category_ch = data['category_ch']
            category_en = data['category_en']
            next_time = data['next_time']
            base_time = now - next_time
            print(next_time)

            try:
                self.get_toutiao_video(category_ch,category_en)
                item = {}
                item['category_ch'] = category_ch
                item['category_en'] = category_en
                item['next_time'] = now
                self.redis_cli.rpush('spider_toutiao_video',str(item))
            except Exception as e:
                print(e)
                continue

            if next_time > 1546408509 and base_time < 7200:
                time.sleep(7200)

if __name__ == "__main__":
    for i in range(5):
        c = Video()
        work_thread = Thread(target=c.run)
        work_thread.start()
