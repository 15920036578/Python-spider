# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item,Field


class WandoujiaItem(Item):
    collection = "wandou"

    cate_name = Field()         # 分类名
    child_cate_name = Field()   # 分类编号
    app_name = Field()          # 子分类名
    install = Field()           # 子分类编号
    volume = Field()             # 体积
    comment = Field()           # 评论
    icon_url = Field()           # 图表url



