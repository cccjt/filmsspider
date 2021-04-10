import re
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from bson.objectid import ObjectId

import site_config
from utils.MongoUtil import MongoUtil

app = Flask(__name__)
# 实现跨域访问
cors = CORS(app, resources={r"*": {"origins": "*"}})
Mg = MongoUtil()

film_filters = [
    {
        'key': 'classify',
        'list': [
            {'name': '电影', 'value': 1}, {'name': '连续剧', 'value': 2}, {'name': '动漫', 'value': 3},
            {'name': '综艺', 'value': 5}
        ]
    },
    {
        'key': 'order',
        'list': [
            {'name': '最新上映'}, {'name': '评分最高'}, {'name': '最多推荐'}
        ]
    },
    {
        'key': 'area',
        'list': [
            {'name': '全部地区'}, {'name': '中国大陆'}, {'name': '美国'}, {'name': '中国'},
            {'name': '香港'}, {'name': '中国台湾'}, {'name': '日本'}, {'name': '韩国'}, {'name': '英国'}, {'name': '法国'},
            {'name': '德国'}, {'name': '意大利'}, {'name': '西班牙'}, {'name': '印度'}, {'name': '泰国'}, {'name': '俄罗斯'},
            {'name': '伊朗'}, {'name': '加拿大'}, {'name': '澳大利亚'}
        ]
    },
    {
        'key': 'genre',
        'list': [
            {'name': '全部类型'}, {'name': '剧情'}, {'name': '喜剧'}, {'name': '动作'}, {'name': '爱情'}, {'name': '科幻'},
            {'name': '动画'}, {'name': '悬疑'}, {'name': '惊悚'}, {'name': '恐怖'}, {'name': '犯罪'}, {'name': '同性'},
            {'name': '音乐'}, {'name': '歌舞'}, {'name': '传记'}, {'name': '历史'}, {'name': '战争'}, {'name': '西部'},
            {'name': '奇幻'}, {'name': '冒险'}, {'name': '灾难'}, {'name': '武侠'}, {'name': '情色'}
        ]
    },
    {
        'key': 'year',
        'list': [
            {'name': '全部年份'}, {'name': '2021'}, {'name': '2020'}, {'name': '2019'},
            {'name': '2018'}, {'name': '2017'}, {'name': '2016'}, {'name': '2015'},
            {'name': '2014'}, {'name': '2013'}, {'name': '2012'}, {'name': '2011'},
            {'name': '2010'}
        ]
    }
]


@app.route('/')
def index():
    return ''


@app.route('/getClassify', methods=['get'])
def getFilters():
    secret = request.headers.get('secret', type=str, default='')
    if secret != '' and secret == site_config.config_secret:
        film_filters[0]['list'].append({"name": "伦理", 'value': 49})
    return success(film_filters)


@app.route('/getFilmList', methods=['POST'])
def get_film_list():
    # film_filters = getFilm_silters()
    filmsColl = Mg.getCol("films")
    form = request.values
    secret = request.headers.get('secret', type=str, default='')
    pagesize = form.get('pagesize', type=int, default=60)
    page = form.get('page', type=int, default=1)
    keyword = form.get('keyword', type=str, default='')

    classify = form.get('classify', type=int, default=0)
    area = form.get('area', type=int, default=0)
    genre = form.get('genre', type=int, default=0)
    year = form.get('year', type=int, default=0)

    order_index = form.get('order', type=int, default=0)

    where = {}
    classifyVal = film_filters[0]['list'][classify]['value']
    where['classify'] = int(classifyVal)

    if keyword:
        where['film_name'] = {'$regex': keyword}

    if area > 0:
        country = film_filters[2]['list'][area]['name']
        where['$or'] = [{"douban_country": {'$regex': country}}, {"area": {'$regex': country}}]

    if genre > 0:
        genrestr = film_filters[3]['list'][genre]['name']
        where['douban_genre'] = {'$regex': genrestr}

    if year > 0:
        yearstr = film_filters[4]['list'][year]['name']
        where['douban_initial_year'] = int(yearstr)

    if order_index == 0:
        sort = [('douban_initial_year', -1), ('douban_initial_date', -1)]
    elif order_index == 1:
        sort = [('douban_rating', -1)]
    else:
        sort = [("recommend", -1)]
    # print(where)
    res = filmsColl.find(where,
                         {'_id': 1, 'film_name': 1, 'douban_initial_date': 1, 'douban_initial_year': 1,
                          'douban_rating': 1,
                          'douban_pic': 1, 'pic': 1}).limit(pagesize).skip(pagesize * (page - 1)).sort(sort)
    rows = []
    for x in res:
        x['_id'] = str(x['_id'])
        rows.append(x)

    data = {
        'rows': rows,
        'total': filmsColl.count_documents(where)
    }
    return success(data)

film_name_re = re.compile('第\w+季|_|超清|(\d+集全)|\d+|剧场版|\(|\)|普通话|版')

@app.route('/getFilmInfo', methods=['POST'])
def get_film_info():
    filmsColl = Mg.getCol("films")
    form = request.form
    _id = form.get('id', type=str, default=None)
    secret = request.headers.get('secret', type=str, default='')
    if _id:
        info = filmsColl.find_one({'_id': ObjectId(_id)})
        info['recommend'] = []
        film_name = re.sub(film_name_re, '', info['film_name']).strip()
        # print(film_name)
        recommend = filmsColl.find(
            {'film_name': {'$regex': film_name}, '_id': {'$ne': info['_id']}, 'classify': info['classify']},
            {'_id': 1, 'douban_rating': 1, 'douban_initial_date': 1, 'initial_year': 1,
             'douban_country': 1, 'douban_pic': 1, 'pic': 1, 'film_name': 1, 'note': 1,
             'area': 1}).limit(12)
        for x in recommend:
            x['_id'] = str(x['_id'])
            info['recommend'].append(x)

        if secret == site_config.config_secret:
            info['isAdmin'] = True
        info['_id'] = str(info['_id'])
        return success(info)
    return jsonify({'code': 1})


@app.route('/upRecommend', methods=['POST'])
def upRecommend():
    filmsColl = Mg.getCol("films")
    form = request.form
    _id = form.get('id', type=str, default=None)
    if _id:
        filmsColl.update_one({'_id': ObjectId(_id)}, {'$inc': {'recommend': 1}})
    return jsonify({'code': 0})


@app.route('/reportErr', methods=['POST'])
def report_err():
    filmsColl = Mg.getCol("films")
    form = request.form
    fid = form.get('id', type=str, default=None)
    if fid:
        filmsColl.update_one({'_id': ObjectId(fid)}, {'$set': {'douban_state': 1}})
    return jsonify()


def success(data, info=''):
    if type(data).__name__ == 'list':
        for x in data:
            if '_id' in x:
                x['_id'] = str(x['_id'])
    return jsonify({'code': 0, 'info': info, 'data': data})


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
