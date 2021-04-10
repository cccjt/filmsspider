import requests, json
from tqdm import tqdm
import re

from utils.MongoUtil import MongoUtil

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

re_filters_xml = [
    re.compile('<\s*span[^>]*>[^<]*<\s*/\s*span\s*>', re.I),
    re.compile('"></script><a a="'),
    re.compile(r'//*?(?=]]>)'),
    re.compile('<br/>')
]

re_filters_name = re.compile('论|福|理')

nameFilter = ['幕后记录', '预告片', '花絮']

noteFilter = [
    '预告', '预告片', 'MV'
]
typeFilter = [
    '电影解说', '预告片', '电影说', '记录片', '综艺', '音乐MV', '音乐片', '综艺节目', '综艺片', '精英文艺', '微电影', '内地综艺', '大陆综艺', '音乐MTV', '纪录片',
    '欧美综艺', '歌曲MV', '游戏解说', '少儿频道', '高尔夫', '摩托车', '拳击', 'WWE摔跤娱乐', '橄榄球', '赛车', '解说', 'MMA综合格斗', 'VIP视频秀', '网球',
    '美女热舞写真', 'UFC终极格斗', '足球', '篮球', '棒球'
]


class Spider:

    def __init__(self):
        self.Mg = MongoUtil()

    def run(self, site_id=None):
        coll = self.Mg.getCol('site')
        res = coll.find()
        for site in res:
            # try:
            if 'data_type' in site and site['data_type'] == 'json':
                self.update_site_json(site)
                last_page = self.get_films_json(site)
            else:
                pass
                self.update_site(site, coll)
                last_page = self.get_films(site)
            coll.update_one({'_id': site['_id']}, {'$set': {'last_page': last_page}})
            # except:
            #     continue

            # last_page = self.get_films(site)
            # coll.update_one({'_id': site['_id']}, {'$set': {'last_page': last_page}})
        # self.fixClassify()

    # 过滤非法字符
    def filter_xml(self, str):
        str = str.strip()
        for x in re_filters_xml:
            str = re.sub(x, '', str)
        return str

    # 过滤电影
    def filter_film(self, name):
        if len(re.findall(re_filters_name, name)) > 0:
            return 1
        return 0

    # 更新总数和pagesize
    def update_site(self, site, coll):
        try:
            news = requests.get(site['api_url'], timeout=5)
            root = ET.fromstring(self.filter_xml(news.text))
        except:
            return
        _ns = root.find('list').attrib
        tyClass = root.find('class')
        configs = []
        for x in tyClass:
            configs.append({
                'ty': x.attrib['id'],
                'key': x.text
            })
        data = {
            'last_recordcount': int(_ns['recordcount']),
            'pagesize': int(_ns['pagesize']),
            'pagecount': int(_ns['pagecount']),
            'configs': configs
        }
        coll.update_one({'id': site['id']}, {"$set": data})

    def set_classify(self, site, tid):
        for x, y in site['classify'].items():
            if int(tid) in y:
                return int(x)
        return 0

    # 获取列表
    def get_films(self, _site):
        coll = self.Mg.getCol('films')
        siteColl = self.Mg.getCol('site')
        site = siteColl.find_one({'id': _site['id']})
        # 补一页
        page = site['last_page']
        last = int(site['pagecount']) - site['last_page'] if int(site['pagecount']) - site['last_page'] >= 0 else 0
        addNum = 0
        updateNum = 0
        sameNum = 0
        tqIt = tqdm(range(last * site['pagesize']), total=last,
                    desc=self.set_desc(site, page, addNum, updateNum, sameNum))
        for x in tqIt:
            siteColl.update_one({'_id': site['_id']}, {'$set': {'last_page': page}})
            url = site['api_url'] + '?ac=videolist&pg=%d' % page
            page += 1
            try:
                res = requests.get(url, timeout=20)
            except:
                return page

            try:
                root = ET.fromstring(res.text.strip())
            except:
                continue

            if len(root.find('list')) == 0:
                return page

            for child in root.find('list'):
                last -= 1
                film_name = child.find('name').text.upper() if child.find('name').text else ''
                note = child.find('note').text.upper() if child.find('note').text else ''
                video = []
                for v in child.find('dl'):
                    flag = v.attrib['flag']
                    if flag == '' or not v.text or len(list(v.text.split('#'))) == 0:
                        continue
                    video.append({
                        'key': flag,
                        'plist': list(v.text.split('#'))
                    })
                if len(video) == 0:
                    continue
                year = self.set_year(child.find('year').text)
                info = {
                    'film_name': film_name,
                    'tid': int(child.find('tid').text),
                    'pic': child.find('pic').text.strip() if child.find('pic').text else '',
                    'site_id': site['id'],
                    'state': int(self.filter_film(film_name)),
                    'des': child.find('des').text.strip() if child.find('des').text else '',
                    'type': child.find('type').text,
                    'area': child.find('area').text,
                    'year': int(year),
                    'douban_initial_year': int(year),
                    'classify': self.set_classify(site, int(child.find('tid').text)),
                    'note': note,
                    'video': video
                }
                if int(child.find('tid').text) not in site['filter_tid']:
                    continue

                old = coll.find_one({'film_name': film_name, 'note': note})
                if not old:
                    coll.insert_one(info)
                    addNum += 1
                else:
                    sameNum += 1
                    oldVideo = old['video'] if 'video' in old else []
                    coll.update_one({'_id': old['_id']}, {'$set': {'video': self.set_video(video, oldVideo)}})
                    # new_video_keys = list(map(lambda x: x['key'], video))
                    # old_video_keys = list(map(lambda x: x['key'], old['video']))
                    # difference = list(set(new_video_keys).difference(set(old_video_keys)))
                    # for newKey in difference:
                    #     newPlist = list(filter(lambda x: x['key'] == newKey, video))[0]
                    #     coll.update_one({'_id': old['_id']}, {'$addToSet': {'video': newPlist}})
                    updateNum += 1

                tqIt.set_description(desc=self.set_desc(site, page, addNum, updateNum, sameNum))
        return page

    # 更新总数和pagesize
    def update_site_json(self, site):
        coll = self.Mg.getCol('site')
        news = requests.get(site['api_url'], timeout=5)
        news = news.json()
        tyClass = news['class']
        configs = []
        for x in tyClass:
            configs.append({
                'ty': x['type_id'],
                'key': x['type_name']
            })
        if 'total' in news:
            data = {
                'last_recordcount': int(news['total']),
                'pagesize': int(news['limit']),
                'pagecount': int(news['pagecount']),
                'configs': configs
            }
        else:
            page = news['page']
            data = {
                'last_recordcount': int(page['recordcount']),
                'pagesize': int(page['pagesize']),
                'pagecount': int(page['pagecount']),
                'configs': configs
            }
        coll.update_one({'id': site['id']}, {"$set": data})

    def get_films_json(self, _site):
        coll = self.Mg.getCol('films')
        siteColl = self.Mg.getCol('site')
        site = siteColl.find_one({'id': _site['id']})
        # 补一页
        page = site['last_page']
        # 剩余页数
        last = int(site['pagecount']) - site['last_page']
        addNum = 0
        updateNum = 0
        sameNum = 0
        tqIt = tqdm(range(last * site['pagesize']),
                    desc=self.set_desc(site, page, addNum, updateNum, sameNum))

        for x in tqIt:
            siteColl.update_one({'_id': site['_id']}, {'$set': {'last_page': page}})
            # 参数:p页码,翻页;wd关键词;cid分类id; 可以实现全部数据/分类数据获取还有搜索数据
            url = site['api_url'] + '?ac=detail&pg=' + str(page)
            page += 1
            try:
                res = requests.get(url, timeout=20)
                root = res.json()
            except:
                return page

            if len(root['list']) == 0:
                return page

            for child in root['list']:
                last -= 1
                film_name = child['vod_name'].upper() if child['vod_name'] else ''
                note = child['vod_remarks'].upper() if child['vod_remarks'] else ''
                kkey = child['vod_play_from'].split('$$$')[1] if child['vod_play_from'].find('$$$') > -1 else child[
                    'vod_play_from']

                video = [{
                    'key': kkey,
                    'plist': child['vod_play_url'].split('#')
                }]
                if len(video) == 0 or int(child['type_id']) not in site['filter_tid']:
                    continue
                year = self.set_year(child['vod_year'])
                info = {
                    'film_name': film_name,
                    'tid': child['type_id'],
                    'pic': child['vod_pic'].strip() if child['vod_pic'] else '',
                    'site_id': site['id'],
                    'state': int(self.filter_film(film_name)),
                    'des': child['vod_content'].strip() if child['vod_content'] else '',
                    'type': child['type_name'],
                    'area': child['vod_area'],
                    'year': int(year),
                    'douban_initial_year': int(year),
                    'classify': self.set_classify(site, int(child['type_id'])),
                    'note': note,
                    'video': video
                }

                old = coll.find_one({'film_name': film_name, 'note': note})
                if not old:
                    coll.insert_one(info)
                    addNum += 1
                else:
                    sameNum += 1
                    oldVideo = old['video'] if 'video' in old else []
                    coll.update_one({'_id': old['_id']}, {'$set': {'video': self.set_video(video, oldVideo)}})
                    updateNum += 1

                tqIt.set_description(desc=self.set_desc(site, page, addNum, updateNum, sameNum))
        return page

    def set_year(self, old):
        old = re.sub(re.compile('普通话|年'), '', old)
        year = int(old) if old and 1970 < int(old) < 2021 else 1970
        return year

    def set_video(self, newV, oldV):
        new_video_keys = list(map(lambda x: x['key'], newV))
        for x in oldV:
            if x['key'] not in new_video_keys:
                newV.append(x)
        return newV

    def set_desc(self, site, page, addNum, updateNum, sameNum):
        return "[%s: %d, 总页数: %d, page: %d, 新增: %d, 修改: %d, 相同: %d]" % (
            site['site_name'], site['id'], site['pagecount'], page, addNum, updateNum, sameNum)

    def fixClassify(self):
        baseClassifyDict = {
            "1": [1, 5, 6, 7, 8, 9, 10, 11, 20, 21, 22, 23, 24, 25, 26, 27, 29],
            "2": [2, 12, 13, 14, 15, 16, 17, 18, 48, 54, 34, 33],
            "3": [3, 45, 38, 37],
            "4": [4, 41, 47, 28, 39, 40],
            "5": [49, 51, 42, 43, 55, 19],
            "6": [60, 44, 43, 42, 30],
            "49": [49, 51, 52, 53, 55, 19]
        }
        coll = self.Mg.getCol('films')
        site_list = self.Mg.getCol('site').find()

        for site in site_list:
            if 'type_change' in site:
                for t in site['type_change']:
                    coll.update_many({'site_id': site['id'], 'tid': int(t['ty']), 'new_tid': {"$exists": False}},
                                     {'$set': {'new_tid': int(t['change'])}})

        for (k, v) in baseClassifyDict.items():
            query = {"$or": [
                {
                    u"$and": [
                        {
                            u"new_tid": {
                                u"$exists": True
                            }
                        },
                        {
                            u"new_tid": {
                                u"$in": v
                            }
                        }
                    ]
                },
                {
                    u"$and": [
                        {
                            u"new_tid": {
                                u"$exists": False
                            }
                        },
                        {
                            u"tid": {
                                u"$in": v
                            }
                        }
                    ]
                }
            ], "classify": {
                u"$exists": False
            }}
            coll.update_many(query, {'$set': {'classify': k}})


if __name__ == '__main__':
    Spider().run()
    # Spider().fixClassify()
