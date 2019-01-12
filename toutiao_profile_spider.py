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

                print('url: ', url)
                print('title: ', title)
                print('=====================华丽的分割线===========================')

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
                        url = 'http://dev.api.juejinchain.cn/index/spider/toutiao'
                        requests.post(url, data=items)
                        time.sleep(0.001)
                        jjb_url = 'http://api.juejinchain.com/index/spider/toutiao'
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
        print(url)
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

    def get_comment(self, item_id, group_id,offset):
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
            #'Host': 'is-hl.snssdk.com',
            'User-Agent': UA
            #'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0.1; SM-A8000 Build/MMB29M) NewsArticle/7.0.3 cronet/TTNetVersion:a729d5c3',
        }
        time.sleep(random.randint(1, 2) / 16)
        try:
            response = requests.get(comment_url, headers=headers, timeout=3)
            total_number = response.json()['total_number']
            data = response.json()['data']
            time.sleep(random.randint(1, 2) / 1)
            print('data: ', data)
            if data == []:
                now = int(time.time())
                item = {'item_id': item_id, 'group_id': group_id, 'save_time': now}
                self.redis_cli.sadd('spider_toutiao_comment_id', str(item))
                print('insert item success！！！')
                return
            self.parse_comment(data, item_id, group_id, total_number,UA,offset)
        except:
            now = int(time.time())
            item = {'item_id': item_id, 'group_id': group_id, 'save_time': now}
            self.redis_cli.sadd('spider_toutiao_comment_id', str(item))
            print('something is wrong!!!')

    def parse_comment(self, comments, item_id, group_id, total_number,UA,offset):
        for comment in comments:
            # 当前请求Unix时间戳
            mt = int(time.time())
            # API签名字符串
            para = 'b#28ac3c1abc' + 'juejinchain.com' + str(mt)
            sign = hashlib.md5(para.encode(encoding='UTF-8')).hexdigest()
            # 文章url
            url = 'http://toutiao.com/item/' + str(item_id)
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
                self.get_reply_comment(id, reply_list, offset_reply,UA)

            items = {
                'mt': mt,
                'sign': sign,
                'arc_url': url,
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
                url = 'http://dev.api.juejinchain.cn/index/spider/toutiao_comment'
                requests.post(url, data=items)
                jjb_url = 'http://api.juejinchain.com/index/spider/toutiao_comment'
                requests.post(jjb_url, data=items)
                print('ok!!!!')
            except Exception as e:
                print('insert db wrong!!!!', e)

        else:
            if total_number <= 50:
                return
            offset += 50
            if offset > 50:
                return
            self.get_comment(item_id, group_id,offset)

    def get_reply_comment(self, id, reply_list, offset_reply,UA):
        param_data = {
            'id': id,
            'count': 50,
            'offset': offset_reply
        }
        #ua = UserAgent()
        headers = {
            'Host': 'is-hl.snssdk.com',
            'User-Agent': UA,
        }
        time.sleep(random.randint(1, 2) / 4)
        try:
            reply_url = 'http://is-hl.snssdk.com/2/comment/v3/reply_list/?' + urlencode(param_data)
            response = requests.get(reply_url, headers=headers, timeout=3)
            soup = response.json()
            print(soup)
            self.parse_reply_comment(soup, id, reply_list, offset_reply,UA)
        except Exception as e:
            print('reply_comment is wrong', e)

    def parse_reply_comment(self, response, id, reply_list, offset_reply,UA):
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
                self.get_reply_comment(id, reply_list, offset_reply,UA)

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
