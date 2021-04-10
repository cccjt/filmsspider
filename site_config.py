# filters = [
#     {
#         'key': 'classify',
#         'list': [{'name': '电影', 'value': 1}, {'name': '连续剧', 'value': 2},
#                  {'name': '动漫', 'value': 3}, {'name': '综艺', 'value': 3}, {"name": "其他", 'value': 6}]
#     },
#     {
#         'key': 'order',
#         'list': [{'name': '综合排序'}, {'name': '评分排序'}, {'name': '上映日期排序'}]
#     },
#     {
#         'key': 'area',
#         'list': [{'name': '全部地区'}, {'name': '中国'}, {'name': '中国香港'}, {'name': '中国台湾'}, {'name': '美国'}, {'name': '韩国'},
#                  {'name': '日本'},
#                  {'name': '泰国'}, {'name': '印度'}]
#     },
#     {
#         'key': 'genre',
#         'list': [{'name': '全部类型'}, {'name': '黑色电影'}, {'name': '爱情'}, {'name': '奇幻'}, {'name': '武侠'}, {'name': '荒诞'},
#                  {'name': '歌舞'},
#                  {'name': '运动'}, {'name': '鬼怪'}, {'name': '动画'}, {'name': '犯罪'}, {'name': '音乐'}, {'name': '儿童'},
#                  {'name': '纪录片'}, {'name': '家庭'}, {'name': '舞台艺术'}, {'name': '科幻'}, {'name': '悬疑'}, {'name': '脱口秀'},
#                  {'name': '惊悚'}, {'name': '历史'}, {'name': '传记'}, {'name': '惊栗'}, {'name': '西部'}, {'name': '情色'},
#                  {'name': '灾难'}, {'name': '同性'}, {'name': '恐怖'}, {'name': '战争'}, {'name': '真人秀'}, {'name': '戏曲'},
#                  {'name': '短片'}, {'name': '冒险'}, {'name': '动作'}, {'name': '剧情'}, {'name': '古装'}, {'name': '喜剧'}
#                  ]
#     },
#     {
#         'key': 'year',
#         'list': [{'name': '全部年份'}, {'name': '2021'}, {'name': '2020'}, {'name': '2019'}, {'name': '2018'},
#                  {'name': '2017'}, {'name': '2016'}, {'name': '2015'}, {'name': '2014'}, {'name': '2013'},
#                  {'name': '2012'}, {'name': '2011'}, {'name': '2010'}]
#     }
# ]



config_secret = 'ccchaha'

DB_CONFIG = {
    "host": "localhost",
    "port": 3308,
    "user": "root",
    "passwd": "123456",
    "db": "myvideo",
    "charset": "utf8mb4"
}

MONGO_CONFIG = {
    "host": "s2.anpaitm.com",
    "port": 27017,
    "username": "kdy222",
    "password": "ba7c9bcec7a",
    "db": "kdy222"
}
