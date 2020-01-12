import scrapy

class RecipesSpider(scrapy.Spider):
    name = "recipes"

    download_delay = 1

    def __init__(self, pages='', **kwargs):
        baseUrl = 'https://lifestyle.sapo.pt/pesquisar?pagina='
        self.start_urls = [baseUrl + str(i) + '&q=&filtro=receitas' for i in range(1,int(pages)+1)]
        print(self.start_urls)
        super().__init__(**kwargs)

    def parse(self, response):
        # Extract recipes from search page
        allHref = response.css('article.recipe')

        # Prevent infinite recursion (recipe page also has the tag by which the url's are discovered)
        if response.request.url.startswith('https://lifestyle.sapo.pt/sabores/receitas'):
            newRecipe = {}

            #
            newRecipe['name'] = response.request.url.split('/')[-1].replace("-", " ")

            # 
            properties = ['cuisine', 'dish', 'time', 'difficulty', 'cost', 'calories-level', 'servings']
            
            for p in properties:
                value = response.css('tr.'+p)

                if value.css('td.name::text').get() == None: continue
                elif p == 'time' or p == "difficulty" or p == 'cost' or p == 'calories-level':
                    newRecipe[value.css('td.name::text').get()] = value.css('div::attr(data-tip-text)').get()

                elif p == 'servings':
                    newRecipe[value.css('td.name::text').get()] = value.css('td.value::text').get()
                    
                else:
                    newRecipe[value.css('td.name::text').get()] = value.css('a::text').get()

            #
            newRecipeIngredients = {}
            newRecipeQuantities = {}
            iCounter=0
            qCounter=0

            #
            ingredientTable = response.css('table.ingredients-table')
            for ingredients, quantities in zip(ingredientTable.css('td.ingredient-name::text'), ingredientTable.css('td.ingredient-quantity::text')):
                newRecipeIngredients[iCounter] = ingredients.get()
                newRecipeQuantities[qCounter] = quantities.get() + ' de ' + ingredients.get()

                iCounter+=1
                qCounter+=1

            #
            newRecipe['ingredients'] = newRecipeIngredients
            newRecipe['quantities'] = newRecipeQuantities

            #
            newRecipePrep = {}
            pCounter=0

            #
            preparation = response.css('section.recipe-preparation')
            for paragraph in preparation.css('p::text'):
                newRecipePrep[pCounter] = paragraph.get()

                pCounter+=1

            #
            newRecipe['preparation'] = newRecipePrep
            
            yield newRecipe

        else:
            for href in allHref:
                newUrl = href.css('a::attr(href)').extract_first()
                newUrl = 'https://lifestyle.sapo.pt' + newUrl
                #print(newUrl)

                yield scrapy.Request(newUrl, callback=self.parse)