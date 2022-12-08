import copy
import json
import pymysql
import random
import re
import requests
import time
from bs4 import BeautifulSoup
from requests.api import head


class Spider_for_bilibili:
    """a video-spider for bilibili."""

    def __init__(self, root_url):
        """initialize the spider."""
        self.urls_List = []
        self.Videos_List = []
        self.Authors_List = []
        self.root_url = root_url
        self.header = {
            'user-agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84'
        }

    def wait(self):
        """wait for seconds."""
        time.sleep(float(random.randint(4, 6) / 4))

    def BV(self, url):
        """return the BV id."""
        return re.search('BV\w{10}', url).group()

    def save_HTMLs(self, new_url, video_soup):
        """save the .html file."""
        with open(
                f'E:\\CODE\\Grade_1_Summer\\Python\\HTMLs\\{self.BV(new_url)}.html',
                'w',
                encoding='utf-8') as f_HTMLs:
            f_HTMLs.write(video_soup.prettify())

    def save_Covers(self, new_url, response):
        """save the .jpg file of covers of videos."""
        with open(
                f'E:\\CODE\\Grade_1_Summer\\Python\\bilibili\\Search\\static\\img\\Covers\\{self.BV(new_url)}.jpg',
                'wb') as f_Covers:
            f_Covers.write(response.content)

    def save_Portraits(self, uid, response):
        """save the .jpg file of portraits of authors."""
        with open(
                f'E:\\CODE\\Grade_1_Summer\\Python\\bilibili\\Search\\static\\img\\Portraits\\{uid}.jpg',
                'wb') as f_Portraits:
            f_Portraits.write(response.content)

    def head_data(self, video_soup):
        """get the data of the head."""
        tag = video_soup.find('head', attrs={'itemprop': 'video'})
        name = tag.find('meta', attrs={'itemprop': 'author'})['content']
        id = 0
        uid = 0
        for index, author in enumerate(self.Authors_List):
            if author['name'] == name:
                id = index + 1
                uid = author['uid']
        BV_id = self.BV(tag.find('meta', attrs={'itemprop': 'url'})['content'])
        data = {
            'title':
            str(tag.title.string)[:-14],
            'author': {
                'name': tag.find('meta', attrs={'itemprop':
                                                'author'})['content'],
                'key_id': id,
                'portrait': f'img/Portraits/{uid}.jpg'
            },
            'description':
            tag.find('meta', attrs={'itemprop': 'description'})['content'],
            'BV_id':
            BV_id,
            'url':
            tag.find('meta', attrs={'itemprop': 'url'})['content'],
            'cover':
            f'img/Covers/{BV_id}.jpg'
        }
        return data

    def video_data(self, video_soup):
        """get the data of the video."""
        tag = video_soup.find('div', attrs={'class': 'video-data'})
        data = {
            'view':
            int(
                re.search('\d+',
                          tag.find('span', attrs={'class':
                                                  'view'})['title']).group()),
            'barrage':
            int(
                re.search('\d+',
                          tag.find('span', attrs={'class':
                                                  'dm'})['title']).group()),
            'upload_date':
            video_soup.head.find('meta', attrs={'itemprop':
                                                'uploadDate'})['content']
        }
        return data

    def audience_data(self, video_soup, video_json):
        """get the data of the audiences."""
        tag = video_soup.find('div', attrs={'class': 'ops'})
        comment_json = requests.get(
            'https://api.bilibili.com/x/v2/reply?pn=1&type=1&oid=' +
            str(video_json['data']['stat']['aid']), self.header).json()
        self.wait()
        comments = []
        for audience in comment_json['data']['hots']:
            if len(comments) < 5:
                comments.append(audience['content']['message'])
            else:
                break
        data = {
            'like':
            int(
                re.search('\d+',
                          tag.find('span', attrs={'class':
                                                  'like'})['title']).group()),
            'coin':
            video_json['data']['stat']['coin'],
            'collect':
            video_json['data']['stat']['favorite'],
            'comment':
            comments
        }
        return data

    def append_author(self, video_soup, video_json, space_soup):
        """add a new author or add a new works of him."""
        tag = video_soup.find('div', attrs={'class': 'up-info_right'})
        BV_id = self.BV(
            video_soup.head.find('meta', attrs={'itemprop': 'url'})['content'])
        for author in self.Authors_List:
            if re.search('\d+',
                         tag.find('a',
                                  attrs={'report-id': 'name'
                                         })['href']).group() == author['uid']:
                author['works'].append({
                    'title':
                    str(video_soup.head.title.string)[:-14],
                    'key_id':
                    len(self.Videos_List) + 1,
                    'cover':
                    f'img/Covers/{BV_id}.jpg'
                })
                return
        author_json = requests.get(
            'https://api.bilibili.com/x/relation/stat?vmid=' +
            str(video_json['data']['owner']['mid']), self.header).json()
        self.wait()
        try:
            description = tag.find('div', attrs={'class': 'desc'})['title']
        except:
            description = ''
        uid = re.search('\d+',
                        tag.find('a', attrs={'report-id':
                                             'name'})['href']).group()
        self.Authors_List.append({
            'name':
            video_soup.head.find('meta', attrs={'itemprop':
                                                'author'})['content'],
            'uid':
            uid,
            'description':
            description,
            'portrait':
            f'img/Portraits/{uid}.jpg',
            'fan':
            author_json['data']['follower'],
            'works': [{
                'title': str(video_soup.head.title.string)[:-14],
                'key_id': len(self.Videos_List) + 1,
                'cover': f'img/Covers/{BV_id}.jpg'
            }]
        })
        response = requests.get(
            space_soup.head.find('link', attrs={'rel':
                                                'apple-touch-icon'})['href'],
            self.header)
        self.wait()
        self.save_Portraits(uid, response)

    def add_new_url(self, new_url):
        """deal with one single url."""
        video_soup = BeautifulSoup(
            requests.get(new_url, self.header).text, 'lxml')
        self.wait()
        tag = video_soup.find('div', attrs={'class': 'up-info_right'})
        space_soup = BeautifulSoup(
            requests.get(
                'https:' + tag.find('a', attrs={'report-id': 'name'})['href'],
                self.header).text, 'lxml')
        self.wait()
        video_json = requests.get(
            'https://api.bilibili.com/x/web-interface/view?bvid=' +
            self.BV(new_url), self.header).json()
        self.wait()
        self.append_author(video_soup, video_json, space_soup)
        self.Videos_List.append({
            'head_data':
            self.head_data(video_soup),
            'video_data':
            self.video_data(video_soup),
            'audience_data':
            self.audience_data(video_soup, video_json)
        })
        self.save_HTMLs(new_url, video_soup)
        response = requests.get(
            video_soup.head.find('meta', attrs={'itemprop':
                                                'image'})['content'],
            self.header)
        self.wait()
        self.save_Covers(new_url, response)
        self.urls_List.append(new_url)

    def to_MySQL(self):
        """write in database bilibili_db."""
        connection = pymysql.connect(host='localhost',
                                     user='bilibili',
                                     password='114514',
                                     database='bilibili_db',
                                     charset='utf8mb4')
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS `videos`')
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `videos`(`ID` INT NOT NULL AUTO_INCREMENT,`title` TEXT COMMENT '标题',`author` TEXT COMMENT '作者',`description` TEXT COMMENT '简介',`BV_id` TEXT COMMENT 'BV号',`url` TEXT COMMENT 'url',`cover` TEXT COMMENT '封面',`view` INT COMMENT '播放量',`barrage` INT COMMENT '弹幕量',`upload_date` TEXT COMMENT '上传日期',`like` INT COMMENT '点赞数',`coin` INT COMMENT '投币数',`collect` INT COMMENT '收藏数',`comment` TEXT COMMENT '热门评论',PRIMARY KEY(`ID`))DEFAULT CHARACTER SET=utf8mb4 COMMENT='视频信息';"
        )
        cursor.execute('DROP TABLE IF EXISTS `authors`')
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `authors`(`ID` INT NOT NULL AUTO_INCREMENT,`name` TEXT COMMENT '名称',`uid` TEXT COMMENT 'UID',`description` TEXT COMMENT '简介',`portrait` TEXT COMMENT '头像',`fan` INT COMMENT '粉丝数',`works` TEXT COMMENT '作品',PRIMARY KEY(`ID`))DEFAULT CHARACTER SET=utf8mb4 COMMENT='作者信息';"
        )
        insert_sql = 'INSERT INTO `videos`(`title`,`author`,`description`,`BV_id`,`url`,`cover`,`view`,`barrage`,`upload_date`,`like`,`coin`,`collect`,`comment`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        for video in self.Videos_List:
            title = video['head_data']['title']
            author = str(video['head_data']['author'])
            description = video['head_data']['description']
            BV_id = video['head_data']['BV_id']
            url = video['head_data']['url']
            cover_url = video['head_data']['cover']
            view = video['video_data']['view']
            barrage = video['video_data']['barrage']
            upload_date = video['video_data']['upload_date']
            like = video['audience_data']['like']
            coin = video['audience_data']['coin']
            collect = video['audience_data']['collect']
            comment = '$'.join(video['audience_data']['comment'])
            values = (title, author, description, BV_id, url, cover_url, view,
                      barrage, upload_date, like, coin, collect, comment)
            cursor.execute(insert_sql, values)
        insert_sql = 'INSERT INTO `authors`(`name`,`uid`,`description`,`portrait`,`fan`,`works`) VALUES(%s,%s,%s,%s,%s,%s)'
        for author in self.Authors_List:
            name = author['name']
            uid = author['uid']
            description = author['description']
            portrait_url = author['portrait']
            fan = author['fan']
            works = []
            for w in author['works']:
                works.append(str(w))
            values = (name, uid, description, portrait_url, fan,
                      '$'.join(works))
            cursor.execute(insert_sql, values)
        connection.commit()
        connection.close()

    def crawl(self, n):
        """crawl in bilibili."""
        while len(self.urls_List) < n:
            video_soup = BeautifulSoup(
                requests.get(self.root_url, self.header).text, 'lxml')
            self.wait()
            try:
                rec_tag = video_soup.find('div', attrs={'class': 'rec-list'})
                try:
                    for tag in rec_tag.find_all(
                            'div', attrs={'class': 'video-page-card'}):
                        if (re.sub('BV\w{10}', self.BV(tag.a['href']),
                                   self.root_url) not in self.urls_List):
                            try:
                                self.root_url = re.sub('BV\w{10}',
                                                       self.BV(tag.a['href']),
                                                       self.root_url)
                                self.add_new_url(self.root_url)
                            except:
                                continue
                except:
                    continue
            except:
                continue
        self.to_MySQL()


spider = Spider_for_bilibili('https://www.bilibili.com/video/BV1gg41177yD')
spider.crawl(5000)
