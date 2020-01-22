# -*- coding: utf-8 -*-
import json
import re
import scrapy

# Max: 215

# URL to make AJAX requests
AJAX_URL = 'http://www.receitasdeportugal.com/?infinity=scrolling'

# Form data to include in the AJAX request
AJAX_DATA = {
    'action': 'infinite_scroll',
    'page': '1',
    'order': 'DESC'
}

# List of possible xpath queries for ingredients and quantities
INGREDIENTS_XPATH = [
    '//*[@class="ingredient-item-name"]',
    '//*[@class="ingredient"]',
    '//*[@class="shortcode-ingredients"]/ul/li',
    '//*[@class="ingredients-list"]/li'
]

# List of possible xpath queries for preparation steps
PREPARATION_XPATH = [
    '//*[@class="direction-step"]',
    '//*[@class="text_exposed_show"]',
    '//*[@class="instruction"]',
    '//*[@class="instructions"]/li',
    '//*[@class="directions-list"]/li'
]


def get_valid_nodes(response, xpath_list):
    '''
    Try to get a non empty list of XML nodes from a selection of xpath
    queries

    Arguments:
        response -- XML document
        xpath_list -- List of strings each representing xpath query

    Returns:
        None if no XML nodes could be found, and a list of XML nodes
        otherwise
    '''
    for query in xpath_list:
        elements = response.xpath(query)

        # If list of nodes is not empty
        if elements.extract():
            return elements

    return None


class ReceitasPortugalSpider(scrapy.Spider):
    name = 'receitas_portugal'

    def __init__(self, **kwargs):
        # Starting URL, irrelevant, since all links will be extracted \
        # from AJAX requests
        self.start_urls = ['http://www.receitasdeportugal.com/receitas/']

        super().__init__(**kwargs)

    def parse_ajax(self, response):
        # Load received response as a JSON
        received = json.loads(response.body)

        # Check if we haven't reached last page
        if received['type'] != 'empty':
            # Parse received URL's one by one (* unpacks keys)
            for url in [*received['postflair']]:
                yield scrapy.Request(url, callback=self.parse_item)

            # Check if we reached limit of pages to search
            if int(self.pagestart) >= int(self.pageend):
                self.logger.info('Reached limit of pages to crawl')
                return

            # Increase the page counter we're requesting
            self.pagestart = str(int(self.pagestart)+1)

            # Change the page in the form data
            AJAX_DATA['page'] = self.pagestart

            # Make next AJAX request
            yield scrapy.FormRequest(
                AJAX_URL, formdata=AJAX_DATA, callback=self.parse_ajax)

        else:
            self.logger.info('No more recipes to crawl')

    def parse_item(self, response):
        # Start making a new dicionary entry
        new_recipe = {}

        # Extract recipe name and URL
        new_recipe['name'] = response\
            .xpath('//*[@class="entry-title fn"]/text()')\
            .extract_first()

        new_recipe['url'] = response.request.url

        # For now, assume these properties don't exist, if they do, they will \
        # be updated
        new_recipe['gastronomia'] = ''
        new_recipe['tipo'] = ''
        new_recipe['custo'] = ''
        new_recipe['calorias'] = ''
        new_recipe['dificuldade'] = ''
        new_recipe['tempo'] = ''
        new_recipe['porção'] = ''
        new_recipe['vegan'] = False

        # Try to get dish type
        try:
            new_recipe['tipo'] = response\
                .xpath('//*[@class="entry-category"]/a[1]/text()') \
                .extract_first()
        except:
            self.logger.debug('Recipe has no "dish type" property, in: '
                              + response.request.url)

        # Try to check if recipe is vegan or not
        try:
            vegan = response\
                .xpath('//*[@class="entry-category"]/a[1]/text()')\
                .extract_first()

            if vegan == 'Vegetariano':
                new_recipe['vegan'] = True
        except:
            self.logger.debug('Recipe has no "vegan" property, in: '
                              + response.request.url)

        # Create new dictionaries to hold ingredients and quantities
        new_recipe_ingredients = {}
        new_recipe_quantities = {}

        # Pattern to discard ingredient unit-related stuff
        pattern = \
            re.compile('(([0-9]*\.)?[0-9]+(kg|mg|dl|l|ml|g|gr|grs|(colheres)|\
                (colher)|(colh.))?)|^(kg|mg|dl|l|ml|g|gr|grs|(colheres)|(colher)|\
                (colh.))$', re.IGNORECASE)  # pylint: disable=anomalous-backslash-in-string

        # Get ingredient and quantity info
        ingredients = get_valid_nodes(response, INGREDIENTS_XPATH)

        if ingredients is None:
            return

        # Iterate over all extracted elements
        for i, ingredient_selector in enumerate(ingredients):
            # Extract every text node in the <li> tag, also joining \
            # any child node text
            ingredient = ingredient_selector\
                .xpath('normalize-space(string(descendant-or-self::*))')\
                .extract_first().strip()

            # Since everything is just one string, add it to \
            # quantities dictionary
            new_recipe_quantities[i] = ingredient

            # Assume no ingredient was found for current i, for consistency
            new_recipe_ingredients[i] = ''

            # For single ingredients, additional parsing will be needed
            words = ingredient.split()

            # If the sentence has 'q.b.' anywhere, add every word but 'q.b.'
            if 'q.b.' in words:
                words.remove('q.b.')
                new_recipe_ingredients[i] = " ".join(words).strip()

            # If not, then iterate over every single word
            else:
                for j, word in enumerate(words):
                    # If current word matches 'de', just add the \
                    # rest as ingredient
                    if word and (word in "de"):
                        new_recipe_ingredients[i] = " ".join(words[j+1:]).strip()
                        break

                    # If the word matches a unit-related pattern \
                    # (if it's 100ml, 100, 100kg, etc.), continue the loop \
                    # (ignore it)
                    elif word and (bool(pattern.match(word))):
                        pass

                    # If word doesn't match anything, then just add it and \
                    # the rest of the words as the ingredient
                    else:
                        new_recipe_ingredients[i] = " ".join(words[j:]).strip()
                        break

        # Add the newly created dictionaries to root dictionary
        new_recipe['ingredients'] = new_recipe_ingredients
        new_recipe['quantidade'] = new_recipe_quantities

        # Create a new dictionary that will hold preparation steps
        new_recipe_instructions = {}

        # Get all instructions (only a non empty list of elements)
        preparation = get_valid_nodes(response, PREPARATION_XPATH)

        if preparation is None:
            return

        # Iterate over every preparation step
        for i, step in enumerate(preparation):
            new_recipe_instructions[i] = step\
                .xpath('normalize-space(string(descendant-or-self::*))')\
                .extract_first()

        # Add preparation dictionary to root dictionary
        new_recipe['preparação'] = new_recipe_instructions

        yield new_recipe

    def parse(self, response):
        # Check if we received required arguments \
        # (and that they can be parsed with int())
        try:
            if int(self.pagestart) and int(self.pageend):
                pass

        except ValueError:
            self.logger.critical('Argument error. Not valid integers')
            return

        except AttributeError:
            self.logger.critical('Argument error. Required: -a pagestart=<n> -a pageend=<m>')
            return

        # Check if pageend is greater or equal than pagestart
        if int(self.pageend) < int(self.pagestart):  # pylint: disable=no-member
            self.logger.critical('Ending page cannot be smaller than starting page.')
            return

        # Make first AJAX request
        AJAX_DATA['page'] = self.pagestart

        yield scrapy.FormRequest(
            AJAX_URL, formdata=AJAX_DATA, callback=self.parse_ajax)
