import requests

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from utils.MongoUtil import MongoUtil


def insert_site():
    ss = {'id': 34, 'site_key': 'okzy',
          'api_url': 'https://api.okzy.tv/api.php/provide/vod/at/json/?ac=detail', 'site_name': 'okzy',
          'configs': [{'type_id': 1, 'type_name': '电影'}, {'type_id': 2, 'type_name': '连续剧'},
                      {'type_id': 3, 'type_name': '综艺'}, {'type_id': 4, 'type_name': '动漫'},
                      {'type_id': 5, 'type_name': '资讯'}, {'type_id': 6, 'type_name': '动作片'},
                      {'type_id': 7, 'type_name': '喜剧片'}, {'type_id': 8, 'type_name': '爱情片'},
                      {'type_id': 9, 'type_name': '科幻片'}, {'type_id': 10, 'type_name': '恐怖片'},
                      {'type_id': 11, 'type_name': '剧情片'}, {'type_id': 12, 'type_name': '战争片'},
                      {'type_id': 13, 'type_name': '国产剧'}, {'type_id': 14, 'type_name': '香港剧'},
                      {'type_id': 15, 'type_name': '韩国剧'}, {'type_id': 16, 'type_name': '欧美剧'},
                      {'type_id': 17, 'type_name': '公告'}, {'type_id': 18, 'type_name': '头条'},
                      {'type_id': 20, 'type_name': '纪录片'}, {'type_id': 21, 'type_name': '微电影'},
                      {'type_id': 22, 'type_name': '台湾剧'}, {'type_id': 23, 'type_name': '日本剧'},
                      {'type_id': 24, 'type_name': '海外剧'}, {'type_id': 25, 'type_name': '内地综艺'},
                      {'type_id': 26, 'type_name': '港台综艺'}, {'type_id': 27, 'type_name': '日韩综艺'},
                      {'type_id': 28, 'type_name': '欧美综艺'}, {'type_id': 29, 'type_name': '国产动漫'},
                      {'type_id': 30, 'type_name': '日韩动漫'}, {'type_id': 31, 'type_name': '欧美动漫'},
                      {'type_id': 32, 'type_name': '港台动漫'}, {'type_id': 33, 'type_name': '海外动漫'},
                      {'type_id': 34, 'type_name': '福利片'}, {'type_id': 35, 'type_name': '解说'},
                      {'type_id': 36, 'type_name': '电影解说'}, {'type_id': 37, 'type_name': '伦理片'}],
          'data_type': 'json',
          'filter_tid': [3, 5, 17, 18, 20, 21, 22, 25, 26, 27, 28, 35, 36]}
    Mg = MongoUtil()
    siteColl = Mg.getCol('site')
    siteColl.insert_one(ss)


def get_site():
    Mg = MongoUtil()
    siteColl = Mg.getCol('site')
    res = siteColl.find({'id': 8})
    print(list(res)[0])


def resolveAddress():
    url = 'https://api.okzy.tv/api.php/provide/vod/at/json/?ac=list'
    res = requests.get(url)
    root = res.json()
    print(root['class'])

    # root = ET.fromstring(res.text)
    # _class = root.find('class')
    # config = []
    # for x in _class.findall('ty'):
    #     config.append({
    #         'ty': x.attrib['id'],
    #         'key': x.text
    #     })
    # print(config)
    # # print(_class)


if __name__ == '__main__':
    resolveAddress()
    # insert_site()
