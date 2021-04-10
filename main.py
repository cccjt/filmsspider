from spider.spider import Spider

Spider().run()
# change_classify.updateClassify()
#
# DoubanSpider().run_search_link()
# DoubanSpider().run_search_info()

# # 修复动画类型
# Db.update("update film_list set classify=4 where douban_genre like '%动画%'")
# Db.update("update film_list set classify=4 where douban_genre like '%真人秀%'")
# Db.update("update film_list set classify=2 where classify=1 and film_name like '%第%' and film_name like '%季%'")
# Db.update("update film_list set classify=2 where classify=1 and film_name like '%第%' and film_name like '%集%'")
# # 修复日期
# Db.update("update film_list set douban_initial_year=1980,douban_initial_date='1980-01-01' where douban_initial_year > 2021")


