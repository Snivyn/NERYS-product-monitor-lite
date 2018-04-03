'''
NERYS
supreme module

left to do:
save products to sql db
load products from sql db on startup
'''

import requests
from bs4 import BeautifulSoup as soup
import random
from log import log as log
from threading import Thread
from discord_hooks import Webhook
import time

class Product:
    def __init__(self, link, image, title = "", stock = False):
        self.link = link
        self.image = image
        self.title = title
        self.stock = stock

def read_from_txt(path):
    '''
    (None) -> list of str
    Loads up all sites from the sitelist.txt file in the root directory.
    Returns the sites as a list
    '''
    # Initialize variables
    raw_lines = []
    lines = []

    # Load data from the txt file
    try:
        f = open(path, "r")
        raw_lines = f.readlines()
        f.close()

    # Raise an error if the file couldn't be found
    except:
        log('e', "Couldn't locate <" + path + ">.")
        raise FileNotFound()

    if(len(raw_lines) == 0):
        raise NoDataLoaded()

    # Parse the data
    for line in raw_lines:
        lines.append(line.strip("\n"))

    # Return the data
    return lines


def get_proxy(proxy_list):
    '''
    (list) -> dict
    Given a proxy list <proxy_list>, a proxy is selected and returned.
    '''
    # Choose a random proxy
    proxy = random.choice(proxy_list)

    # Set up the proxy to be used
    proxies = {
        "http": str(proxy),
        "https": str(proxy)
    }

    # Return the proxy
    return proxies


def send_embed(alert_type, product):
    '''
    (str, str, list, str, str, str) -> None
    Sends a discord alert based on info provided.
    '''
    # Set webhook
    url = discord_webhook

    # Create embed to send to webhook
    embed = Webhook(url, color=123123)

    # Set author info
    embed.set_author(name='NERYS', icon='https://static.zerochan.net/Daenerys.Targaryen.full.2190849.jpg')

    # Set product details
    if(alert_type == "RESTOCK"):
        embed.set_desc("RESTOCK: " + product.title)
    elif(alert_type == "NEW"):
        embed.set_desc("NEW: " + product.title)

    embed.add_field(name="Product", value=product.title)
    embed.add_field(name="Link", value=product.link)
    embed.add_field(name="Stock", value=str(product.stock))

    # Set product image
    embed.set_thumbnail(product.image)
    embed.set_image(product.image)

    # Set footer
    embed.set_footer(text='NERYS by @snivynGOD', icon='https://static.zerochan.net/Daenerys.Targaryen.full.2190849.jpg', ts=True)

    # Send Discord alert
    embed.post()

def monitor():
    # GET "view all" page
    link = "http://www.supremenewyork.com/shop/all"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
        }
    proxies = get_proxy(proxy_list)

    try:
        r = requests.get(link, timeout=5, verify=False)
    except:
        log('e', "Connection to URL <" + link + "> failed. Retrying...")
        try:
            if(use_proxies):
                proxies = get_proxy(proxy_list)
                r = requests.get(link, proxies=proxies, timeout=8, verify=False)
            else:
                r = requests.get(link, timeout=8, verify=False)                
        except:
            log('e', "Connection to URL <" + link + "> failed.")
            return

    page = soup(r.text, "html.parser")
    products = page.findAll("div", {"class": "inner-article"})

    log('i', "Checking stock of Supreme products...")
    for product in products:
        link = "https://www.supremenewyork.com" + product.a["href"]
        monitor_supreme_product(link, product)


def monitor_supreme_product(link, product):
    # Product info
    image = "https:" + product.a.img["src"]
    if(product.text == "sold out"):
        stock = False
    else:
        stock = True
        
    # Product already in database
    try:
        if(stock is True and products_list[link].stock is False):
            log('s', products_list[link].title + " is back in stock!")
            products_list[link].stock = True
            send_embed("RESTOCK", products_list[link])
        elif(stock is False and products_list[link].stock is True):
            log('s', products_list[link].title + " is now out of stock.")
            products_list[link].stock = False
    # Add new product to database
    except:
        # GET product name
        try:
            if(use_proxies):
                proxies = get_proxy(proxy_list)
                r = requests.get(link, proxies=proxies, timeout=8, verify=False)
            else:
                r = requests.get(link, timeout=8, verify=False)
        except:
            log('e', "Connection to URL <" + link + "> failed. Retrying...")
            try:
                if(use_proxies):
                    proxies = get_proxy(proxy_list)
                    r = requests.get(link, proxies=proxies, timeout=8, verify=False)
                else:
                    r = requests.get(link, timeout=8, verify=False)                  
            except:
                log('e', "Connection to URL <" + link + "> failed.")
                return

        title = soup(r.text, "html.parser").find("title").text

        # Add product to database
        products_list[link] = Product(link, image, title, stock)
        log('s', "Added " + title + " to the database.")
        send_embed("NEW", products_list[link])


def build_db():
    # GET "view all" page
    link = "http://www.supremenewyork.com/shop/all"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
        }
    proxies = get_proxy(proxy_list)

    try:
        r = requests.get(link, timeout=5, verify=False)
    except:
        log('e', "Connection to URL <" + link + "> failed. Retrying...")
        try:
            if(use_proxies):
                proxies = get_proxy(proxy_list)
                r = requests.get(link, proxies=proxies, timeout=8, verify=False)
            else:
                r = requests.get(link, timeout=8, verify=False)
        except:
            log('e', "Connection to URL <" + link + "> failed.")
            return

    page = soup(r.text, "html.parser")
    products = page.findAll("div", {"class": "inner-article"})

    log('i', "Checking stock of Supreme products...")
    for product in products:
        link = "https://www.supremenewyork.com" + product.a["href"]

        # Product info
        image = "https:" + product.a.img["src"]
        if(product.text == "sold out"):
            stock = False
        else:
            stock = True        

        # GET product name
        try:
            if(use_proxies):
                proxies = get_proxy(proxy_list)
                r = requests.get(link, proxies=proxies, timeout=8, verify=False)
            else:
                r = requests.get(link, timeout=8, verify=False)
        except:
            log('e', "Connection to URL <" + link + "> failed. Retrying...")
            proxies = get_proxy(proxy_list)
            r = requests.get(link, proxies=proxies, timeout=8, verify=False)
            try:
                if(use_proxies):
                    proxies = get_proxy(proxy_list)
                    r = requests.get(link, proxies=proxies, timeout=8, verify=False)
                else:
                    r = requests.get(link, timeout=8, verify=False)                  
            except:
                proxies = get_proxy(proxy_list)
                log('e', "Connection to URL <" + link + "> failed.")
                return

        title = soup(r.text, "html.parser").find("title").text

        # Add product to database
        products_list[link] = Product(link, image, title, stock)
        log('s', "Added " + title + " to the database.")


if(__name__ == "__main__"):
    # Ignore insecure messages
    requests.packages.urllib3.disable_warnings()

    # Load proxies (if available)
    proxy_list = read_from_txt("proxies.txt")
    log('i', "Loaded " + str(len(proxy_list)) + " proxies.")
    if(len(proxy_list) == 0):
        use_proxies = False
    else:
        use_proxies = True    

    # Initialize variables
    products_list = {}
    proxies = get_proxy(proxy_list)
    discord_webhook = ""  # Put your webhook here

    # Build database
    build_db()

    # Monitor products
    while(True):
        monitor()
        time.sleep(8)