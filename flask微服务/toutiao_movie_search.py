# coding=utf-8

import requests
import time
import hashlib
import json
import re
import random
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.packages.urllib3.exceptions import InsecureRequestWarning
#禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Movie(object):
    def __init__(self):
        self.offset = 0
        self.count = 0

    def movie_page_search(self,keyword):
        param_data = {
            'offset': self.offset,
            'format': 'json',
            'keyword': keyword,
            'autoload': 'true',
            'count': 20,
            'cur_tab': 1,
            'from': 'search_tab',
            'pd': 'synthesis'
        }
        headers = {
            'Accept': 'application/json, text/javascript',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'www.toutiao.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Mobile Safari/537.36',
            #'Cookie': 'tt_webid=6633177721172510211; UM_distinctid=16795d64deb4d2-06cf1e2bb36f16-3a3a5d0c-1fa400-16795d64dec651; tt_webid=6633177721172510211; csrftoken=e4399435db5073524703dd9ea9fdea4e; uuid="w:e8e0021456144b609cbcbccb9790fe68"; _ba=BA0.2-20181212-51299-WX9Hyj2N1lZjqeaWXXp6; _ga=GA1.2.710554198.1544683104; WEATHER_CITY=%E5%A4%A9%E6%B4%A5; utm_source=toutiao; __tasessionId=59o94pvbj1546410545161; CNZZDATA1259612802=2038699008-1544404633-https%253A%252F%252Fwww.baidu.com%252F%7C1546409460'
        }
        try:
            url = 'https://www.toutiao.com/search_content/?' + urlencode(param_data)
            response = requests.get(url,headers=headers,timeout=3,verify=False).json()
            time.sleep(1)
            data = response['data']
            self.parse_page(data)
        except Exception as e:
            if self.count < 2:
                self.count += 1
                self.movie_page_search(keyword)
            print('something is wrong!!!',e)
            return

        has_more = response['has_more']
        if has_more:
            self.offset += 20
            self.movie_page_search(keyword)

    def parse_page(self,data_list):
        for data in data_list:
            try:
                has_gallery = data['has_gallery']
                has_video = data['has_video']
            except:
                continue

            if has_gallery or has_video:
                continue

            # 当前请求Unix时间戳
            mt = int(time.time())
            # API签名字符串
            para = 'b#28ac3c1abc' + 'juejinchain.com' + str(mt)
            sign = hashlib.md5(para.encode(encoding='UTF-8')).hexdigest()
            #文章URL
            item_id = data['item_id']
            url = 'http://toutiao.com/group/' + str(item_id) + '/'
            #文章标题
            title = data['title']
            #文章摘要
            abstract = data['abstract']
            #媒体号名称（文章作者名称）
            author = data['media_name']
            #文章阅读数
            read_count = data['read_count']
            #文章评论数
            comment_count = data['comment_count']
            #发布时间(Unix时间戳)
            publish_time = data['publish_time']

            content_info = self.get_content(item_id)
            #文章内容
            content = content_info['content']
            #文章小图
            img_url = content_info['img_url']
            #文章大图
            large_img_url = content_info['large_img_url']

            '''
            print('url: ', url)
            print('title: ', title)
            print('abstract: ', abstract)
            print('author: ', author)
            print('read_count: ', read_count)
            print('comment_count: ', comment_count)
            print('publish_time: ', publish_time)
            print('img_url: ', img_url)
            print('large_img_url: ', large_img_url)
            print('content: ',content)


            if comment_count > 0:
                offset = 0
                group_id = item_id
                self.get_comment(item_id, group_id, offset)
            '''

    def get_content(self, cid):
        url = "http://a6.pstatp.com/article/content/lite/14/1/{}/{}/1/".format(cid, cid)
        #print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }
        try:
            response = requests.get(url=url, headers=headers)
            resp = response.json()['data']
            con = resp['content']
            #print('con+++++++++++++++++',con)
            time.sleep(0.1)
            if con == '该内容已删除':
                content = '[]'
            else:
                r = re.sub(r'zip_src_path=".*?"', '', con)
                soup = BeautifulSoup(r, 'lxml')
                content = str(soup.select("article")[0])
                print('content=================',content)
        except:
            content = '[]'

        try:
            # 小图
            img_url = json.dumps([url_list['url'] for url_list in resp['thumb_image']])
        except:
            img_url = '[]'
        try:
            # 大图
            large_img_url = json.dumps([url_list['url'] for url_list in resp['image_detail']])
        except:
            large_img_url = '[]'

        item = {
            'img_url': img_url,
            'large_img_url': large_img_url,
            'content': content
        }

        return item

if __name__ == "__main__":
    m = Movie()
    keyword = '后会无期'
    m.movie_page_search(keyword)