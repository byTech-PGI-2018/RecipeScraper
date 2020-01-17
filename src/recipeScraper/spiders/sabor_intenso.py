# -*- coding: utf-8 -*-
import scrapy, re


class SaborIntensoSpider(scrapy.Spider):
    name = 'sabor_intenso'
    #allowed_domains = ['https://www.saborintenso.com/']


    def __init__(self, pagestart='', pageend='', **kwargs):
        # Create base URL's from where to start searching for recipes
        baseUrls = ['https://www.saborintenso.com/chef/caderno-1/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-9/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-19/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-15/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-30/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-25/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-41/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-45/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-42/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-49/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-57/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-54/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-62/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-76/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-66/&ver=tudo&page=%s/',
                    'https://www.saborintenso.com/chef/caderno-84/&ver=tudo&page=%s/']
        
        # For each kind of base URL, build N search pages
        self.start_urls = [baseUrl % i for baseUrl in baseUrls for i in range(int(pagestart), int(pageend)+1)]

        super().__init__(**kwargs)

    def parse(self, response):
        #print("ENTERING FROM: " + response.request.url)
        # Check if the current URL is a recipe
        if response.request.url.startswith("https://www.saborintenso.com/f"):
            # It's a recipe
            
            # Start making a new dicionary entry
            newRecipe = {}

            newRecipe['name'] = response.css('span.bc_l2::text').extract_first()
            newRecipe['url'] = response.request.url

            # For now, assume the recipe is not vegan
            newRecipe['vegan'] = False

            # The recipe may not have these properties, but add them anyway for consistency
            newRecipe['gastronomia'] = ""
            newRecipe['tipo'] = ""
            newRecipe['dificuldade'] = ""

            # Try to extract dish type
            try:
                newRecipe['tipo'] = response.css('a.bc_l0::text').extract()[2]

                # Check if the type is vegan
                if newRecipe['tipo'] and (newRecipe['tipo'] in 'Vegetariana'):
                    newRecipe['vegan'] = True
            except:
                print("No dish type for recipe: " + response.request.url)

            # Try to extract dish portions
            try:
                newRecipe['porção'] = response.xpath('//*[@class="topico"]/font[1]/font/b/text()').extract_first().split("para")[-1].replace(":", "").strip()
            except:
                print("No portion info for recipe: " + response.request.url)

            # Try to extract calorie information
            try:
                newRecipe['calorias'] = response.xpath('//*[@class="topico"]/div[2]/font[1]/text()').extract_first().split(":")[-1].strip()
            except:
                print("No calorie info for recipe: " + response.request.url)

            # Create new dictionaries to hold ingredients and quantities
            newRecipeIngredients = {}
            newRecipeQuantities = {}

            # Pattern to discard ingredient unit-related stuff
            #pattern = re.compile('[0-9].*([0-9]|kg|g|ml|l)$', re.IGNORECASE)
            pattern = re.compile('(([0-9]*\.)?[0-9]+(kg|mg|l|ml|g|(colheres)|(colher))?)|^(kg|mg|l|ml|g|(colheres)|(colher))$', re.IGNORECASE)
            #single_digit = re.compile('[0-9]$', re.IGNORECASE)
            
            # TODO: Sometimes there's an additional <a> tag in the <li> tag
            # Get ingredients and respective quantities (in the source HTML, they will be mixed)
            ingredients = response.xpath('//*[@class="topico"]/ul/descendant::*/text()').extract()
            for i, ingredient in enumerate(ingredients):
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

            # Get all instructions
            instructions = response.xpath('//*[@class="topico"]/self::*/text()').extract()

            # Remove newlines characters and empty strings from the list
            instructions = [i.replace("\r\n", "").replace("\n", "") for i in instructions if (i.replace("\r\n", "").replace("\n", "") and not i.replace("\r\n", "").replace("\n", "").isspace())]
            for i, instruction in enumerate(instructions):
                newRecipeInstructions[i] = instruction

            # Add newly created dictionary to root dictionary
            newRecipe['preparação'] = newRecipeInstructions

            # Assume preparation time and cost is empty for now
            newRecipe['tempo'] = ''
            newRecipe['custo'] = ''

            # Get preparation time and cost elements (if they exist)
            items = response.xpath('//*[@class="topico"]/*[@color="seagreen"]//text()').extract()

            # Try to add preparation time (older recipes don't have this element)
            try:
                newRecipe['tempo'] = items[0].split(":")[-1].strip()
            except:
                print('Failed to obtain preparation time for recipe: ' + response.request.url)

            # Try to add recipe cost (some recipes don't have this)
            try:
                newRecipe['custo'] = items[1].split("|")[0].split(":")[-1].strip()
            except:
                print('Failed to obtain cost for recipe: ' + response.request.url)

            # Return the recipe data
            yield newRecipe

        # Otherwise, find all recipe URL's from search page
        else:
            # Extract recipe URL containers
            allHref = response.css('div.sombra_pub')

            # Yield new request for every recipe we find
            for href in allHref:
                url = href.css('a::attr(href)').extract_first()

                yield scrapy.Request(url, callback=self.parse)

