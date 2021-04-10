import asyncio
import re

import requests
from pyppeteer import launch
from tqdm import tqdm

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from utils.MongoUtil import MongoUtil


str = '113306末日杀戮(原声版)'

def filter_film_name(name):
        # 过滤电影名称
        filter_re = re.compile("超清720P|高清\w*|%|\.|'|\\n|       |\u3000\u3000|（\w+）|普通话版|粤语版|\((.*)\)")
        return re.sub(filter_re, '', name).strip()

print(filter_film_name(str))
