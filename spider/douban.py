import re
import requests
import js2py

url = f'https://search.douban.com/movie/subject_search?search_text=%E7%AC%AC%E5%8D%81%E4%B8%80%E5%9B%9E&cat=1002'
r = requests.get(url)
data = re.findall(r'window.__DATA__ = "(.*?)";', r.content.decode('utf-8'))[0]

with open('douban-decryption.js', 'r', encoding='utf-8') as f:
    js = f.read()
    jsCode = js2py.EvalJs()
    jsCode.execute(js)
    print(jsCode)
    resul = jsCode.decrypt(data)
    print(resul)

