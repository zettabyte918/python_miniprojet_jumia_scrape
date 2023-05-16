from urllib.parse import parse_qs, urlparse
from django.shortcuts import render
import pandas as pd
import requests
from django.http import HttpResponse
import time
from bs4 import BeautifulSoup
from django.core.cache import cache

# ANSI escape codes for colors
GREEN = "\033[92m"
END = "\033[0m"
YELLOW = "\033[33m"

# dataframe colums
columns = [
    "id",
    "image",
    "url",
    "name",
    "brand",
    "categorie",
    "new_price",
    "old_price",
    "sale",
    "officiel",
]


class TimeTracker:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    def get_time_taken(self):
        time_taken = float(self.end_time - self.start_time)
        time_taken_seconds = round(time_taken, 2)
        return time_taken_seconds


# def search(query):
#     """
#     Search function that fetches suggestions from jumia.com.tn based on a query.
#     Args:
#         query (str): The query to search for.
#     Returns:
#         list: List of suggestions as BeautifulSoup objects.
#     """
#     params = {"query": query}
#     # Fetch page with suggestions using GET request with query as parameter
#     page = requests.get("https://www.jumia.com.tn/fragment/suggestions/", params=params)
#     soup = BeautifulSoup(page.content, "html.parser")
#     return soup.find_all("a", class_="itm")


def export_to_excel(request):
    """
    Export the DataFrame dict to an Excel file.
    """
    # Retrieve the products_df JSON string, and the query from the request.POST dictionary
    products_df_json = request.POST.get("products_df")
    query = request.POST.get("query")

    filename = "{}.xlsx".format(query).replace(" ", "_")

    # remove all double quote in string then replace single quote to double quote to convert it json
    products_df_json = products_df_json.replace('"', "").replace("'", '"')

    # Deserialize the JSON string into a DataFrame
    products_df = pd.read_json(products_df_json, orient="records")
    products_df = products_df.reindex(columns=columns)

    # Export the DataFrame to an Excel file
    products_df.to_excel("products.xlsx", index=False)

    # Read the Excel file as bytes
    with open("products.xlsx", "rb") as excel_file:
        excel_data = excel_file.read()

        # Create the HttpResponse object with appropriate headers for download
        response = HttpResponse(
            excel_data,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = "attachment; filename={}".format(filename)

    return response


def generatePagination(pagination_html):
    pages = []
    if pagination_html:
        for page in pagination_html.find_all("a"):
            label = page.get("aria-label")
            is_current = "_act" in page.get("class", [])  # Check for "_act" class
            if label is not None and label.startswith("Page"):
                page_number = label.split(" ")[1]
                if page_number.isdigit():  # Check if page number is numeric
                    page_info = {
                        "page_number": page_number,
                        "is_current": is_current,
                    }
                    pages.append(page_info)
    return pages


def getLastPage():
    page = requests.get("https://www.jumia.com.tn/smartphones/")
    soup = BeautifulSoup(page.content, "html.parser")
    # Using CSS selector
    a_last = soup.select_one('a[aria-label="Dernière page"]')
    href = a_last["href"]
    parsed_url = urlparse(href)
    page = parse_qs(parsed_url.query).get("page")
    return page[0]


def productsList(query, page, max_price, min_price):
    """
    Fetches products from jumia.com.tn based on a query.
    Args:
        query (str): The query to search for.
    Returns:
        pd.DataFrame: DataFrame containing product details.
    """
    # Initialize an empty products DataFrame
    products_df = pd.DataFrame(columns=columns)
    last_page = getLastPage()

    # Add the query from the user to fetch jumia for a specific product, and a page
    for i in range(1, int(last_page)):
        print("{}Srapping page number {}: {}".format(GREEN, i, END))
        params = {
            "page": i,
        }

        # Request jumia html page
        page = requests.get("https://www.jumia.com.tn/smartphones/", params=params)

        # Pass the page to the BeautifulSoup library to handle it and extract information
        soup = BeautifulSoup(page.content, "html.parser")

        articles = soup.find_all("article", class_="prd")

        for article in articles:
            # Extract article (product) details using BeautifulSoup methods (brand, name, price, image ...)
            image = article.find("img", class_="img")
            core = article.find("a", class_="core")
            new_price = article.find("div", class_="prc")
            old_price = article.find("div", class_="old")
            sale = article.find("div", class_="bdg _dsct _sm")
            officiel = article.find("div", class_="bdg _mall _xs")

            # Filter products by category to only add phones
            if "Phones & Tablets/Mobile Phones/Smartphones" in core["data-category"]:
                item = {
                    "id": core["data-id"],
                    "image": image["data-src"],
                    "url": core["href"],
                    "name": core["data-name"],
                    "brand": core["data-brand"],
                    "categorie": core["data-category"],
                    "new_price": new_price.text if new_price else 0,
                    "old_price": old_price.text if old_price else 0,
                    "sale": sale.text if sale else 0,
                    "officiel": 1 if officiel else 0,
                }

                # Remove comma or dot from price strings and convert to float ('1,299.90 TND' to 1299.90)
                item["new_price"] = float(item["new_price"].split()[0].replace(",", ""))

                # sometime old price is none so we need to test it first
                if item["old_price"]:
                    item["old_price"] = float(
                        item["old_price"].split()[0].replace(",", "")
                    )

                # Add current item to the products DataFrame
                item_df = pd.DataFrame([item], columns=products_df.columns)
                products_df = pd.concat([products_df, item_df], ignore_index=True)

                # Convert "sale" column to numeric values
                products_df["sale"] = (
                    products_df["sale"].replace("%", "", regex=True).astype(float)
                )

                # Sort the DataFrame by "sale" column in descending order
                products_df = products_df.sort_values(by="sale", ascending=False)

    # save products in cach
    cache.set("scraped_data", products_df.to_dict(orient="records") or [])
    return products_df.to_dict(orient="records") or []


def Smartphones(request):
    """
    View function that handles the request for smartphones and displays the results on a template.
    Args:
        request (HttpRequest): The HTTP request object.
    Returns:
        HttpResponse: The HTTP response object containing the rendered template with the products data.
    """
    # calculate how long the request take in seconds
    timer = TimeTracker()
    timer.start()

    # Get query params (search)
    query = request.GET.get("search")
    page = request.GET.get("page") or 1
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    # Initialize data and fill it with products from jumia by query
    data = cache.get("scraped_data")
    if data is None:
        print("{}Start scraping jumia pages:{}".format(YELLOW, END))
        data = productsList(query, page, max_price, min_price)

    # Filter products by brand and price
    filtered_results = filter_products(
        data, brand=query, min_price=min_price, max_price=max_price
    )

    # Capture time in seconds
    timer.stop()
    time_taken_seconds = timer.get_time_taken()

    # Return data to the Django template
    context = {
        "products": filtered_results,
        "query": query or "",
        "page": page,
        "min_price": min_price or "",
        "max_price": max_price or "",
        "time_taken": time_taken_seconds,
    }

    return render(request, "smartphones.html", context)


def filter_products(products, brand=None, min_price=None, max_price=None):
    if brand is None and min_price is None and max_price is None:
        # No filters specified, return the full list of products
        return products

    filtered_products = []

    for product in products:
        # Check if brand matches the filter
        if brand and product["brand"].lower() != brand.lower():
            continue

        # Check if price falls within the specified range
        if min_price and min_price != "" and product["new_price"] < float(min_price):
            continue

        if max_price and max_price != "" and product["new_price"] > float(max_price):
            continue

        # Add the product to the filtered list
        filtered_products.append(product)

    return filtered_products
