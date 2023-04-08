from django.shortcuts import render
import requests
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


def productsList(query):
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
            }

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
    # Get query params (search)
    query = request.GET.get('search')

    # Initialize empty data if query is not set, otherwise fill it with products from jumia by query
    data = []
    if (query):
        data = productsList(query)

    # Return data to the Django template
    return render(request, 'smartphones.html', {'products': data, "query": query})
