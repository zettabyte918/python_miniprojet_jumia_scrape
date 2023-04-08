from django.shortcuts import render
import requests
from bs4 import BeautifulSoup


def search(query):
    params = {
        'query': query
    }
    page = requests.get(
        "https://www.jumia.com.tn/fragment/suggestions/", params=params)
    soup = BeautifulSoup(page.content, "html.parser")
    return soup.find_all("a", class_="itm")


def productsList(query):

    products = []
    params = {
        'q': query
    }
    page = requests.get(
        "https://www.jumia.com.tn/catalog/", params=params)
    soup = BeautifulSoup(page.content, "html.parser")
    articles = soup.find_all("article", class_="prd")
    for article in articles:
        image = article.find('img', class_='img')
        core = article.find('a', class_='core')
        new_price = article.find('div', class_='prc')
        old_price = article.find('div', class_='old')
        sale = article.find('div', class_='bdg _dsct _sm')

        item = {
            "id": core["data-id"],
            "image": image['data-src'],
            "url": core['href'],
            "name": core['data-name'],
            "brand": core["data-brand"],
            "categorie": core["data-category"],
            "new_price": new_price.text if new_price else 0,
            "old_price": old_price.text if old_price else 0,
            "sale": sale.text if sale else 0,

        }

        products.append(item)

    return products


def Smartphones(request):
    # get query params (search)
    query = request.GET.get('search')

    # init empty data if query is not set otherwser fill it with products from jumia by query
    data = []
    if (query):
        data = productsList(query)

    return render(request, 'smartphones.html', {'products': data, "query": query})
