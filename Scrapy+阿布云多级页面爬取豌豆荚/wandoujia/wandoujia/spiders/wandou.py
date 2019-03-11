# -*- coding: utf-8 -*-
import scrapy
import re
import json
from urllib.parse import urlencode
import logging

from wandoujia.items import WandoujiaItem


# 把日志输出到文件内
logging.basicConfig(filename="wandoujia.log",filemode="w",level=logging.DEBUG,
                    format="%(asctime)s %(message)s",datefmt="%Y/%m/%d %I/%M/%S %p")
logging.warning("warn message")
logging.error("error message")


class WandouSpider(scrapy.Spider):
    name = 'wandou'
    allowed_domains = ['www.wandoujia.com']
    start_urls = ['http://www.wandoujia.com/']

    def __init__(self):
        # 软件分类页面
        self.cate_url = "https://www.wandoujia.com/category/app"
        # 小分类，需主分类和子分类编号
        self.url = "https://www.wandoujia.com/category/"
        # ajax 请求url，需参数
        self.ajax_url = "https://www.wandoujia.com/wdjweb/api/category/more?"
        # 实例化分类标签
        self.wandou_category = Get_category()


    def start_requests(self):
        yield scrapy.Request(self.cate_url,callback=self.get_category)

    def get_category(self,response):
        cate_content = self.wandou_category.parse_category(response)
        for item in cate_content:
            child_cate = item["child_cate_codes"]
            for cate in child_cate:
                cate_code = item["cate_code"]     # 5029
                cate_name = item["cate_name"]     # 影音播放
                child_cate_code = cate["child_cate_code"]    # 716
                child_cate_name = cate["child_cate_name"]   # 视频

                page = 1
                logging.debug("正在爬取：%s-%s 第 %s 页" % (cate_name, child_cate_name, page))

                if page == 1:
                    # 构造首页url
                    category_url = '{}{}_{}'.format(self.url,cate_code,child_cate_code)
                else:
                    params ={
                        'catId':cate_code,
                        'subCatId':child_cate_code,
                        'page':page,
                        'ctoken': 'kamD4KvHwl9PwHYkn3CsZomD'
                    }
                    category_url = self.ajax_url + urlencode(params)

                    dict = {'page': page, 'cate_name': cate_name, 'cate_code': cate_code,
                            'child_cate_name': child_cate_name, 'child_cate_code': child_cate_code}

                    yield scrapy.Request(category_url,callback=self.parse,meta=dict)

    def parse(self,response):
        if len(response.body) >= 100:
            page = response.meta['page']
            cate_name = response.meta['cate_name']
            cate_code = response.meta['cate_code']
            child_cate_name = response.meta['child_cate_name']
            child_cate_code = response.meta['child_cate_code']

            if page == 1:
                contents = response
            else:
                jsonresponse = json.loads(response.body_as_unicode())
                contents = jsonresponse['data']['content']
                contents = scrapy.Selector(text=contents,type="html")

            contents = contents.css('.card')
            for content in contents:
                item = WandoujiaItem()
                item['cate_name'] = cate_name
                item['child_cate_name'] = child_cate_name
                item['app_name'] = self.clean_name(content.css('.name::text').extract_first())
                item['install'] = content.css('.install-count::text').extract_first()
                item['volume'] = content.css('.meta span:last-child::text').extract_first()
                item['comment'] = content.css('.comment::text').extract_first().strip()
                item['icon_url'] = self.get_icon_url(content.css('.icon-wrap a img'),page)
                yield item

            page += 1
            params = {
                'catId':cate_code,
                'subCatId':child_cate_code,
                'page':page,
                'ctoken': 'kamD4KvHwl9PwHYkn3CsZomD'
            }
            ajax_url = self.ajax_url + urlencode(params)

            dict = {'page': page, 'cate_name': cate_name, 'cate_code': cate_code,
                    'child_cate_name': child_cate_name, 'child_cate_code': child_cate_code}

            yield scrapy.Request(ajax_url, callback=self.parse, meta=dict)

    # 去除不能用于文件命名的特殊字符
    def clean_name(self,name):
        pattern = re.compile(r'[\/\\\:\*\?\"\<\>\|]')
        name = re.sub(pattern, '', name)
        return name

    def get_icon_url(self,item,page):
        if page == 1:
            if item.css('::attr("src")').extract_first().startswith('https'):
                url = item.css('::attr("src")').extract_first()
            else:
                url = item.css('::attr("data-original")').extract_first()
        else:
            url = item.css('::attr("data-original")').extract_first()
        return url


# 获得主分类和子分类的编号
class Get_category():
    def parse_category(self,response):
        category = response.css(".parent-cate")
        data = [{
            "cate_name": item.css(".cate-link::text").extract_first(),
            "cate_code": self.get_category_code(item),
            "child_cate_codes": self.get_child_category(item)
        } for item in category]
        return data

    # 提取主分类编号
    def get_category_code(self,item):
        cate_url = item.css('.cate-link::attr("href")').extract_first()
        pattern = re.compile(r".*/(\d+)")
        cate_code = re.search(pattern,cate_url)
        return cate_code.group(1)


    # 获取所有子分类标签数值编码
    def get_child_category(self,item):
        child_cate = item.css('.child-cate a')
        child_cate_url = [{
            "child_cate_name": child.css('::text').extract_first(),
            "child_cate_code": self.get_child_category_code(child)
        } for child in child_cate]
        return child_cate_url

    # 提取子分类的编号
    def get_child_category_code(self,child):
        child_cate_url = child.css('::attr("href")').extract_first()
        pattern = re.compile(r'.*_(\d+)')
        child_cate_code = re.search(pattern,child_cate_url)
        return child_cate_code.group(1)









