# -*- coding: utf-8 -*-
import scrapy
import json
import re
import unicodedata

# Base URL's
baseUrl = 'https://www.vaqueiro.pt'
ajaxUrl = 'https://www.vaqueiro.pt/Search/QueryService'

# Data field for AJAX requests
data = {'formSelected': "0" ,
        'text': ""          ,
        'difficulty': ""    ,
        'time': ""          ,
        'cost': ""          ,
        'StartIdx': ""      ,
        'EndIdx': ""        }

# Map category names passed as arguments to actual meaningful category info
categories =    {
    'sopas': "1",
    'entradas': "2",
    'saladas': "3",
    'carnes': "6",
    'peixes': "4",
    'massas': "8",
    'arroz': "9",
    'legumes': "7",
    'acompanhamentos': "12",
    'paes': "10",
    'pizzas': "11",
    'bebidas': "13",
    'dietas': "15",
    'doces': "14"
}

# Map the total number of pages each recipe category has
max_pages = {
    'sopas'     : "22",
    'entradas'  : "60",
    'saladas'   : "21",
    'carnes'    : "76",
    'peixes'    : "70",
    'massas'    : "14",
    'arroz'     : "15",
    'legumes'   : "14",
    'acompanhamentos': "5",
    'paes'      : "11",
    'pizzas'    : "7",
    'bebidas'   : "7",
    'dietas'    : "4",
    'doces'     : "124"
}


class VaqueiroSpider(scrapy.Spider):
    name = 'vaqueiro'

    def __init__(self, **kwargs):
        # Base URL from which to execute AJAX requests (actually irrelevant)
        self.start_urls = ['https://www.vaqueiro.pt/receitas/pesquisa']

        super().__init__(**kwargs)

    # This function handles parsing of received recipe URL's and making every AJAX request but the first
    def parse_ajax(self, response):
        # Parse all recipe URL's
        received = json.loads(response.body)['bodydata']['Results']

        # Handle each recipe individually
        for recipe in received:
           yield scrapy.Request(baseUrl+recipe['Url'], callback=self.parse_items)

        # Increment the item offsets
        itemstart = int(response.meta.get("itemstart")) + 12
        itemend = itemstart + 11

        # Check if we reached the limit of pages to search, or if there are no more pages to search
        pagecount = int(response.meta.get("pagecount"))
        if pagecount >= int(self.pageend) or pagecount >= int(max_pages[self.category]): # pylint: disable=no-member
            return

        # If not, increment pagecount
        pagecount += 1

        # Add the item offsets to the AJAX request data
        data['StartIdx'] = str(itemstart)
        data['EndIdx'] = str(itemend)

        # Ask for next AJAX request
        yield scrapy.FormRequest(ajaxUrl, formdata=data, meta={"pagecount": str(pagecount), "itemstart": str(itemstart)}, callback=self.parse_ajax)

    # This function extracts data from each individual recipe URL
    def parse_items(self, response):
        # Start making a new dicionary entry
        newRecipe = {}

        newRecipe['name'] = response.xpath('//*[@class="recipe-title"]/text()').extract_first().strip()
        newRecipe['url'] = response.request.url

        # For now, assume the recipe is not vegan
        newRecipe['vegan'] = False

        # The recipe may not have these properties, but add them anyway for consistency
        newRecipe['gastronomia'] = ""
        newRecipe['tipo'] = ""
        newRecipe['dificuldade'] = ""
        newRecipe['calorias'] = ""
        newRecipe['porção'] = ""
        newRecipe['custo'] = ""
        newRecipe['tempo'] = ""
        newRecipe['dificuldade'] = ""


        # Set dish type as category passed as argument
        newRecipe['tipo'] = self.category # pylint: disable=no-member

        # Try to get recipe properties (cost, duration and difficulty)
        try:
            properties = response.xpath('//*[@class="additional-info"]//dd/text()').extract()[:3]

            newRecipe['custo'] = properties[0]
            newRecipe['tempo'] = properties[1]
            newRecipe['dificuldade'] = properties[2]
        except:
            print("Failed to get recipe properties for recipe: " + response.request.url)

        # Try to get portions
        try:
            newRecipe['porção'] = response.xpath('//*[@class="preparation"]//span/text()').extract_first()
        except:
            print("Failed to get recipe portion for recipe: " + response.request.url)

        # Create new dictionaries to hold ingredients and quantities
        newRecipeIngredients = {}
        newRecipeQuantities = {}

        # Pattern to discard ingredient unit-related stuff
        pattern = re.compile('(([0-9]*\.)?[0-9]+(kg|mg|dl|l|ml|g|(colheres)|(colher))?)|^(kg|mg|dl|l|ml|g|(colheres)|(colher))$', re.IGNORECASE) # pylint: disable=anomalous-backslash-in-string

        # Get ingredients and respective quantities (in the source HTML, they will be mixed)
        ingredients = response.xpath('//*[@class="preparation"]/ul/descendant::li')

        # Iterate over all extracted <li> elements
        for i, ingredientSelector in enumerate(ingredients):
            # Extract every text node in the <li> tag, also joining any child node text
            ingredient = ingredientSelector.xpath('string(descendant-or-self::*)').extract_first().replace("\n", "").strip()

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
        
        # Add newly created dictionaries to root dictionary
        newRecipe['ingredients'] = newRecipeIngredients
        newRecipe['quantidade'] = newRecipeQuantities

        # Create a new dictionary that will hold preparation steps
        newRecipeInstructions = {}

        # Get all instructions, split by a newline char, and remove empty strings and tabs
        instructions = response.xpath('substring-after(//*[@class="instructions"]/descendant-or-self::*[not(@class="title")], "Preparação")').extract_first()
        iCounter=0
        for instruction in instructions.replace("\t", "").splitlines():
            instruction = instruction.strip()

            # Check if the string isn't empty before adding it
            if instruction:
                newRecipeInstructions[iCounter] = unicodedata.normalize("NFKD", instruction)
                iCounter += 1
        
        # Add preparation dictionary to root dictionary
        newRecipe['preparação'] = newRecipeInstructions

        yield newRecipe

    # This function handles the initial AJAX request
    def parse(self, response):
        # Check if we received required arguments
        try:
            if self.pagestart or self.pageend or self.category:
                pass
        except:
            print("No arguments")
            return

        # Build first AJAX request, with item index offset from (pagestart-1)*12 to (pagestart-1)*12+11
        itemstart = str( ( int(self.pagestart) -1) *12) # pylint: disable=no-member
        data['StartIdx'] = itemstart
        data['EndIdx'] = str( int(itemstart) +11 )

        # Set the category value
        data['category'] = categories[self.category] # pylint: disable=no-member

        pagecount = self.pagestart # pylint: disable=no-member
        
        yield scrapy.FormRequest(ajaxUrl, formdata=data, meta={"pagecount": pagecount, "itemstart": itemstart}, callback=self.parse_ajax)


