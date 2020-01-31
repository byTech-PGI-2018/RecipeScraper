# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

MAIN_LINK = 'https://www.teleculinaria.pt/receitas/page/%s/'

ALLOW_PATTERN = r'/receitas/[A-Za-z0-9]+'  # Needs to have something after the '/'

class TeleculinariaSpider(CrawlSpider):
    name = 'teleculinaria'

    rules = (
        Rule(
            LinkExtractor(
                restrict_xpaths = ['//div[@class="td-block-span6"]//h3[@class="entry-title td-module-title"]'],
                allow = ALLOW_PATTERN,
            ),
            follow = False,
            callback = 'parse_items'
        ),
    )

    def __init__(self, pagestart='', pageend='', **kwargs):
        self.start_urls = [MAIN_LINK % i for i in range(int(pagestart), int(pageend) + 1)]

        super().__init__(**kwargs)

    def parse_items(self, response):
        new_dictionary = {}

        new_dictionary['name'] = response.xpath('//h1[@class="entry-title"]/text()').extract_first()
        new_dictionary['url'] = response.request.url

        yield new_dictionary
