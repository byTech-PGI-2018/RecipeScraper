import scrapy

class RecipesSpider(scrapy.Spider):
    name = "recipes"

    def __init__(self, pagestart='', pageend='', **kwargs):
        # Create search page URL's from page 1 to page N passed as parameter
        baseUrl = 'https://lifestyle.sapo.pt/pesquisar?pagina='
        self.start_urls = [baseUrl + str(i) + '&q=&filtro=receitas' for i in range(int(pagestart),int(pageend)+1)]
        
        super().__init__(**kwargs)

    def parse(self, response):
        # Extract recipes from search page
        allHref = response.css('article.recipe')

        # Prevent infinite recursion (recipe page also has the tag by which the URL's are discovered)
        if response.request.url.startswith('https://lifestyle.sapo.pt/sabores/receitas'):

            # Start making a new dicionary entry
            newRecipe = {}
            newRecipe['name'] = response.css('h1.recipe-title::text').extract_first()

            # Get properties (dish type, speed, difficulty, ...) of the recipe
            properties = ['cuisine', 'dish', 'time', 'difficulty', 'cost', 'calories-level', 'servings']
            
            for p in properties:
                # Get each property name-value pair (gastronomy: international, time: quick, ...)
                value = response.css('tr.'+p)

                # Some properties aren't available in all recipes (cost and calories)
                if value.css('td.name::text').extract_first() == None: continue

                # Some properties aren't a simple value but a graphical representation
                elif p == 'time' or p == "difficulty" or p == 'cost' or p == 'calories-level':
                    newRecipe[value.css('td.name::text').extract_first()] = value.css('div::attr(data-tip-text)').extract_first()

                elif p == 'servings':
                    newRecipe[value.css('td.name::text').extract_first()] = value.css('td.value::text').extract_first()
                
                # Some properties have a hyperlink
                else:
                    newRecipe[value.css('td.name::text').extract_first()] = value.css('a::text').extract_first()

            # Create new dictionaries to hold ingredients and quantities (and counters, to serve as keys)
            newRecipeIngredients = {}
            newRecipeQuantities = {}
            iCounter=0
            qCounter=0

            # Get ingredients and their quantities
            ingredientTable = response.css('table.ingredients-table')
            for ingredients, quantities in zip(ingredientTable.css('td.ingredient-name::text'), ingredientTable.css('td.ingredient-quantity::text')):
                newRecipeIngredients[iCounter] = ingredients.extract()
                newRecipeQuantities[qCounter] = quantities.extract() + ' de ' + ingredients.extract()

                iCounter+=1
                qCounter+=1

            # Add ingredients and quantities to root dictionary
            newRecipe['ingredients'] = newRecipeIngredients
            newRecipe['quantities'] = newRecipeQuantities

            # Create new dictionary to hold preparation paragraphs (and counter to serve as key)
            newRecipePrep = {}
            pCounter=0

            # Get each paragraph from preparation section
            preparation = response.css('section.recipe-preparation')
            for paragraph in preparation.css('p::text'):
                newRecipePrep[pCounter] = paragraph.extract()

                pCounter+=1

            # Add preparation to root dictionary
            newRecipe['preparation'] = newRecipePrep
            
            # Return the recipe dictionary
            yield newRecipe

        else:
            for href in allHref:
                # Get URL text (in format /sabores/<name> and prepend base URL to it)
                newUrl = href.css('a::attr(href)').extract_first()
                newUrl = 'https://lifestyle.sapo.pt' + newUrl

                # Recursively call this function with new URL
                yield scrapy.Request(newUrl, callback=self.parse)