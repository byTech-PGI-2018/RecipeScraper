# -*- coding: utf-8 -*-
import scrapy, json
from scrapy.selector import Selector 


class PingoDoceSpider(scrapy.Spider):
    name = 'pingo_doce'
    #allowed_domains = ['https://www.pingodoce.pt/receitas']

    def __init__(self, pagestart='', pageend='', **kwargs):
        # Create base URL's that crawler will visit, from page number 'pagestart' to 'pageend'
        baseUrl = 'https://www.pingodoce.pt/wp-content/themes/pingodoce/ajax/pd-ajax.php?type=recipe&page=%s&query=&filters=&action=custom-search'
        self.start_urls = [baseUrl % i for i in range(int(pagestart), int(pageend)+1)]

        super().__init__(**kwargs)

    def parse(self, response):
        # Check if URL comes is 'Load More' request or recipe
        if response.request.url.startswith("https://www.pingodoce.pt/receitas"):
            # It's a recipe
            
            # Start making a new dicionary entry
            newRecipe = {}

            newRecipe['name'] = response.css('h1.main-slide-title::text').extract_first()
            newRecipe['url'] = response.request.url

            # For now, assume the recipe is not vegan
            newRecipe['vegan'] = False

            # The recipe may not have these properties, but add them anyway for consistency
            newRecipe['gastronomia'] = ""
            newRecipe['tipo'] = ""

            # Get properties (dish type, speed, difficulty, ...) of the recipe
            properties = ['recipetype', 'dificulty', 'preptime', 'nr_persons']

            # These will be the keys in the firestore db
            pKeys = {'dificulty': 'dificuldade', 'preptime': 'tempo', 'nr_persons': 'porção'}

            for p in properties:
                
                # If we are extracting cuisine type and dish type
                if p == 'recipetype':
                    # Get cuisine and type elements
                    recipetypes = response.css('div.recipe-types')

                    # Loop through all elements, which can range from none to more than two
                    for i, rt in enumerate(recipetypes.css('span.recipetype::text')):
                        # We only want to save the first...
                        if i == 0:
                            newRecipe['gastronomia'] = rt.extract().replace("|", "").strip()
                        
                        # ... and the last
                        elif i == len(recipetypes.css('span.recipetype::text'))-1:
                            newRecipe['tipo'] = rt.extract().strip()
                    
                    # Also check if the recipe is vegan (these values may be empty, hence the first test)
                    if newRecipe['gastronomia'] and (newRecipe['gastronomia'] in ['vegetariana', 'vegan']):
                        newRecipe['vegan'] = True

                    if newRecipe['tipo'] and (newRecipe['tipo'] in ['vegetariana', 'vegan']):
                        newRecipe['vegan'] = True


                else:
                    recipedetails = response.css('div.recipe-details')

                    # Get the property's value (guaranteed to exist)
                    newRecipe[pKeys[p]] = recipedetails.css('label.' + p + '::text').extract_first()

            # Create new dictionaries to hold ingredients and quantities
            newRecipeIngredients = {}
            newRecipeQuantities = {}

            # Get all ingredients and their quantities
            ingredients = response.css('li.ingredient-wrapper')

            for i, ingredient in enumerate(ingredients):
                # Join ingredient quantity and ingredient unit and add to dictionary
                quantity = ingredient.css('span.ingredient-quantity::text').extract_first()

                # Not all recipes have this element
                if ingredient.css('span.ingredient-unit::text').extract_first() is not None:
                    quantity = quantity + " " + ingredient.css('span.ingredient-unit::text').extract_first()
                    
                try:
                    # Join ingredient quantity and unit with ingredient name (if it exists, if not, abort this recipe)
                    quantity = quantity + " " + ingredient.css('span.ingredient-product::text').extract()[1].replace("\r\n", "").replace("\t", "").strip()
                    newRecipeQuantities[i] = quantity

                    # Add ingredient name to dictionary (if it exists, if not, abort this recipe)
                    newRecipeIngredients[i] = ingredient.css('span.ingredient-product::text').extract()[1].replace("\r\n", "").replace("\t", "").strip()
                except:
                    print("Failed to obtain ingredient name for recipe: " + response.request.url)
                    return

            # Add newly created dictionaries to root dictionary
            newRecipe['ingredients'] = newRecipeIngredients
            newRecipe['quantidade'] = newRecipeQuantities

            # Create new dictionaries to hold preparation steps
            newRecipeInstructions = {}

            # Get all preparation steps
            instructions = response.css('li.instruction-item')

            for i, instruction in enumerate(instructions):
                # Join instruction step number with instruction
                text = instruction.css('span.instruction-index::text').extract_first().strip()
                text = text + instruction.css('span.instruction-body::text').extract_first().strip()

                # Add step to dictionary
                newRecipeInstructions[i] = text

            # Add newly created dictionary to root dictionary
            newRecipe['preparação'] = newRecipeInstructions

            # Recipes from this site don't have these properties, but add empty values for consistency
            newRecipe['calorias'] = ""
            newRecipe['custo'] = ""

            # Return the recipe dictionary
            yield newRecipe

        else:
            # Parse the received JSON
            data = json.loads(response.body)
            htmlText = data['data']['html']

            # Actual data is received in a terrible mess of return line and escaped characters, fix this
            htmlText = htmlText.replace("\r\n", "")
            htmlText = htmlText.replace("\\", "")

            # Convert HTML from text to a Selector
            html = Selector(text=htmlText)

            # Parse each unique recipe URL
            for href in html.css('a::attr(href)'):
                
                # Make the request
                yield scrapy.Request(href.extract(), callback=self.parse)


