import requests
from bs4 import BeautifulSoup

url = 'https://lifestyle.sapo.pt/sabores/receitas/robalo-com-bacon-e-sidra'
#url = 'https://lifestyle.sapo.pt/sabores/receitas/rolo-de-espinafres-rucula-parmesao'
page = requests.get(url)

soup = BeautifulSoup(page.content, 'html.parser')

#============ LOOP THIS BOY ==============

# Get properties (dish type, speed, difficulty) of the recipe
properties = ['cuisine', 'dish', 'time', 'difficulty', 'cost', 'calories-level', 'servings']

for p in properties:
    current = soup.find('tr', attrs={'class': p})

    if current is None: continue

    if p == 'time' or p == "difficulty" or p == 'cost' or p == 'calories-level':
        print(current.find('td', attrs={'class': 'name'}).text + ": " + current.find('td', attrs={'class': 'value'}).find('div', attrs={'class': '[ ink-tooltip ]'})['data-tip-text'])
    else:
        print(current.find('td', attrs={'class': 'name'}).text + ": " + current.find('td', attrs={"class": "value"}).text)

# Get ingredients and their quantities
ingredients = soup.find_all('td', attrs={"class": "ingredient-name"})
quantities = soup.find_all('td', attrs={"class": "ingredient-quantity"})

print("\n\nGot ingredients: \n")

for ingredient, quantity in zip(ingredients, quantities):
    print(ingredient.text+": "+quantity.text)

# Get preparation steps of the recipe
prep_section = soup.find_all('section', attrs={'class': 'recipe-preparation'})
prep_p = prep_section[0].find_all('p')

print("\n\nPreparation: ")

for paragraph in prep_p:
    print(paragraph.text)

# Add to a list (or make it json right away)

#============ LOOP THIS BOY ==============