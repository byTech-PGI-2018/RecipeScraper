# -*- coding: utf-8 -*-
import scrapy
import json
import re

# Max: 215

# URL to make AJAX requests
ajaxUrl = 'http://www.receitasdeportugal.com/?infinity=scrolling'

# Form data to include in the AJAX request
ajaxdata = {
    'action': 'infinite_scroll',
    'page': '1',
    'order': 'DESC'
}

class ReceitasPortugalSpider(scrapy.Spider):
    name = 'receitas_portugal'
    #start_urls = ['http://www.receitasdeportugal.com/receitas/']

    def __init__(self, **kwargs):
        # Starting URL, irrelevant, since all links will be extracted from AJAX requests
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
            ajaxdata['page'] = self.pagestart

            # Make next AJAX request
            yield scrapy.FormRequest(ajaxUrl, formdata=ajaxdata, callback=self.parse_ajax)

        else:
            self.logger.info('No more recipes to crawl')


    def parse_item(self, response):
        # Start making a new dicionary entry
        newRecipe = {}

        # Extract recipe name and URL
        newRecipe['name'] = response.xpath('//*[@class="entry-title fn"]/text()').extract_first()
        newRecipe['url'] = response.request.url

        # For now, assume these properties don't exist, if they do, they will be updated
        newRecipe['gastronomia'] = ''
        newRecipe['tipo'] = ''
        newRecipe['custo'] = ''
        newRecipe['calorias'] = ''
        newRecipe['dificuldade'] = ''
        newRecipe['tempo'] = ''
        newRecipe['porção'] = ''
        newRecipe['vegan'] = False

        # Try to get dish type
        try:
            newRecipe['tipo'] = response.xpath('//*[@class="entry-category"]/a[1]/text()').extract_first()
        except:
            self.logger.debug('Recipe has no "dish type" property, in: ' + response.request.url)

        # Try to check if recipe is vegan or not
        try:
            vegan = response.xpath('//*[@class="entry-category"]/a[1]/text()').extract_first()
            if vegan == 'Vegetariano':
                newRecipe['vegan'] = True
        except:
            self.logger.debug('Recipe has no "vegan" property, in: ' + response.request.url)

        # Create new dictionaries to hold ingredients and quantities
        newRecipeIngredients = {}
        newRecipeQuantities = {}

        # Pattern to discard ingredient unit-related stuff
        pattern = re.compile('(([0-9]*\.)?[0-9]+(kg|mg|dl|l|ml|g|gr|grs|(colheres)|(colher)|(colh.))?)|^(kg|mg|dl|l|ml|g|gr|grs|(colheres)|(colher)|(colh.))$', re.IGNORECASE) # pylint: disable=anomalous-backslash-in-string

        # Get ingredient and quantity info
        ingredients = response.xpath('//*[@class="ingredients-list"]/descendant::*[@class="ingredient-item"]')

        # Iterate over all extracted elements
        for i, ingredientSelector in enumerate(ingredients):
            # Extract every text node in the <li> tag, also joining any child node text
            ingredient = ingredientSelector.xpath('normalize-space(string(descendant-or-self::*))').extract_first().strip()

            # Since everything is just one string, add it to quantities dictionary
            newRecipeQuantities[i] = ingredient

            # Assume no ingredient was found for current i, for consistency
            newRecipeIngredients[i] = ''

            # For single ingredients, additional parsing will be needed
            words = ingredient.split()

            # If the sentence has 'q.b.' anywhere, add every word but 'q.b.'
            if 'q.b.' in words:
                words.remove('q.b.')
                newRecipeIngredients[i] = " ".join(words).strip()
            
            # If not, then iterate over every single word
            else:
                for j, word in enumerate(words):
                    # If current word matches 'de', just add the rest as ingredient
                    if word and (word in "de"):
                        newRecipeIngredients[i] = " ".join(words[j+1:]).strip()
                        break

                    # If the word matches a unit-related pattern (if it's 100ml, 100, 100kg, etc.), continue the loop (ignore it)
                    elif word and (bool(pattern.match(word))):
                        pass

                    # If the word doesn't match anything, then just add it and the rest of the words as the ingredient
                    else:
                        newRecipeIngredients[i] = " ".join(words[j:]).strip()
                        break

        # Add the newly created dictionaries to root dictionary
        newRecipe['ingredients'] = newRecipeIngredients
        newRecipe['quantidade'] = newRecipeQuantities

        # Create a new dictionary that will hold preparation steps
        newRecipeInstructions = {}

        # Get all instructions
        preparation = response.xpath('//*[@class="directions-list"]/descendant::*[@class="direction-step"]')

        # Iterate over every preparation step
        for i, step in enumerate(preparation):
            newRecipeInstructions[i] = step.xpath('normalize-space(string(descendant-or-self::*))').extract_first()

        # Add preparation dictionary to root dictionary
        newRecipe['preparação'] = newRecipeInstructions

        yield newRecipe

    def parse(self, response):
        # Check if we received required arguments (and that they can be parsed with int())
        try:
            if int(self.pagestart) and int(self.pageend):
                pass
        except:
            self.logger.critical('Argument error. Required: -a pagestart=<n> -a pageend=<m>, \
                                 where n and m are integers n > 0 and m >= n')
            return

        # Check if pageend is greater or equal than pagestart
        if int(self.pageend) < int(self.pagestart):
            self.logger.critical('Ending page cannot be smaller than starting page.')
            return

        # Make first AJAX request
        ajaxdata['page'] = self.pagestart

        yield scrapy.FormRequest(ajaxUrl, formdata=ajaxdata, callback=self.parse_ajax)



