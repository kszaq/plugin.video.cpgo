# -*- coding: UTF-8 -*-
import sys
import re
import os

try:
    # For Python 3.0 and later
    import urllib.parse as urlparse
except ImportError:
    # Fall back to Python 2's urllib2
    import urlparse


import requests
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs

import string

try:
    import http.cookiejar as cookielib
except ImportError:
    import cookielib


try:
    from urllib.parse import urlencode, quote_plus, quote
except ImportError:
    from urllib import urlencode, quote_plus, quote

import random
import time

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(urlparse.parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.cpgo')

PATH = addon.getAddonInfo('path')
if sys.version_info >= (3, 0, 0):
    DATAPATH = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
else:
    DATAPATH = xbmc.translatePath(
        addon.getAddonInfo('profile')).decode('utf-8')
RESOURCES = PATH + '/resources/'
FANART = RESOURCES + 'fanart.jpg'
sys.path.append(os.path.join(RESOURCES, "lib"))

exlink = params.get('url', None)
name = params.get('title', None)
offse = params.get('page', None)
rys = params.get('image', None)

UA = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36'


auth_url = 'https://b2c.redefine.pl/rpc/auth/'
navigate_url = 'https://b2c.redefine.pl/rpc/navigation/'

clid = addon.getSetting('clientId')
devid = addon.getSetting('devid')

stoken = addon.getSetting('sesstoken')
sexpir = addon.getSetting('sessexpir')
skey = addon.getSetting('sesskey')

file_name = addon.getSetting('fname')
path = addon.getSetting('path')

def build_url(query):
    return base_url + '?' + urlencode(query)


def add_item(url, name, image, folder, mode, isPlayable=True,
             infoLabels=False, FANART=None, itemcount=1, page=0):

    list_item = xbmcgui.ListItem(label=name)

    if isPlayable:
        list_item.setProperty("IsPlayable", 'true')
        contextMenuItems = []
        contextMenuItems.append(('Informacja', 'XBMC.Action(Info)'))
        list_item.addContextMenuItems(contextMenuItems, replaceItems=False)

    if not infoLabels:
        infoLabels = {'title': name, 'plot': name}

    list_item.setInfo(type="video", infoLabels=infoLabels)

    FANART = FANART if FANART else image
    list_item.setArt({'thumb': image, 'poster': image,
                     'banner': image, 'fanart': FANART})
    xbmcplugin.addDirectoryItem(
        handle=addon_handle,
        url=build_url({'title': name, 'mode': mode, 'url': url,
                      'page': page, 'image': image}),
        listitem=list_item,
        isFolder=folder)


def PlayPolsat(stream_url, data):
    import inputstreamhelper
    #from urllib import quote
    PROTOCOL = 'mpd'
    DRM = 'com.widevine.alpha'
    LICENSE_URL = 'https://gm2.redefine.pl/rpc/drm/'
    is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)

    UAcp = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36'
    if is_helper.check_inputstream():
        play_item = xbmcgui.ListItem(path=stream_url)
        play_item.setArt({'thumb': rys, 'poster': rys,
                         'banner': rys, 'fanart': FANART})

        play_item.setMimeType('application/xml+dash')
        play_item.setContentLookup(False)
        if sys.version_info >= (3, 0, 0):
            play_item.setProperty('inputstream', is_helper.inputstream_addon)
        else:
            play_item.setProperty(
                'inputstreamaddon',
                is_helper.inputstream_addon)
        play_item.setProperty("IsPlayable", "true")
        play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
        play_item.setProperty('inputstream.adaptive.license_type', DRM)

        play_item.setProperty(
            'inputstream.adaptive.manifest_update_parameter', 'full')
        play_item.setProperty(
            'inputstream.adaptive.stream_headers',
            'Referer: https://go.cyfrowypolsat.pl')
        play_item.setProperty('inputstream.adaptive.license_key',
                              LICENSE_URL + '|Content-Type=application%2Fjson&Referer=https://go.cyfrowypolsat.pl/&User-Agent=' + quote(UAcp) +
                              '|' + data + '|JBlicense')
        play_item.setProperty(
            'inputstream.adaptive.license_flags',
            "persistent_storage")

    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def checkAccess(id):
    stoken = addon.getSetting('sesstoken')
    sexpir = addon.getSetting('sessexpir')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json; utf-8',
        'Origin': 'https://go.cyfrowypolsat.pl',
        'Connection': 'keep-alive',
    }

    dane = stoken + '|' + sexpir + '|navigation|getMedia'
    authdata = getHmac(dane)

    data = {
        "jsonrpc": "2.0",
        "method": "getMedia",
        "id": 1,
        "params": {
            "cpid": 1,
            "mediaId": id,
            "ua": "cpgo_www/2015",
            "authData": {
                "sessionToken": authdata}}}

    response = requests.post(
        navigate_url,
        headers=headers,
        json=data,
        timeout=15).json()
    prod = response['result']['product']
    prodid = prod['id']
    prodtype = prod['type']
    prodstype = prod['subType']

    dane = stoken + '|' + sexpir + '|payments|checkProductsAccess'
    authdata = getHmac(dane)

    data = {"jsonrpc": "2.0",
            "method": "checkProductsAccess",
            "id": 1,
            "params": {"products": [{"id": prodid,
                                     "type": prodtype,
                                     "subType": prodstype}],
                       "ua": "cpgo_www/2015",
                       "authData": {"sessionToken": authdata}}}
    response = requests.post(
        'https://b2c.redefine.pl/rpc/payments/',
        headers=headers,
        json=data,
        timeout=15).json()
    dostep = response['result'][-1]['access']['statusDescription']
    if 'no access' in dostep:
        return False
    else:
        return True


def playVOD(id):
    dostep = checkAccess(id)
    if dostep:
        playCPGO(id, cpid=1)
    else:
        xbmcgui.Dialog().notification(
            '[B]Uwaga[/B]',
            'Brak dostępu do materiału',
            xbmcgui.NOTIFICATION_INFO,
            6000)
        return False


def playCPGO(id, cpid=0):
    stoken = addon.getSetting('sesstoken')
    sexpir = addon.getSetting('sessexpir')

    dane = stoken + '|' + sexpir + '|auth|getSession'
    authdata = getHmac(dane)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json; utf-8',
        'Origin': 'https://go.cyfrowypolsat.pl',
        'Connection': 'keep-alive',
    }

    data = {"jsonrpc": "2.0", "method": "getSession", "id": 1, "params": {
        "ua": "cpgo_www/2015", "authData": {"sessionToken": authdata}}}

    response = requests.post(
        auth_url,
        headers=headers,
        json=data,
        timeout=15).json()
    sesja = response['result']['session']

    sesstoken = sesja['id']
    sessexpir = str(sesja['keyExpirationTime'])
    sesskey = sesja['key']

    addon.setSetting('sesstoken', sesstoken)
    addon.setSetting('sessexpir', str(sessexpir))
    addon.setSetting('sesskey', sesskey)

    stoken = addon.getSetting('sesstoken')
    sexpir = addon.getSetting('sessexpir')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'text/plain;charset=UTF-8',
        'Origin': 'https://go.cyfrowypolsat.pl',
        'Connection': 'keep-alive',
        'Referer': 'https://go.cyfrowypolsat.pl/tv/channel/' + id,
    }
    dane = stoken + '|' + sexpir + '|navigation|prePlayData'
    authdata = getHmac(dane)
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "prePlayData",
        "params": {
            "ua": "cpgo_www_html5/2 (Windows 10; widevine=true)",
            "cpid": cpid,
            "mediaId": id,
            "authData": {
                "sessionToken": authdata}}}

    response = requests.post(
        navigate_url,
        headers=headers,
        json=data,
        timeout=15).json()
    playback = response['result']['mediaItem']['playback']
    mediaid = playback['mediaId']['id']
    mediaSources = playback['mediaSources'][0]
    keyid = mediaSources['keyId']
    sourceid = mediaSources['id']

    try:
        cc = mediaSources['authorizationServices']['pseudo']
        dane = stoken + '|' + sexpir + '|drm|getPseudoLicense'
        authdata = getHmac(dane)
        devcid = devid.replace('-', '')

        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getPseudoLicense",
            "params": {
                "ua": "cpgo_www_html5/2",
                "cpid": 1,
                "mediaId": mediaid,
                "sourceId": sourceid,
                "deviceId": {
                    "type": "other",
                    "value": devcid},
                "authData": {
                    "sessionToken": authdata}}}
        response = requests.post(
            'https://b2c.redefine.pl/rpc/drm/',
            headers=headers,
            json=data,
            timeout=15).json()
        str_url = response['result']['url']

        PlayPolsatPseudo(str_url)
    except BaseException:

        stream_url = mediaSources['url']

        dane = stoken + '|' + sexpir + '|drm|getWidevineLicense'
        authdata = getHmac(dane)
        devcid = devid.replace('-', '')
        data = quote(
            '{"jsonrpc":"2.0","id":1,"method":"getWidevineLicense","params":{"cpid":%d,"mediaId":"' %
            cpid +
            mediaid +
            '","sourceId":"' +
            sourceid +
            '","keyId":"' +
            keyid +
            '","object":"b{SSM}","deviceId":{"type":"other","value":"' +
            devcid +
            '"},"ua":"cpgo_www_html5/2","authData":{"sessionToken":"' +
            authdata +
            '"}}}')
        PlayPolsat(stream_url, data)
    return


def PlayPolsatPseudo(str_url):
    play_item = xbmcgui.ListItem(path=str_url)

    play_item.setContentLookup(False)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def loginCPgo():
    headers = {
        'Host': 'b2c.redefine.pl',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json; utf-8',
        'Origin': 'https://go.cyfrowypolsat.pl',
        'DNT': '1',
        'Referer': 'https://go.cyfrowypolsat.pl/',
    }
    osinfo = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36"
    uaipla = "www_iplatv/12345 (Mozilla/5.0 Windows NT 10.0; WOW64 AppleWebKit/537.36 KHTML, like Gecko Chrome/62.0.3202.9 Safari/537.36)"

    clid = addon.getSetting('clientId')
    devid = addon.getSetting('devid')

    stoken = addon.getSetting('sesstoken')
    sexpir = addon.getSetting('sessexpir')
    skey = addon.getSetting('sesskey')

    def gen_hex_code(myrange=6):
        return ''.join([random.choice('0123456789ABCDEF')
                       for x in range(myrange)])

    def ipla_system_id():
        myrand = gen_hex_code(10) + '-' + gen_hex_code(4) + '-' + \
            gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(12)

        return myrand
    if not clid and not devid:

        clientid = ipla_system_id()
        deviceid = ipla_system_id()

        addon.setSetting('clientId', clientid)
        addon.setSetting('devid', deviceid)
        loginCPgo()

    else:

        usernameCP = addon.getSetting('usernameCP')
        passwordCP = addon.getSetting('passwordCP')
        if usernameCP and passwordCP:
            data = {
                "jsonrpc": "2.0",
                "method": "login",
                "id": 1,
                "params": {
                    "authData": {
                        "loginICOK": usernameCP,
                        "passwordICOK": passwordCP,
                        "deviceIdICOK": {
                            "value": devid,
                            "type": "other"}},
                    "ua": "cpgo_www/2015"}}
            response = requests.post(
                auth_url,
                headers=headers,
                json=data,
                timeout=15).json()
            try:
                blad = response['error']
                if blad:
                    message = blad['message']
                    xbmcgui.Dialog().notification(
                        '[B]Logowanie[/B]', message, xbmcgui.NOTIFICATION_INFO, 6000)
                return False

            except BaseException:

                sesja = response['result']['session']

                sesstoken = sesja['id']
                sessexpir = str(sesja['keyExpirationTime'])
                sesskey = sesja['key']

                addon.setSetting('sesstoken', sesstoken)
                addon.setSetting('sessexpir', str(sessexpir))
                addon.setSetting('sesskey', sesskey)
                accesgroup = response['result']['accessGroups']

                addon.setSetting('accgroups', str(accesgroup))

                return True

        else:
            xbmcgui.Dialog().notification(
                '[B]Logowanie[/B]',
                'Błędne dane logowania.',
                xbmcgui.NOTIFICATION_INFO,
                6000)
            return False


def home():
    logged = loginCPgo()
    if logged:
        add_item(
            name='Zalogowany',
            url='',
            mode=' ',
            image='DefaultUser.png',
            folder=False,
            isPlayable=False,
            FANART=FANART)
        add_item(
            name='Telewizja',
            url='',
            mode='tvcpgo',
            image='',
            folder=True,
            isPlayable=False,
            FANART=FANART)
        add_item(
            name='VOD',
            url='',
            mode='vodmain',
            image='',
            folder=True,
            isPlayable=False,
            FANART=FANART)
    else:
        add_item(
            '',
            '[B]Zaloguj[/B]',
            'DefaultAddonService.png',
            False,
            'settings',
            False,
            FANART=FANART)
    xbmcplugin.endOfDirectory(addon_handle)

def channels():
    headers = {
        'Host': 'b2c.redefine.pl',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json; utf-8',
        'Origin': 'https://go.cyfrowypolsat.pl',
        'DNT': '1',
        'Referer': 'https://go.cyfrowypolsat.pl/',
    }

    stoken = addon.getSetting('sesstoken')
    sexpir = addon.getSetting('sessexpir')

    items = []
    myperms = []
    ff = addon.getSetting('accgroups')
    lista = eval(ff)

    for l in lista:
        if 'sc:' in l:
            myperms.append(l)

    dane = stoken + '|' + sexpir + '|navigation|getTvChannels'
    authdata = getHmac(dane)
    data = {
        "jsonrpc": "2.0",
        "method": "getTvChannels",
        "id": 1,
        "params": {
            "filters": [],
            "ua": "cpgo_www/2015",
            "authData": {
                "sessionToken": authdata}}}
    response = requests.post(
        navigate_url,
        headers=headers,
        json=data,
        timeout=15).json()
    aa = response['result']['results']
    for i in aa:
        item = {}

        channelperms = i['grantExpression'].split('*')
        channelperms = [w.replace('+plat:all', '') for w in channelperms]

        for j in myperms:

            if j in channelperms or i['title'] == 'Polsat' or i['title'] == 'TV4':
                item['img'] = i['thumbnails'][-1]['src'].encode('utf-8')
                item['id'] = i['id']

                item['title'] = i['title'].upper().encode('utf-8')
                item['plot'] = i['category']['description'].encode('utf-8')
                items.append(item)
    dupes = []
    filter = []
    for entry in items:
        # xbmc.log('@#@entryentryentryentry: %s' % str(entry), xbmc.LOGNOTICE)
        if not entry['id'] in dupes:
            filter.append(entry)
            dupes.append(entry['id'])

    addon.setSetting('kanaly', str(dupes))

    return filter


def tvmain():
    items = channels()
    itemz = len(items)

    dups = getEpgs()

    for item in items:
        try:
            opis = dups[0][item.get('id')]
        except BaseException:
            opis = ''
        add_item(
            name=item.get('title'),
            url=item.get('id'),
            mode='playCPGO',
            image=item.get('img'),
            folder=False,
            isPlayable=True,
            infoLabels={
                'title': item.get('title'),
                'plot': opis},
            itemcount=itemz,
            FANART=FANART)

    xbmcplugin.endOfDirectory(addon_handle)


def newtime(ff):
    from datetime import datetime
    ff = re.sub(':\\d+Z', '', ff)
    dd = re.findall('T(\\d+)', ff)[0]
    dzien = re.findall('(\\d+)T', ff)[0]
    dd = '{:>02d}'.format(int(dd) + 2)
    if dd == '24':
        dd = '00'
        dzien = '{:>02d}'.format(int(dzien) + 1)
    if dd == '25':
        dd = '01'
        dzien = '{:>02d}'.format(int(dzien) + 1)
    ff = re.sub('(\\d+)T(\\d+)', '%sT%s' % (dzien, int(dd)), ff)

    import time
    try:
        format_date = datetime.strptime(ff, '%Y-%m-%dT%H:%M')
    except TypeError:
        format_date = datetime(*(time.strptime(ff, '%Y-%m-%dT%H:%M')[0:6]))
    dd = int('{:0}'.format(int(time.mktime(format_date.timetuple()))))

    return dd, format_date


def getEpgs():
    kanaly = addon.getSetting('kanaly')
    kanaly = eval(kanaly)

    import datetime
    now = datetime.datetime.now()
    now2 = datetime.datetime.now() + datetime.timedelta(days=1)
    aa1 = now.strftime('%Y-%m-%dT%H:%M:%S') + ('.%03dZ' %
                                               (now.microsecond / 10000))
    aa = now2.strftime('%Y-%m-%dT%H:%M:%S') + ('.%03dZ' %
                                               (now.microsecond / 10000))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json; utf-8',
        'Origin': 'https://go.cyfrowypolsat.pl',
        'Connection': 'keep-alive',
        'Referer': 'https://go.cyfrowypolsat.pl/program',
    }
    stoken = addon.getSetting('sesstoken')
    sexpir = addon.getSetting('sessexpir')

    dane = stoken + '|' + sexpir + '|navigation|getChannelsProgram'
    authdata = getHmac(dane)

    data = {
        "jsonrpc": "2.0",
        "method": "getChannelsProgram",
        "id": 1,
        "params": {
            "channelIds": kanaly,
            "fromDate": aa1,
            "toDate": aa,
            "ua": "cpgo_www/2015",
            "authData": {
                "sessionToken": authdata}}}
    response = requests.post(
        navigate_url,
        headers=headers,
        json=data,
        timeout=15).json()

    dupek = []
    import datetime
    now = datetime.datetime.now()
    ab = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    from datetime import datetime
    import time
    try:
        format_date = datetime.strptime(ab, '%Y-%m-%dT%H:%M:%SZ')
    except TypeError:
        format_date = datetime(*(time.strptime(ab, '%Y-%m-%dT%H:%M:%SZ')[0:6]))
    zz = int('{:0}'.format(int(time.mktime(format_date.timetuple()))))

    items = {}
    for kanal in kanaly:

        el1 = ''
        if kanal in response['result']:
            dane = response['result'][kanal]
            for i in range(len(dane)):
                try:
                    nowy, format_date = newtime(dane[i]["startTime"])
                    nowy2, format_date2 = newtime(dane[i + 1]["startTime"])
                    trwa = nowy2 - nowy
                    if nowy < zz and nowy + trwa > zz:
                        tyt = dane[i]["title"]
                        tyt2 = dane[i]["genre"]
                        cc = re.sub(':\\d+$', '', str(format_date))
                        el1 += '[COLOR khaki]' + cc + '[/COLOR] - ' + \
                            tyt + ' [COLOR violet](' + tyt2 + ')[/COLOR][CR]'
                    elif nowy > zz:
                        tyt = dane[i]["title"]
                        tyt2 = dane[i]["genre"]
                        cc = re.sub(':\\d+$', '', str(format_date))
                        el1 += '[COLOR khaki]' + cc + '[/COLOR] - ' + \
                            tyt + ' [COLOR violet](' + tyt2 + ')[/COLOR][CR]'

                except BaseException:
                    pass

        else:
            continue
        items[kanal] = el1
    dupek.append(items)

    return dupek


def vodmain():
    add_item(
        name='Szukaj',
        url='',
        mode='vodszukaj',
        image=RESOURCES +
        'search.png',
        folder=True,
        isPlayable=False,
        FANART=FANART)

    add_item(
        name='HBO KIDS BAJKI',
        url='5013942',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/j9/j9p3zzbbmvdmh9chn5q6getonjap53es.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='HBO KIDS FILMY',
        url='5013941',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/dz/dz71b4398yukkaun4mjym6ifdqc9acsv.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='HBO SERIALE',
        url='5013940',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/47/47oujwhuddyeu2fzmzai4eaqkad1nexu.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='HBO FILMY',
        url='5013939',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/m8/m8scw85v5cu6q2ojo4mv54c9xhy8qmdh.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='SERIAL',
        url='5006931',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/64/6443791fd5030a9be3114f72ab366ff5.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='SPORT',
        url='5006453',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/d4/d4ce016f9f8c11eb1f6c14da33ceb965.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='WIEDZA',
        url='5005992',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/16/161e7fa69332ebfd9d06688cfc415a70.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='ROZRYWKA',
        url='5005431',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/3b/3bae15a5a5009189bdd40e54ad99f1e8.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='NEWS',
        url='5005294',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/61/61e3597b651a7b223fe2c52a753d33eb.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='DZIECI',
        url='5005051',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/8d/8d10fc3ff57b5019a8b546836dfbbd8f.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    add_item(
        name='FILM',
        url='5005049',
        mode='vodlist',
        image='https://r.dcs.redcdn.pl/http/o2/redefine/redb/a5/a548757da60de0894d63a6f91becd5a3.jpg',
        folder=True,
        isPlayable=False,
        FANART=FANART)
    xbmcplugin.endOfDirectory(addon_handle)


def vodSzukaj(query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json; utf-8',
        'Origin': 'https://go.cyfrowypolsat.pl',
        'Connection': 'keep-alive',
    }
    stoken = addon.getSetting('sesstoken')
    sexpir = addon.getSetting('sessexpir')

    items = []
    myperms = []

    ff = addon.getSetting('accgroups')
    lista = eval(ff)

    for l in lista:
        if 'sc:' in l:
            myperms.append(l)
        if 'oth:' in l:
            myperms.append(l)

    dane = stoken + '|' + sexpir + '|navigation|searchContentWithTreeNavigation'
    authdata = getHmac(dane)

    data = {
        "jsonrpc": "2.0",
        "method": "searchContentWithTreeNavigation",
        "id": 1,
        "params": {
            "query": query,
            "limit": 50,
            "ua": "cpgo_www/2015",
            "authData": {
                "sessionToken": authdata}}}
    response = requests.post(
        navigate_url,
        headers=headers,
        json=data,
        timeout=15).json()
    #
    mud = 'playVOD'
    folder = False
    isplay = False
    aa = response['result']['results']
    if 'keyCategoryId' in aa[0]:
        mud = 'vodlist'
        folder = True
        isplay = False
    otal = response['result']['total']

    for i in aa:
        item = {}
        for j in myperms:
            item['img'] = i['thumbnails'][-1]['src'].encode('utf-8')
            item['id'] = i['id']
            try:
                item['title'] = i['title'].upper().encode('utf-8')
            except BaseException:
                item['title'] = i['name'].upper().encode('utf-8')
            item['plot'] = i['description'].encode('utf-8')
            items.append(item)

    dupes = []
    filter = []
    for entry in items:
        if not entry['id'] in dupes:
            filter.append(entry)
            dupes.append(entry['id'])
    items = filter
    itemz = len(items)

    for item in items:

        add_item(
            name=item.get('title'),
            url=item.get('id'),
            mode=mud,
            image=item.get('img'),
            folder=folder,
            isPlayable=isplay,
            infoLabels=item,
            itemcount=itemz,
            FANART=FANART)
    xbmcplugin.endOfDirectory(addon_handle)


def vodList(id):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json; utf-8',
        'Origin': 'https://go.cyfrowypolsat.pl',
        'Connection': 'keep-alive',
    }

    stoken = addon.getSetting('sesstoken')
    sexpir = addon.getSetting('sessexpir')

    items = []
    myperms = []
    ff = addon.getSetting('accgroups')
    lista = eval(ff)

    for l in lista:
        if 'sc:' in l:
            myperms.append(l)
        if 'oth:' in l:
            myperms.append(l)

    dane = stoken + '|' + sexpir + '|navigation|getCategoryContentWithFlatNavigation'
    authdata = getHmac(dane)
    data = {
        "jsonrpc": "2.0",
        "method": "getCategoryContentWithFlatNavigation",
        "id": 1,
        "params": {
            "catid": int(id),
            "limit": 50,
            "offset": int(offse),
            "collection": {
                "type": "sortedby",
                "name": "A-Z",
                "default": True,
                "value": "13"},
            "ua": "cpgo_www/2015",
            "authData": {
                "sessionToken": authdata}}}

    response = requests.post(
        navigate_url,
        headers=headers,
        json=data,
        timeout=15).json()
    #
    mud = 'playVOD'
    folder = False
    isplay = True

    aa = response['result']['results']
    if 'keyCategoryId' in aa[0]:
        mud = 'vodlist'
        folder = True
        isplay = False
    otal = response['result']['total']

    for i in aa:
        item = {}

        for j in myperms:

            item['img'] = i['thumbnails'][-1]['src'].encode('utf-8')
            item['id'] = i['id']
            try:
                item['title'] = i['title'].upper().encode('utf-8')
            except BaseException:
                item['title'] = i['name'].upper().encode('utf-8')
            item['plot'] = i['description'].encode('utf-8')
            items.append(item)

    dupes = []
    filter = []

    for entry in items:
        if not entry['id'] in dupes:
            filter.append(entry)
            dupes.append(entry['id'])
    items = filter
    itemz = len(items)

    for item in items:

        add_item(
            name=item.get('title'),
            url=item.get('id'),
            mode=mud,
            image=item.get('img'),
            folder=folder,
            isPlayable=isplay,
            infoLabels=item,
            itemcount=itemz,
            FANART=FANART)

    if int(offse) + 50 < otal:
        add_item(
            name='Następna strona',
            url=id,
            mode='vodlist',
            image=RESOURCES +
            'nextpage.png',
            folder=True,
            isPlayable=False,
            infoLabels=None,
            itemcount=itemz,
            page=int(offse) +
            50,
            FANART=FANART)

    xbmcplugin.endOfDirectory(addon_handle)


def getHmac(dane):
    skey = addon.getSetting('sesskey')
    import hmac
    import hashlib
    import binascii
    import base64
    from hashlib import sha256
    ssdalej = dane
    import base64

    def base64_decode(s):
        """Add missing padding to string and return the decoded base64 string."""
        #log = logging.getLogger()
        s = str(s).strip()
        try:
            return base64.b64decode(s)
        except TypeError:
            padding = len(s) % 4
            if padding == 1:
                #log.error("Invalid base64 string: {}".format(s))
                return ''
            elif padding == 2:
                s += b'=='
            elif padding == 3:
                s += b'='
            return base64.b64decode(s)
    secretAccessKey = base64_decode(skey.replace('-', '+').replace('_', '/'))

    auth = hmac.new(secretAccessKey, ssdalej.encode("ascii"), sha256)
    vv = base64.b64encode(bytes(auth.digest())).decode("ascii")

    aa = vv
    bb = ssdalej + '|' + aa.replace('+', '-').replace('/', '_')
    return bb


def generate_m3u():
    if not loginCPgo():
        xbmcgui.Dialog().notification('CP Go', 'Przed wygenerowaniem listy należy się zalogować!', xbmcgui.NOTIFICATION_ERROR)
        return
        
    # Skopiowanko z plugin.video.pilot.wp by c0d34fun
    if file_name == '' or path == '':
        xbmcgui.Dialog().notification('CP Go', 'Ustaw nazwę pliku oraz katalog docelowy', xbmcgui.NOTIFICATION_ERROR)
        return

    xbmcgui.Dialog().notification('CP Go', 'Generuję listę M3U', xbmcgui.NOTIFICATION_INFO)
    data = '#EXTM3U\n'

    for item in channels():
        id = item.get('id', None)
        title = item.get('title', '').decode('utf-8')
        data += '#EXTINF:-1,%s\nplugin://plugin.video.cpgo?mode=playCPGO&url=%s\n' % (title, id)

    f = xbmcvfs.File(path + file_name, 'w')
    f.write(data.encode('utf-8'))
    f.close()

    xbmcgui.Dialog().notification('CP Go', 'Wygenerowano listę M3U', xbmcgui.NOTIFICATION_INFO)


if __name__ == '__main__':
    mode = params.get('mode', None)
    if mode is None:
        home()
    elif mode == 'BUILD_M3U':
        generate_m3u()
    elif mode == 'playCPGO':
        playCPGO(exlink)
    elif mode == 'tvcpgo':
        tvmain()
    elif mode == 'vodmain':
        vodmain()
    elif mode == 'vodlist':
        vodList(exlink)

    elif mode == 'playVOD':
        playVOD(exlink)

    elif mode == 'vodszukaj':
        query = xbmcgui.Dialog().input(
            u'Szukaj, Podaj tytuł...',
            type=xbmcgui.INPUT_ALPHANUM)
        if query:
            vodSzukaj(query)

    elif mode == 'settings':
        addon.openSettings()
        xbmc.executebuiltin('Container.Refresh()')
