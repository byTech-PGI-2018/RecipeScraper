# -*- coding: utf-8 -*-

import requests
import io, json
import logging
import signal
import sys, argparse
from bs4 import BeautifulSoup

print("Starting script")

# Main dictionary that will hold every recipe
recipesDict = {}

#TODO: Log every op to a file
#TODO: Terminal printing operations, to show current url, how many, time elapsed
#TODO: Maybe use threads, to enable pausing/stopping without using ctrl+c

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pages', type=int, default=1, help='Number of pages to search.')
    parser.add_argument('-r', '--recipes', type=int, default=-1, help='Number of recipes to retrieve.')

    arguments = parser.parse_args()

    main_function(arguments)

def main_function(arguments):
    # Handle SIGINT signal
    signal.signal(signal.SIGINT, receiveSignal)

    # Counter for recipe number in final json
    i=0

    currentPage=1
    for j in range(arguments.pages):
        # Make the request
        page = requests.get('https://lifestyle.sapo.pt/pesquisar?pagina=%s&q=&filtro=receitas' % currentPage)
        soup = BeautifulSoup(page.content, 'html.parser')

        #Get all recipe HTML class
        recipeClasses = soup.find_all('li', attrs={'class': '[ tiny-100 small-50 medium-33 large-33 xlarge-33 ] '})

        for recipeClass in recipeClasses:

            #Get each individual recipe HREF (in format: /sabores/...)
            recipeUrl = recipeClass.find('a')['href']
            recipeUrl = 'https://lifestyle.sapo.pt' + recipeUrl

            #Get the corresponding HTML
            print("======Making request: "+recipeUrl)
            page = requests.get(recipeUrl)
            soup = BeautifulSoup(page.content, 'html.parser')

            # Start making a new dicionary entry
            newRecipe = {}

            # Get recipe name
            newRecipe['name'] = soup.find('h1', attrs={'class': 'recipe-title'}).text

            # Get properties (dish type, speed, difficulty, ...) of the recipe
            properties = ['cuisine', 'dish', 'time', 'difficulty', 'cost', 'calories-level', 'servings']

            for p in properties:
                # Get each property key value pair (gastronomy: international, time: quick, ...)
                current = soup.find('tr', attrs={'class': p})

                # Some properties aren't available in all recipes (cost and calories)
                if current is None: continue

                # Some properties aren't a simple value but a graphical representation
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

            # Create new dictionaries to hold these values
            newRecipeIngredients = {}
            newRecipeQuantities = {}

            # Counters for each ingredient and quantity, will be the keys in dictionary
            ingredientCount = 0
            quantityCount = 0

            for ingredient, quantity in zip(ingredients, quantities):
                print(ingredient.text+": "+quantity.text)
                newRecipeIngredients[ingredientCount] = ingredient.text
                newRecipeQuantities[quantityCount] = (quantity.text + ' de ' + ingredient.text)

                ingredientCount+=1
                quantityCount+=1

            # Add created dictionaries to root recipe dictionary
            newRecipe['ingredients'] = newRecipeIngredients
            newRecipe['quantities'] = newRecipeQuantities

            # Get preparation steps of the recipe
            prep_section = soup.find_all('section', attrs={'class': 'recipe-preparation'})
            prep_p = prep_section[0].find_all('p')

            # Create new dictionary to hold these paragraphs
            newRecipePrep = {}
            print("\n\nPreparation: ")

            # Counter for each paragraph, will be key in dictionary
            prepCounter=0
            for paragraph in prep_p:
                print(paragraph.text)
                newRecipePrep[prepCounter] = paragraph.text

                prepCounter+=1

            # Add created dictionaries to root recipe dictionary
            newRecipe['preparation'] = newRecipePrep

            # Add to final recipe dictionary
            recipesDict[i] = newRecipe

            i+=1

            # Check if we reached recipe limit
            if i == arguments.recipes:
                break

            #print(json.dumps(recipesDict, indent=4,default=str).decode("unicode-escape"))

        # Check if we reached recipe limit
        if i == arguments.recipes:
            break

        currentPage+=1

    write_to_json()

def write_to_json():
    # Write final dictionary to a file
    with io.open('data.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(recipesDict, ensure_ascii=False))

def receiveSignal(signalNumber, frame):
    # Trigger writing dicitonary to file when receiving SIGINT (Ctrl+C)
    write_to_json()
    exit(1)

main()