#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import demiurge, sys, getopt, os, pickle, tempfile

urlWallapop = 'http://es.wallapop.com'
urlWallapopMobile = 'http://p.wallapop.com/i/'
SAVE_LOCATION = os.path.join(tempfile.gettempdir(), 'alertWallapop.pkl')
data_save = True
push_bullet = False

# Query params
_minPrice = "" # Min query price [0..20000]. Empty for no minPrice
_maxPrice = "" # Max query price [0..20000]. Empty for no maxPrice
_dist = "0_" # "0_" -> No limit, "0_10000" -> My town (10km), "0_5000" -> My area (5km), "0_1000" -> Neaby (1km)
_order = "creationDate-dec" # "distance-asc" -> Near first, "salePrice-asc" -> Cheap first, "salePrice-des" -> Expensive first, "creationDate-des" -> New first
_kws = "" # Plus-separated query words (E.g. gameboy+color+pokemon)
_lat = "1.234567" # Latitude in signed degrees format w/ 6 decimals (E.g. 1.234567)
_lng = "-7.654321" # Longitude in signed degrees format w/ 6 decimals (E.g. -7.654321)

# Notify params
pushToken = '<your token here>'
email = '<your email here>'

# Demiurge for get products in Wallapop
class Products(demiurge.Item):
    title = demiurge.TextField(selector='a.product-info-title')
    price = demiurge.TextField(selector='span.product-info-price')
    url = demiurge.AttributeValueField(selector='div.card-product-product-info a.product-info-title', attr='href')

    class Meta:
        selector = 'div.card-product'

class ProductDetails(demiurge.Item):
    description = demiurge.TextField(selector='p.card-product-detail-description')
    location = demiurge.TextField(selector='div.card-product-detail-location')

    class Meta:
        selector = 'div.card-product-detail'

def sendPushBullet(pushToken, email, title, body, url):
    command = "curl -X POST -H 'Access-Token: {pushToken}' -F 'type=link' -F 'title={title}' -F 'body={body}' -F 'url={url}' -F 'email={email}' 'https://api.pushbullet.com/v2/pushes'".format(pushToken = pushToken, email=email, title=title, body=body, url=url)
    os.system(command)

def wallAlert(urlSearch):
    # Load after data search
    data_temp = []
    try:
        dataFile = open(SAVE_LOCATION, 'rb')
        data_save = pickle.load(dataFile)
    except:
        data_save = open(SAVE_LOCATION, 'wb')
        pickle.dump(data_temp, data_save)
        pass

    # Read web
    results = Products.all(urlSearch)

    for item in results:
        data_temp.append({'title': item.title
                          , 'price': item.price
                          , 'relativeUrl': item.url })

    # Check new items
    list_news = []
    if data_save and data_save != data_temp:
        for item in data_temp:
            if item not in data_save:
                list_news.append(item)

    for item in list_news:
        # Get info from new items
        title = item['title'] + " - " + item['price']
        url = urlWallapop + item['relativeUrl']
        itemDetails = ProductDetails.one(url)
        body = itemDetails.description + "\n" + itemDetails.location
        productID = url.split("-")[-1]
        applink = urlWallapopMobile + productID

        # Send Alert
        print(title, body, url)
        print('-' * 10)
        if push_bullet:
            sendPushBullet(pushToken, email, title, body, applink)
    print(data_save)
    # Save data
    data_save = open(SAVE_LOCATION, 'wb')
    pickle.dump(data_temp, data_save)


def usage():
    print ("Usage:", __file__," -k <keywords> -m <min price> -x <max price> -d <distance> -l <latitude> -g <longitude>")
    optionsHelp()

def optionsHelp():
    print('     -k : Keywords. E.g. "gameboy pokemon"')
    print('     -m : Min price [0..20000]. Default: no limit')
    print('     -x : Max price [0..20000]. Default: no limit')
    print('     -d : Distance [0_ -> no limit, 0_10000 -> 10km, 0_5000 -> 5km, 0_1000 -> 1km]. Default: no limit')
    print('     -l : Latitude. Default: 40.4378693')
    print('     -g : Longitude. Default: -3.819963')

def extractArguments(argv):

    _minPrice = ""
    _maxPrice = ""
    _dist = "0_"
    _order = "creationDate-dec"
    _kws = ""
    _lat = "40.4378693"
    _lng = "-3.819963"

    try:
        opts, args = getopt.getopt(argv, "k:m:x:d:l:g:o:")

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        _kws = arg if opt in ("-k") else _kws
        _minPrice = arg if opt in ("-m") else _minPrice
        _maxPrice = arg if opt in ("-x") else _maxPrice
        _dist = arg if opt in ("-d") else _dist
        _order = arg if opt in ("-o") else _order
        _lat = arg if opt in ("-l") else _lat
        _lng = arg if opt in ("-g") else _lng
    
    if not _kws:
        usage()
        sys.exit(2)

    return _kws, _minPrice, _maxPrice, _dist, _order, _lat, _lng

def main(argv):

    # Process command line arguments
    _kws, _minPrice, _maxPrice, _dist, _order, _lat, _lng = extractArguments(argv)

    print ("Searching", _kws)
    urlSearch = ('http://es.wallapop.com/search?'
                'kws=' + _kws + '&'
                'minPrice=' + _minPrice + '&'
                'maxPrice=' + _maxPrice + '&'
                'dist=' + _dist + '&'
                'order=' + _order + '&'
                'lat=' + _lat + '&'
                'lng=' + _lng
    )
    wallAlert(urlSearch)

if __name__ == "__main__":
    main(sys.argv[1:])

