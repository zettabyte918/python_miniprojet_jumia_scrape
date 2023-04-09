from django.shortcuts import render
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup


def search(query):
    """
    Search function that fetches suggestions from jumia.com.tn based on a query.
    Args:
        query (str): The query to search for.
    Returns:
        list: List of suggestions as BeautifulSoup objects.
    """
    params = {
        'query': query
    }
    # Fetch page with suggestions using GET request with query as parameter
    page = requests.get(
        "https://www.jumia.com.tn/fragment/suggestions/", params=params)
    soup = BeautifulSoup(page.content, "html.parser")
    return soup.find_all("a", class_="itm")


class product():
    id = ""
    brand = ""
    image = ""
    name = ""
    new_price = ""
    old_price = ""
    sale = ""
    url = ""

    def __init__(self, id, brand, image, name, new_price, old_price, sale, url):
        self.id = id
        self.brand = brand
        self.image = image
        self.name = name
        self.new_price = new_price
        self.old_price = old_price
        self.sale = sale
        self.url = url


def productsList(query, max_price, min_price):
    """
    Fetches products from jumia.com.tn based on a query.
    Args:
        query (str): The query to search for.
    Returns:
        list: List of products as dictionaries containing product details.
    """
    # Initialize an empty products array
    products = []

    # Add the query from the user to fetch jumia for a specific product
    params = {
        'q': query
    }

    # Request jumia html page
    page = requests.get(
        "https://www.jumia.com.tn/catalog/", params=params)

    # Pass the page to the BeautifulSoup library to handle it and extract information
    soup = BeautifulSoup(page.content, "html.parser")
    articles = soup.find_all("article", class_="prd")

    for article in articles:
        # Extract article (product) details using BeautifulSoup methods (brand, name, price, image ...)
        image = article.find('img', class_='img')
        core = article.find('a', class_='core')
        new_price = article.find('div', class_='prc')
        old_price = article.find('div', class_='old')
        sale = article.find('div', class_='bdg _dsct _sm')
        officiel = article.find('div', class_='bdg _mall _xs')

        # Filter products by category to only add phones
        if (core["data-category"].split()[0] == "Phones"):
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
                "officiel": 1 if officiel else 0,
            }

            # Remove comma or dot from price strings and convert to float ('1,299.90 TND' to 1299.90)
            item['new_price'] = float(item['new_price'].split()[0].replace(
                ',', ''))

            # sometime old price is none so we need to test it first
            if (item["old_price"]):
                item['old_price'] = float(item['old_price'].split()[0].replace(
                    ',', ''))

           # Filter products based on max_price and min_price if provided
            if max_price is not None and max_price.isnumeric() and item['new_price'] > float(max_price):
                continue  # skip the product if price is greater than max_price
            if min_price is not None and min_price.isnumeric() and item['new_price'] < float(min_price):
                continue  # skip the product if price is less than min_price

            # Add current item to the products array
            products.append(item)

    return products


def Smartphones(request):
    """
    View function that handles the request for smartphones and displays the results on a template.
    Args:
        request (HttpRequest): The HTTP request object.
    Returns:
        HttpResponse: The HTTP response object containing the rendered template with the products data.
    """
    # calculate how long the request take in seconds
    start_time = time.time()  # Capture start time
    # Get query params (search)
    query = request.GET.get('search')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Initialize empty data if query is not set, otherwise fill it with products from jumia by query
    data = []
    if (query):
        data = productsList(query, max_price, min_price)

    end_time = time.time()  # Capture end time
    time_taken = float(end_time - start_time)  # Calculate time taken
    # round it to only 2 degit after the point
    time_taken_seconds = round(time_taken, 2)

    # Return data to the Django template
    context = {
        'products': data,
        'query': query or "",
        'min_price': min_price or "",
        'max_price': max_price or "",
        'time_taken': time_taken_seconds
    }
    return render(request, 'smartphones.html', context)
