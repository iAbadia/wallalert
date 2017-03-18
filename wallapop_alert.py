#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import demiurge, sys, getopt, os, pickle, tempfile, time

urlWallapop = 'http://es.wallapop.com'
urlWallapopMobile = 'http://p.wallapop.com/i/'
SAVE_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'alertWallapop.pkl')
HISTORY_SIZE = 20   
data_save = True
push_bullet = False
debug = True

# Notify params
pushToken = '<your token here>'
email = '<your email here>'

# Debug
def printD(str, good):
    # If ok, print +, else -
    global debug
    if debug:
        if good:
            print('[+] ' + str)
        else:
            print('[-] ' + str)


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

def wallAlert(urlSearch, notify):
    # Load after data search
    data_temp = []
    try:
        dataFile = open(SAVE_LOCATION, 'rb')
        data_save = pickle.load(dataFile)
    except:
        data_save = open(SAVE_LOCATION, 'wb+')
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

        # Notify, if needed
        if notify:
            # Send Alert
            printD(title + body + url, True)
            printD('-' * 10, True)
            if push_bullet:
                sendPushBullet(pushToken, email, title, body, applink)
    # Save data
    data_save = open(SAVE_LOCATION, 'wb')
    pickle.dump(data_temp, data_save)

def usage():
    print("Usage:", __file__," -k keywords [-m min price] [-x max price] [-d distance] [-l latitude] [-g longitude]")
    print('Ex:   ', __file__,' -k "ps4 games" -m 10 -x 15 -d "0_1000" -l "40.4378693" -g "-3.819963"') 
    print('')
    optionsHelp()

def optionsHelp():
    print('   KEYWORDS')
    print('     -k : Keywords. E.g. "gameboy pokemon"')
    print('   PRICE')
    print('     -m : Min price [0..20000]. Default: no limit')
    print('     -x : Max price [0..20000]. Default: no limit')
    print('   SCOPE')
    print('     -d : Distance [0_ -> no limit, 0_10000 -> 10km, 0_5000 -> 5km, 0_1000 -> 1km]. Default: no limit')
    #print('     -o : Order. [distance-asc -> Near first, salePrice-asc -> Cheap first, salePrice-des -> Expensive first, creationDate-des -> New first]. Default: creationDate-des')
    print('   LOCATION')
    print('     -l : Latitude. Default: 40.4378693')
    print('     -g : Longitude. Default: -3.819963')

def extractArguments(argv):
    # Default values
    _minPrice = ""
    _maxPrice = ""
    _dist = "0_"
    _order = "creationDate-dec"
    _kws = ""
    _lat = "40.4378693"
    _lng = "-3.819963"

    # Get opts
    try:
        opts, args = getopt.getopt(argv, "k:m:x:d:l:g:o:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    
    # Parse opts
    for opt, arg in opts:
        _kws = arg if opt in ("-k") else _kws
        _minPrice = arg if opt in ("-m") else _minPrice
        _maxPrice = arg if opt in ("-x") else _maxPrice
        _dist = arg if opt in ("-d") else _dist
        _order = arg if opt in ("-o") else _order
        _lat = arg if opt in ("-l") else _lat
        _lng = arg if opt in ("-g") else _lng

    # Check min reqs (keywords)
    if not _kws:
        usage()
        sys.exit(2)

    return _kws, _minPrice, _maxPrice, _dist, _order, _lat, _lng

def main(argv):

    # Process command line arguments
    _kws, _minPrice, _maxPrice, _dist, _order, _lat, _lng = extractArguments(argv)

    printD("Searching for: " + _kws, True)
    urlSearch = ('http://es.wallapop.com/search?'
                'kws=' + _kws + '&'
                'minPrice=' + _minPrice + '&'
                'maxPrice=' + _maxPrice + '&'
                'dist=' + _dist + '&'
                'order=' + _order + '&'
                'lat=' + _lat + '&'
                'lng=' + _lng
    )

    printD('URL: ' + urlSearch, True)

    # Fill DB
    wallAlert(urlSearch, True)

    # Query every 30 secs
    #while True:
     #   wallAlert(urlSearch, True)
      #  time.sleep(30)

if __name__ == "__main__":
    main(sys.argv[1:])
