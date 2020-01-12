# -*- coding: utf-8 -*-

import requests
import io, json
from bs4 import BeautifulSoup

print("Starting script")

searchUrl = 'https://lifestyle.sapo.pt/pesquisar?filtro=receitas&q=&dificuldade=&duracao=&tipo-cozinha=&tipo-prato=&custo='
url = 'https://lifestyle.sapo.pt/sabores/receitas/robalo-com-bacon-e-sidra'
#url = 'https://lifestyle.sapo.pt/sabores/receitas/rolo-de-espinafres-rucula-parmesao'
#page = requests.get(url)

#soup = BeautifulSoup(page.content, 'html.parser')

recipesDict = {}

#TODO: Loop main function, to find every recipe url
#TODO: Log every op to a file
#TODO: Terminal printing operations, to show current url, how many, time elapsed
#TODO: Maybe use threads, to enable pausing/stopping without using ctrl+c

page = requests.get(searchUrl)
soup = BeautifulSoup(page.content, 'html.parser')
#Get all recipe href's
recipeUrls = soup.find_all('li', attrs={'class': '[ tiny-100 small-50 medium-33 large-33 xlarge-33 ] '})
i=0
print(recipeUrls)
for recipeUrl in recipeUrls:
    url = recipeUrl.find('a')['href']
    url = 'https://lifestyle.sapo.pt' + url
    print("======Making request: "+url)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    #============ LOOP THIS BOY ==============

    # Parse recipe name from url
    splitUrl = url.split('/')
    recipeName = splitUrl[-1].replace('-', ' ')

    # Start making a new dicionary entry
    newRecipe = {}
    newRecipe['name'] = recipeName

    # Get properties (dish type, speed, difficulty) of the recipe
    properties = ['cuisine', 'dish', 'time', 'difficulty', 'cost', 'calories-level', 'servings']

    for p in properties:
        current = soup.find('tr', attrs={'class': p})

        if current is None: continue

        if p == 'time' or p == "difficulty" or p == 'cost' or p == 'calories-level':
            print(current.find('td', attrs={'class': 'name'}).text + ": " + current.find('td', attrs={'class': 'value'}).find('div', attrs={'class': '[ ink-tooltip ]'})['data-tip-text'])
            newRecipe[p] = current.find('td', attrs={'class': 'value'}).find('div', attrs={'class': '[ ink-tooltip ]'})['data-tip-text']
        else:
            print(current.find('td', attrs={'class': 'name'}).text + ": " + current.find('td', attrs={"class": "value"}).text)
            newRecipe[p] = current.find('td', attrs={"class": "value"}).text

    # Get ingredients and their quantities
    ingredients = soup.find_all('td', attrs={"class": "ingredient-name"})
    quantities = soup.find_all('td', attrs={"class": "ingredient-quantity"})

    print("\n\nGot ingredients: \n")
    newRecipeIngredients = {}
    newRecipeQuantities = {}

    ingredientCount = 0
    quantityCount = 0
    for ingredient, quantity in zip(ingredients, quantities):
        print(ingredient.text+": "+quantity.text)
        newRecipeIngredients[ingredientCount] = ingredient.text
        newRecipeQuantities[quantityCount] = (quantity.text + ' de ' + ingredient.text)

        ingredientCount+=1
        quantityCount+=1

    newRecipe['ingredients'] = newRecipeIngredients
    newRecipe['quantities'] = newRecipeQuantities

    # Get preparation steps of the recipe
    prep_section = soup.find_all('section', attrs={'class': 'recipe-preparation'})
    prep_p = prep_section[0].find_all('p')

    newRecipePrep = {}
    print("\n\nPreparation: ")

    prepCounter=0
    for paragraph in prep_p:
        print(paragraph.text)
        newRecipePrep[prepCounter] = paragraph.text

        prepCounter+=1

    newRecipe['preparation'] = newRecipePrep

    # Add to a list (or make it json right away)
    recipesDict[i] = newRecipe

    print(recipesDict)
    i+=1
    print(json.dumps(recipesDict, indent=4,default=str).decode("unicode-escape"))
    break
    #============ LOOP THIS BOY ==============

with io.open('data.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(recipesDict, ensure_ascii=False))