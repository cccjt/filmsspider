import asyncio
import json
import random
import re
import sys
import time

import aiohttp
import requests
from bs4 import BeautifulSoup
from pyppeteer import launch
from pyppeteer.network_manager import Request

from utils.AsyncPool import AsyncPool
from utils.MongoUtil import MongoUtil

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class DoubanSpider(object):
    def __init__(self):
        self.proxyArr = []
        self.searchFilmList = []
        self.film_coll = MongoUtil().getCol('films')
        pass

    def run_search_link(self):
        self.init_proxy(5)
        # Db = MysqlHelper()
        # self.searchFilmList = Db.select(
        #     "select id,film_name,douban_url from film_list where douban_url is null and classify in (1,2,4)")
        query = {
            "douban_rating": {
                "$exists": False
            },
            "douban_state": {"$ne": 1},
            "classify": {
                "$in": [
                    1.0,
                    # 2.0,
                    # 4.0
                ]
            }}
        projection = {"_id": 1.0, 'film_name': 1}

        self.searchFilmList = self.film_coll.find(query, projection=projection)
        self.searchFilmList = list(self.searchFilmList)
        self.count = len(self.searchFilmList)
        print(self.count)
        # asyncio.run(self.searchLink())
        # 任务组， 最大协程数
        loop = asyncio.get_event_loop()
        tasks = []
        for x in range(10):
            tasks.append(self.searchLink())
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

    # 搜索详情
    def run_search_info(self):
        self.init_proxy(2)
        query = {'$and': [
            {
                "douban_url": {
                    u"$exists": True
                }
            },
            {
                "douban_rating": {
                    u"$exists": True
                }
            },
            {
                "douban_url": {
                    u"$ne": u"no"
                }
            },
            {
                "douban_country": {
                    u"$exists": False
                }
            },
            {
                "douban_state": {
                    u"$ne": 1
                }
            }
        ]}
        self.searchFilmList = self.film_coll.find(query, projection={"_id": 1, 'douban_url': 1, 'year': 1})
        self.searchFilmList = list(self.searchFilmList)
        self.count = len(self.searchFilmList)
        # asyncio.run(self.get_film_info())

        pool = AsyncPool(maxsize=1)
        for x in range(self.count):
            pool.submit(self.get_film_info())
        pool.release()
        pool.wait()

    # 初始化代理池
    def init_proxy(self, num=2):
        ip = requests.get('https://www.anpaitm.com/index/test?key=JGbeg4gFJD875obads')
        requests.get(
            'http://wapi.http.linkudp.com/index/index/save_white?neek=352139&appkey=3fdebe3814651abea473ec39b5dc53d1&white=' + ip.text)
        res = requests.get(
            f'http://webapi.http.zhimacangku.com/getip?num={num}&type=2&pro=&city=0&yys=0&port=11&time=1&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions=')
        js = res.json()
        for x in js['data']:
            self.proxyArr.append(f"{x['ip']}:{x['port']}")
        time.sleep(1)

    # 获取代理, 随机拿一个
    def get_proxy(self):
        if len(self.proxyArr) == 0:
            return ''
        index = random.randint(0, len(self.proxyArr) - 1)
        return self.proxyArr[index] if len(self.proxyArr) > 0 else ''

    # 代理失效后的处理
    def del_proxy(self, proxy):
        if not proxy: return

        if proxy in self.proxyArr:
            self.proxyArr.remove(proxy)

        if len(self.proxyArr) < 2:
            self.init_proxy()

    async def get_browser(self):
        proxy = self.get_proxy()
        browser = await launch({'headless': False, 'autoClose': True, 'args': [
            f"--user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(56, 70)}.0.3538.25 Safari/537.36 Core/1.70.3861.400 QQBrowser/10.7.43{random.randint(0, 10)}.400",
            '--proxy-server=%s' % proxy
        ]})
        return browser, proxy

    @staticmethod
    def filter_film_name(name):
        # 过滤电影名称
        filter_re = re.compile("超清720P|高清\w*|%|\.|'|\\n|       |\u3000\u3000|（\w+）|普通话版|粤语版|\((.*)\)")
        return re.sub(filter_re, '', name).strip()

    # def codingJson(self, data):
    #     return escape_string(self.filter_film_name(json.dumps(data, ensure_ascii=False)))

    async def intercept_request(req):
        """请求过滤"""
        if req.resourceType in ['image', 'media', 'eventsource', 'websocket']:
            await req.abort()
        else:
            await req.continue_()

    # 通过电影名称搜索豆瓣链接
    async def searchLink(self):
        browser = None
        page = None
        browser, proxy = await self.get_browser()
        page = await browser.newPage()
        # await page.setRequestInterception(True)
        # page.on('request', "item=>self.intercept_request")
        # page.on('request', lambda req: asyncio.ensure_future(self.intercept_request(req)))

        while True:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            if len(self.searchFilmList) == 0:
                break
            film = self.searchFilmList.pop()
            film_name = self.filter_film_name(film['film_name'])
            print(film_name)
            link = 'https://search.douban.com/movie/subject_search?search_text=' + film_name
            try:
                goto_link = await page.goto(link, {'timeout': 50 * 1000})
                body = await page.J('body')
                body_text = await page.evaluate('item=>item.textContent', body)
                if goto_link.status != 200 or body_text.find('检测到有异常') != -1 or body_text.find(
                        '服务异常') != -1 or body_text.find('请登录后再试') != -1:
                    self.del_proxy(proxy)
                    print('检测到有异常')
                    await page.close()
                    await browser.close()
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    browser, proxy = await self.get_browser()
                    page = await browser.newPage()
                    continue
                # 没有找到
                if body_text.find('换个搜索词试试吧') != -1 or body_text.find('根据相关法律法规和政策') != -1:
                    self.film_coll.update_one({'_id': film['_id']}, {'$set': {'douban_state': 1}})
                    print("\r剩余--： %d" % len(self.searchFilmList), end='')
                    continue
            except:
                # await page.close()
                # await browser.close()
                # page = None
                # browser = None
                # self.del_proxy(proxy)
                print('检测到有异常')
                # continue

            root = await page.J('#wrapper')
            # root_text = await page.evaluate('item=>item.textContent', root)

            item_root = await page.J('.item-root')
            while not item_root:
                await asyncio.sleep(1)

            # 没有搜到
            if not item_root:
                data = {'douban_url': 'no', 'film_name': film_name}
                # Db.update_dict('film_list', {'id': film['id']}, data)
                print('no find')
                continue
            # print(await page.evaluate('item=>item.textContent', item_root))
            # print(await page.evaluate('item=>item.src', await item_root.J('.cover-link >.cover')))
            # print(await page.evaluate('item=>item.href', await item_root.J('.cover-link')))
            title = await page.evaluate('item=>item.textContent', await item_root.J('.title-text'))

            douban_rating = await item_root.J('.rating >.rating_nums')
            if douban_rating:
                douban_rating = await page.evaluate('item=>item.textContent', douban_rating)
            else:
                douban_rating = 1.1
            data = {
                'douban_pic': await page.evaluate('item=>item.src', await item_root.J('.cover-link >.cover')),
                'douban_url': await page.evaluate('item=>item.href', await item_root.J('.cover-link')),
                'douban_rating': douban_rating,
                'film_name': film_name
            }
            self.film_coll.update_one({'_id': film['_id']}, {'$set': data})
            print("\r剩余： %d" % len(self.searchFilmList), end='')

        if page:
            await page.close()
        if browser:
            await browser.close()
        page = None
        browser = None

    async def get_film_info(self):
        try:
            film = self.searchFilmList.pop()
        except:
            return
        proxy = self.get_proxy()
        headers = {
            'Host': 'movie.douban.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3904.108 Safari/537.36'}
        # 实例化好一个请求对象
        async with aiohttp.ClientSession(trust_env=True) as sess:
            # 调用get发起请求，返回一个响应对象
            async with sess.get(url=film['douban_url'], headers=headers, timeout=5000,
                                proxy="http://" + proxy) as response:
                # await asyncio.sleep(random.uniform(0.5, 1.5))
                if response.status != 200:
                    self.del_proxy(proxy)
                    print('err')
                    return
                    # pool.submit(self.get_film_info(Db, pool))

                page_text = await response.text()
                soup = BeautifulSoup(page_text, 'html.parser')
                info = soup.find('div', id="info")
                if info.find('span', text=re.compile("^职业.?")) or info.find('span', text=re.compile("^性别.?")) or \
                        info.find('dt', text=re.compile("^官方网站.?")) or info.find('h2', text=re.compile("影人简介.?")):
                    self.film_coll.update_one({'_id': film['_id']}, {'$set': {'douban_state': 1}})
                    self.count -= 1
                    print("\r剩余-： %d" % self.count, end='')
                    return

                producer = info.find(name='span', class_=re.compile('pl'), text=re.compile("^制片国家.?"))
                producer = producer.next_sibling.replace(' ', '') if producer is not None else ''
                if producer == '':
                    producer1 = info.find('span', attrs={'property': 'v:initialReleaseDate'})
                    producer1 = producer1.string if producer1 else ''
                    producer1 = re.findall(r'[0123456789-]?\((.*)\)', producer1) if producer1 else []
                    producer = producer1[0] if len(producer1) > 0 else ''
                data_str = soup.find('script', attrs={'type': 'application/ld+json'}).string
                data_dict = json.loads(data_str, strict=False)
                douban_name = data_dict['name']
                director = data_dict['director'][0]['name'] if len(data_dict['director']) > 0 else ''
                actor = []
                for x in data_dict['actor']:
                    actor.append(x['name'])
                # year = fi.lm['year'] if film['year'] and film['year'] != -1 else '1990'
                # initial_date = data_dict['datePublished'] if data_dict['datePublished'] != '' else str(year) + '-01-01'
                # douban_initial_year = initial_date.split('-')[0] if initial_date else year
                year = 1990
                if data_dict['datePublished']:
                    initial_date = data_dict['datePublished']
                else:
                    if film['year'] and 1960 < int(film['year']) < 2022:
                        year = film['year']
                    initial_date = str(year) + '-01-01'
                douban_initial_year = initial_date.split('-')[0] if initial_date else year

                if len(soup.select('#link-report span')) > 0:
                    if soup.select('#link-report .all'):
                        des_text = soup.select('#link-report .all')[0].get_text()
                    else:
                        des_text = soup.select('#link-report span')[0].get_text()
                    des = self.filter_film_name(des_text)
                else:
                    des = ''

                data = {
                    'douban_genre': data_dict['genre'],
                    'douban_country': producer,
                    'douban_initial_date': initial_date,
                    'douban_initial_year': douban_initial_year,
                    'actor': actor,
                    'director': director,
                    'douban_name': douban_name if len(douban_name) <= 200 else douban_name[:100],
                    'douban_des': self.filter_film_name(des)
                }
                print(data)
                print(film)
                # Db.update_byid('film_list', data)
                # Db.update_dict('film_info', {'film_id': film['id']}, data2)
                self.film_coll.update_one({'_id': film['_id']}, {'$set': data})
                self.count -= 1
                print("\r剩余： %d" % self.count, end='')


if __name__ == '__main__':
    DoubanSpider().run_search_link()
    # DoubanSpider().run_search_link()
