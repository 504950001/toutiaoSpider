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
                url = 'http://dev.api.juejinchain.cn/index/spider/video'
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

    def get_comment(self, item_id, group_id, offset):
        ua = UserAgent()
        UA = ua.random
        ts = int(time.time())
        param_data = {
            'offset': offset,
            'group_id': group_id,
            'aggr_type': 1,
            'count': 50,
            'item_id': item_id,
            'ts': ts
        }
        comment_url = 'http://is-hl.snssdk.com/article/v4/tab_comments/?' + urlencode(param_data)
        headers = {
            'User-Agent': UA
            #'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0.1; SM-A8000 Build/MMB29M) NewsArticle/7.0.3 cronet/TTNetVersion:a729d5c3',
        }
        time.sleep(random.randint(1, 2) / 16)
        try:
            response = requests.get(comment_url, headers=headers, timeout=3)
            total_number = response.json()['total_number']
            data = response.json()['data']
            #time.sleep(random.randint(1, 2) / 1)
            print('data: ', data)
            self.parse_comment(data, item_id, group_id, total_number, UA, offset)
        except Exception as e:
            print('something is wrong!!!',e)

    def parse_comment(self, comments, item_id, group_id, total_number, UA, offset):
        for comment in comments:
            # 当前请求Unix时间戳
            mt = int(time.time())
            # API签名字符串
            para = 'b#28ac3c1abc' + 'juejinchain.com' + str(mt)
            sign = hashlib.md5(para.encode(encoding='UTF-8')).hexdigest()
            # 文章url
            url = 'http://toutiao.com/group/' + str(item_id) + '/'
            # 回复唯一标识ID
            id = comment['comment']['id']
            # 评论用户名称
            user_name = comment['comment']['user_name']
            # 评论用户头像链接
            user_img_url = comment['comment']['user_profile_image_url']
            # 评论内容text
            text = comment['comment']['text']
            # 评论时间
            create_time = comment['comment']['create_time']
            # 评论内容点赞数
            digg_count = comment['comment']['digg_count']
            # 评论回复数
            reply_count = comment['comment']['reply_count']

            print('text: ', text)
            print('total_number: ', total_number)

            # 获取回复comment
            reply_list = []
            if reply_count > 0:
                offset_reply = 0
                self.get_reply_comment(id, reply_list, offset_reply, UA)

            items = {
                'mt': mt,
                'sign': sign,
                'url': url,
                'nickname': user_name,
                'avatar': user_img_url,
                'content': text,
                'reply': reply_count,
                'fabulous': digg_count,
                'comment_time': create_time,
                'reply_list': json.dumps(reply_list),
            }

            # 文章评论信息存储
            try:
                url = 'http://dev.api.juejinchain.cn/index/spider/video_comment'
                #url = 'http://dev.api.juejinchain.cn/index/spider/toutiao_comment'
                body = requests.post(url, data=items)
                print(body.text)
                #jjb_url = 'http://api.juejinchain.com/index/spider/toutiao_comment'
                #requests.post(jjb_url, data=items)
                print('comment ok!!!!')
            except Exception as e:
                print('insert db wrong!!!!', e)

        else:
            if total_number <= 50:
                return
            offset += 50
            if offset > 50:
                return
            self.get_comment(item_id, group_id, offset)

    def get_reply_comment(self, id, reply_list, offset_reply, UA):
        param_data = {
            'id': id,
            'count': 50,
            'offset': offset_reply
        }

        headers = {
            'Host': 'is-hl.snssdk.com',
            'User-Agent': UA,
        }
        time.sleep(random.randint(1, 2) / 16)

        try:
            reply_url = 'http://is-hl.snssdk.com/2/comment/v3/reply_list/?' + urlencode(param_data)
            response = requests.get(reply_url, headers=headers, timeout=3)
            soup = response.json()
            print(soup)
            self.parse_reply_comment(soup, id, reply_list, offset_reply, UA)
        except Exception as e:
            print('reply_comment is wrong', e)

    def parse_reply_comment(self, response, id, reply_list, offset_reply, UA):
        # 判断是否有下一页
        has_more = response['data']['has_more']
        comments = response['data']['data']
        for comment in comments:
            print('-------reply comment---------')
            # 回复内容text
            text = comment['text']
            # 回复时间
            create_time = comment['create_time']
            # 点赞数
            digg_count = comment['digg_count']
            # 用户名
            try:
                user_name = comment['user']['name']
            except:
                user_name = comment['user']['screen_name']
            # 用户头像链接
            avatar_url = comment['user']['avatar_url']
            # 回复的回复内容reply_to_comment
            try:
                reply_to_text = comment['reply_to_comment']['text']
                reply_to_user = comment['reply_to_comment']['user_name']
                try:
                    large_image_list = comment['reply_to_comment']['large_image_list']
                    url_img_list = []
                    for url_list in large_image_list:
                        url_img_list.append(url_list['url'])
                except:
                    url_img_list = []
                reply_to_comment = {
                    'reply_to_text': reply_to_text,
                    'reply_to_user': reply_to_user,
                    'url_img_list': url_img_list
                }
            except:
                reply_to_comment = {}

            print('reply_text: ', text)

            items = {
                'nickname': user_name,
                'avatar': avatar_url,
                'content': text,
                'fabulous': digg_count,
                'comment_time': create_time,
                'reply_to_comment': reply_to_comment
            }
            reply_list.append(items)

        else:
            if has_more:
                print('111111')
                offset_reply += 50
                self.get_reply_comment(id, reply_list, offset_reply, UA)

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
