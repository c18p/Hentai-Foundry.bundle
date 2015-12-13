NAME   = 'Hentai-Foundry'
PREFIX = '/photos/hentai-foundry'
ICON = "icon-default.png"
URL_BASE = 'http://www.hentai-foundry.com'
PARAMS   = "?enterAgree=1&size=1550"
PATHS = {'featured': "/pictures/featured",
     'recent':   "/pictures/recent/all",
     'popular':  '/pictures/popular',
     'random':   '/pictures/random',
     'user':     '/pictures/user',
     'category': '/categories',
}
SORTABLE_PATHS  = [PATHS['user'], PATHS['category']]
FAVOURITE_PATHS = [PATHS['user'], PATHS['category']] 
SORT_METHODS = ["date_new","views most","rating highest","faves most","popularity most"]
####################################################################################################
def Start():

    ObjectContainer.title1 = NAME

    HTTP.CacheTime  = 0
    HTTP.User_Agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'

    # Session start
    HTTP.ClearCookies()
    res = HTTP.Request(URL_BASE + PARAMS, immediate=True)
    Dict['cookie'] = HTTP.CookiesForURL(URL_BASE)

    if not 'favourites' in Dict:
        Dict['favourites'] = []

    if 'categories' in Dict: 
        del Dict['categories']

    Dict.Save()

@handler(PREFIX, NAME)
def MainMenu():       

    oc = ObjectContainer()

    oc.add(DirectoryObject(
        key   = Callback(Browse, path='/pictures/featured', page=1),
        title = u'%s' % L('featured')
    ))

    oc.add(DirectoryObject(
        key   = Callback(Browse, path='/pictures/recent/all', page=1),
        title = u'%s' % L('recent')
    ))

    oc.add(DirectoryObject(
        key   = Callback(Browse, path='/pictures/popular', page=1),
        title = u'%s' % L('popular')
    ))

    oc.add(DirectoryObject(
        key   = Callback(Browse, path='/pictures/random', page=1),
        title = u'%s' % L('random')
    ))

    oc.add(DirectoryObject(
        key = Callback(Favourites),
        title = u'%s' % L('favourites'),
    ))

    oc.add(DirectoryObject(
        key   = Callback(BrowseCategories),
        title = u'%s'% L('categories'),
    ))

    oc.add(PrefsObject(
        title = L('preferences'),
    ))

    return oc

# filters are applied to a session by posting to /site/filters. all requests made will then have these filters applied. (assuming the page can be filtered)
def Sort(token, order='rating highest'):

    data = {"YII_CSRF_TOKEN":   token,
        "rating_nudity":    3,
        "rating_violence":  3,
        "rating_profanity": 3,
        "rating_racism":    3,
        "rating_sex":       3,
        "rating_spoilers":  3,
        "rating_yaoi":      1,
        "rating_yuri":      1,
        "rating_teen":      1,
        "rating_guro":      0,
        "rating_furry":     0,
        "rating_beast":     0,
        "rating_male":      1,
        "rating_female":    1,
        "rating_futa":      1,
        "rating_other":     1,
        "filter_media":     "A",
        "filter_type":      1, #0 all, 1 pictures, 2 flash
        "filter_order":     order
        # date_new,date_old,update_new,update_old,a-z,z-a,views most,rating highest,
        # comments most,faves most,popularity most
    }
    res = HTTP.Request(URL_BASE + '/site/filters', headers={'Cookie': Dict['cookie']}, values=data, immediate=True)        

@route(PREFIX + '/addfav', page=int)
def AddFavourite(path, page=1, sort=""):

    if not path in Dict['favourites']:
        Dict['favourites'].append(path)
        Dict.Save()
    return Browse(path, page=page, sort=sort)

@route(PREFIX + '/remfav', page=int)
def RemFavourite(path, page=1, sort=""):

    if path in Dict['favourites']:
        Dict['favourites'].remove(path)
        Dict.Save()
    return Browse(path, page=page, sort=sort)

@route(PREFIX + '/favourites')
def Favourites():

    oc = ObjectContainer()
    for item in Dict['favourites']:
        oc.add(DirectoryObject(
            key   = Callback(Browse, path=item),
            title = u'%s' % item,
        ))
    return oc

def PathIsSortable(path):

    for x in SORTABLE_PATHS:
        if x in path: return True
    return False

def PathIsFavouritable(path):

    for x in FAVOURITE_PATHS:
        if x in path: return True
    return False

@route(PREFIX + '/browse', page=int)
def Browse(path, page=1, sort=""):

    oc = ObjectContainer()

    url = URL_BASE + path + '/page/%d' % page + PARAMS

    # Sort if needed
    if sort:
        data  = HTML.ElementFromString(HTTP.Request(url, headers={'Cookie': Dict['cookie']}).content)
        token = str(data.xpath("//input[@name='YII_CSRF_TOKEN']/@value")[0])
        Sort(token, order=sort)

    # Get the page
    data = HTML.ElementFromString(HTTP.Request(url, headers={'Cookie': Dict['cookie']}).content)

    # Add the add/remove from favourites
    if PathIsFavouritable(path):
        if path in Dict['favourites']:
            oc.add(DirectoryObject(
                key = Callback(RemFavourite, path=path, page=page, sort=sort),
                title = u'%s' % L('remove favourite')
            ))
        else:
            oc.add(DirectoryObject(
                key = Callback(AddFavourite, path=path, page=page, sort=sort),
                title = u'%s' % L('add favourite')
            ))

    # Add the sort options, only on paths that are sortable
    if PathIsSortable(path):
        for method in SORT_METHODS:
            oc.add(DirectoryObject(
                key = Callback(Browse, path=path, page=page, sort=method),
                title = method
            ))      

    # Add the images
    pics = data.xpath("//td[@class='thumb_square']")
    for item in pics:
        title = item.xpath("div[@class='thumbTitle']/a/text()")[0]
        thumb = 'http:' + item.xpath("table/tr/td/a/img[@class='thumb']/@src")[0]
        url   = URL_BASE + item.xpath("div[@class='thumbTitle']/a/@href")[0]
        user  = item.xpath('a/text()')[0]

        oc.add(PhotoObject(
            url   = url,
            thumb = Resource.ContentsOfURLWithFallback(thumb),
            title = u'%s - %s' % (title, user),
        ))

        # add shortcut to the user if this isn't a users page.
        if not PATHS['user'] in path and Client.Platform not in ['Plex Home Theater', 'OpenPHT']:
            oc.add(DirectoryObject(
                key   = Callback(Browse, path=PATHS['user']+'/%s'%user, page=1),
                title = u'>> %s: %s' % (L('view user'), user),
                thumb = Resource.ContentsOfURLWithFallback(thumb),
            ))

    # Add next button if needed
    if data.xpath("//ul[@class='yiiPager']/li[@class='next']") and Client.Platform not in ['Plex Home Theater', 'OpenPHT']:
        oc.add(NextPageObject(key=Callback(Browse, path=path, page=page+1, sort=sort)))

    return oc

@route(PREFIX + '/categories')
def BrowseCategories(path=""):

    if not 'categories' in Dict:
        GetCategories()

    oc = ObjectContainer()

    data = Dict['categories']

    if len(path) > 0:
        for x in path.split(','):
            if 'children' in data:
                data = data['children']
            data = data[x]

    if 'path' in data:
        oc.add(DirectoryObject(
            key   = Callback(Browse, path=data['path'], page=1),
            title = ' :Browse Entire Category:'
        ))

    if 'children' in data:
        data = data['children']

    for k in data:

        do = DirectoryObject()

        do.title = u'%s' % k

        if data[k]['children']:
            do.key = Callback(BrowseCategories, path='%s,%s'% (path,k) if path else k)
        else:
            do.key = Callback(Browse, path=data[k]['path'], page=1)

        oc.add(do)

    oc.objects.sort(key=lambda obj: obj.title, reverse=False)

    return oc

def GetCategories():

    Dict['categories'] = {}

    data = HTML.ElementFromURL(URL_BASE + '/category/browse' + PARAMS)

    level_1  = data.xpath("//div[@class='browseCategoriesDiv']/ul[@class='list_level_1']")[0]
    cat_dict = ListToDict(level_1)

    Dict['categories'] = cat_dict
    Dict.Save()

# the lists aren't properly nested. This will parse it into a dict
def ListToDict(ul):

    result = {}

    for tag in ul.getchildren():
        if tag.tag == 'li':
            key = str(tag.xpath('a/text()')[0]).replace('&', 'and').replace(',', '').replace('(', '').replace(')', '')
            if tag.getnext() and tag.getnext().tag == 'ul':
                result[key] = {'path': str(tag.xpath('a/@href')[0]), 'children': ListToDict(tag.getnext())}
            else:
                result[key] = {'path': str(tag.xpath('a/@href')[0]), 'children': {}}

    return result