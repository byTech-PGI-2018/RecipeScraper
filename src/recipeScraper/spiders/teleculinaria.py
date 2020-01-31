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
        new_recipe = {}

        new_recipe['name'] = response.xpath('//h1[@class="entry-title"]/text()').extract_first()
        new_recipe['url'] = response.request.url

        # The recipe may not have these properties, but add them anyway for consistency
        new_recipe['gastronomia'] = ""
        new_recipe['tipo'] = ""
        new_recipe['dificuldade'] = ""
        new_recipe['calorias'] = ""
        new_recipe['porção'] = ""
        new_recipe['custo'] = ""
        new_recipe['tempo'] = ""
        new_recipe['dificuldade'] = ""

        # Try to get dish type
        try:
            new_recipe['tipo'] = response\
                .xpath('//div[@class="wpurp-recipe-tags-refeição"]//a/text()')\
                .extract_first()
        except:
            self.logger.debug('Recipe has no dish type property in: ',
                args=response.request.url)

        # Try to get dish difficulty
        try:
            new_recipe['dificuldade'] = response\
                .xpath('//div[@class="wpurp-recipe-tags-grau-de-dificuldade"]//a/text()')\
                .extract_first()
        except:
            self.logger.debug('Recipe has no dish difficulty property in: ',
                args=response.request.url)

        # Try to get dish cost
        try:
            new_recipe['custo'] = response\
                .xpath('//div[@class="wpurp-recipe-tags-custo-da-refeição"]//a/text()')\
                .extract_first()
        except:
            self.logger.debug('Recipe has no dish difficulty property in: ',
                args=response.request.url)

        # Try to get dish preparation time
        try:
            new_recipe['tempo'] = response\
                .xpath('concat(//span[@class="wpurp-recipe-prep-time"], " ", //span[@class="wpurp-recipe-prep-time-text"]/text())')\
                .extract_first()
        except:
            self.logger.debug('Recipe has no dish prep time property in: ',
                args=response.request.url)

        # Try to get dish portion value
        try:
            new_recipe['porção'] = response\
                .xpath('concat(string(//input[@type="number"]/@data-original), " ", //span[@class="wpurp-recipe-servings-changer"]/text())')\
                .extract_first().replace("  ", " ")
        except:
            self.logger.debug('Recipe has no dish prep time property in: ',
                args=response.request.url)

        # Get recipe ingredients
        ingredients = response.xpath('//ul[@class="wpurp-recipe-ingredient-container"]/li')

        new_recipe_ingredients = {}
        new_recipe_quantities = {}

        for i, ingredient in enumerate(ingredients[:len(ingredients)//2]):
            quantity = ingredient\
                .xpath('concat(string(descendant::span[@class="wpurp-recipe-ingredient-quantity"]/@data-original), " ",descendant::span[@class="wpurp-recipe-ingredient-unit"]/text()," ", descendant::span[@class="wpurp-recipe-ingredient-name"]//a/text())')\
                .extract_first()\
                .strip()\
                .replace("  ", " ")

            i_data = ingredient\
                .xpath('descendant::span[@class="wpurp-recipe-ingredient-name"]//a/text()')\
                .extract_first()\
                .strip()

            # Remove q.b. from ingredient
            #if 'q.b.' in i_data.split(" "):
            i_data = i_data.replace('q.b.', '').strip()

            # If ingredient starts with 'de', remove it
            i_data_split = i_data.split(' ')
            if i_data_split[0] == 'de':
                i_data = " ".join(i_data_split[1:]).strip().replace('  ', ' ')

            new_recipe_quantities[i] = quantity
            new_recipe_ingredients[i] = i_data

        new_recipe['ingredients'] = new_recipe_ingredients
        new_recipe['quantidade'] = new_recipe_quantities

        new_recipe_prep = {}

        # Get preparation
        preparation = response.xpath('//ol[@class="wpurp-recipe-instruction-container"]/li')

        for i, step in enumerate(preparation):
            new_recipe_prep[i] = step.xpath('descendant::span[@class="wpurp-recipe-instruction-text"]/text()')\
                .extract_first()\
                .strip()

        new_recipe['preparação'] = new_recipe_prep

        yield new_recipe
