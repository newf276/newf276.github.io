import time, requests
import xbmc, xbmcgui
from resources.lib import text
from resources.lib import dialogs
from resources.lib import settings
from resources.lib.xswift2 import plugin

API_ENDPOINT  = 'https://api-v2launch.trakt.tv'
REDIRECT_URI  = 'urn:ietf:wg:oauth:2.0:oob'
CLIENT_ID     = '5907b6b239f4ce221d1af6901b57160c37b7030ee9265efa1690e05a06d8ed31'
CLIENT_SECRET = '88ede966b4b3d549932cbd6c6df9806f010cb721fbea734e489469b4e2acd5b6'

def call_trakt(path, params={}, data=None, is_delete=False, with_auth=True, pagination=False, page=1):
    params = dict([(k, text.to_utf8(v)) for k, v in params.items() if v])
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID}

    def send_query():
        if with_auth:
            try:
                expires_at = plugin.get_setting(settings.SETTING_TRAKT_EXPIRES_AT, int)
                if time.time() > expires_at: trakt_refresh_token()
            except: pass
            token = plugin.get_setting(settings.SETTING_TRAKT_ACCESS_TOKEN, unicode)
            if token: headers['Authorization'] = 'Bearer ' + token
        if data is not None:
            assert not params
            return requests.post('%s/%s' % (API_ENDPOINT, path), json=data, headers=headers)
        elif is_delete: return requests.delete('%s/%s' % (API_ENDPOINT, path), headers=headers)
        else: return requests.get('%s/%s' % (API_ENDPOINT, path), params, headers=headers)

    def paginated_query(page):
        lists = []
        params['page'] = page
        results = send_query()
        if with_auth and results.status_code == 401 and dialogs.yesno('Authenticate Trakt', 'Do you want to authenticate with Trakt now?') and trakt_authenticate():
            response = paginated_query(1)
            return response
        results.raise_for_status()
        results.encoding = 'utf-8'
        lists.extend(results.json())
        return lists, results.headers['X-Pagination-Page-Count']
    if pagination == False:
        response = send_query()
        if with_auth and response.status_code == 401 and dialogs.yesno('Authenticate Trakt', 'Do you want to authenticate with Trakt now?') and trakt_authenticate(): response = send_query()
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.json()
    else:
        response, numpages = paginated_query(page)
        return response, numpages

def search_trakt(**search_params):
    return call_trakt('search', search_params)

def find_trakt_ids(id_type, id, query=None, type=None, year=None):
    response = search_trakt(id_type=id_type, id=id)
    if not response and query:
        response = search_trakt(query=query, type=type, year=year)
        if response and len(response) > 1: response = [r for r in response if r[r['type']]['title'] == query]
    if response:
        content = response[0]
        return content[content['type']]['ids']
    return {}

def trakt_get_device_code():
    data = {'client_id': CLIENT_ID}
    return call_trakt('oauth/device/code', data=data, with_auth=False)

def trakt_get_device_token(device_codes):
    data = {
        'code': device_codes['device_code'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET}
    start = time.time()
    expires_in = device_codes['expires_in']
    progress_dialog = xbmcgui.DialogProgress()
    progress_dialog.create('Authenticate Trakt', 'Please go to  https://trakt.tv/activate  and enter the code', str(device_codes['user_code']))
    try:
        time_passed = 0
        while not xbmc.abortRequested and not progress_dialog.iscanceled() and time_passed < expires_in:            
            try: response = call_trakt('oauth/device/token', data=data, with_auth=False)
            except requests.HTTPError as e:
                if e.response.status_code != 400: raise e
                progress = int(100 * time_passed / expires_in)
                progress_dialog.update(progress)
                xbmc.sleep(max(device_codes['interval'], 1)*1000)
            else: return response
            time_passed = time.time() - start
    finally:
        progress_dialog.close()
        del progress_dialog
    return None

def trakt_refresh_token():
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'refresh_token',
        'refresh_token': plugin.get_setting(settings.SETTING_TRAKT_REFRESH_TOKEN, unicode)}
    response = call_trakt('oauth/token', data=data, with_auth=False)
    if response:
        plugin.set_setting(settings.SETTING_TRAKT_ACCESS_TOKEN, response['access_token'])
        plugin.set_setting(settings.SETTING_TRAKT_REFRESH_TOKEN, response['refresh_token'])

def trakt_authenticate():
    code = trakt_get_device_code()
    token = trakt_get_device_token(code)
    if token:
        expires_at = time.time() + 60*60*24*30
        plugin.set_setting(settings.SETTING_TRAKT_EXPIRES_AT, str(expires_at))
        plugin.set_setting(settings.SETTING_TRAKT_ACCESS_TOKEN, token['access_token'])
        plugin.set_setting(settings.SETTING_TRAKT_REFRESH_TOKEN, token['refresh_token'])
        return True
    return False

def trakt_get_collection(type):
    return call_trakt('sync/collection/%s' % type, params={'extended': 'full'})

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_latest_releases_movies():
    return call_trakt('users/giladg/lists/latest-releases/items', params={'extended': 'full'}, pagination=False, with_auth=False)

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_imdb_top_rated_movies(page):
    result, pages = call_trakt('users/justin/lists/imdb-top-rated-movies/items', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_trending_shows_paginated(page):
    result, pages = call_trakt('shows/trending', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_popular_shows_paginated(page):
    result, pages = call_trakt('shows/popular', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_watched_shows_paginated(page):
    result, pages = call_trakt('shows/watched/weekly', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_collected_shows_paginated(page):
    result, pages = call_trakt('shows/collected/weekly', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_trending_movies_paginated(page):
    result, pages = call_trakt('movies/trending', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_popular_movies_paginated(page):
    result, pages = call_trakt('movies/popular', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_watched_movies_paginated(page):
    result, pages = call_trakt('movies/watched/weekly', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_collected_movies_paginated(page):
    result, pages = call_trakt('movies/collected/weekly', params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)
    return  result, pages

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_related_movies_paginated(imdb_id, page):
    return call_trakt('movies/%s/related' % imdb_id, params={'extended': 'full', 'limit': '20'}, pagination=True, page=page, with_auth=False)

@plugin.cached(TTL=60, cache='Trakt')
def trakt_get_liked_lists(page=1):
    result, pages = call_trakt('users/likes/lists', params={'limit': '20'}, pagination=True, page=page)
    return result, pages

@plugin.cached(TTL=60, cache='Trakt')
def get_list(user, slug):
    return call_trakt('users/%s/lists/%s/items' % (user, slug), params={'extended': 'full'}, pagination=False)
    
@plugin.cached(TTL=60*24, cache='Trakt')
def trakt_get_genres(type):
    return call_trakt('genres/%s' % type)

@plugin.cached(TTL=60, cache='Trakt')
def get_show(id):
    return call_trakt('shows/%s' % id, params={'extended': 'full'})

def get_latest_episode(id):
    return call_trakt('shows/%s/last_episode' % id, params={'extended': 'full'})

@plugin.cached(TTL=60, cache='Trakt')
def get_season(id,season_number):
    seasons = call_trakt('shows/%s/seasons' % id, params={'extended': 'full'})
    for season in seasons:
        if season['number'] == season_number: return season

@plugin.cached(TTL=60, cache='Trakt')
def get_seasons(id):
    seasons = call_trakt('shows/%s/seasons' % id, params={'extended': 'full'})
    return seasons

@plugin.cached(TTL=60, cache='Trakt')
def get_episode(id, season, episode):
    return call_trakt('shows/%s/seasons/%s/episodes/%s' % (id, season, episode), params={'extended': 'full'})

@plugin.cached(TTL=60, cache='Trakt')
def get_movie(id):
    return call_trakt('movies/%s' % id, params={'extended': 'full'})

@plugin.cached(TTL=60, cache='Trakt')
def search_for_list(list_name, page):
    results, pages = call_trakt('search', params={'type': 'list', 'query': list_name, 'limit': '20'}, pagination=True, page=page)
    return results, pages

@plugin.cached(TTL=60, cache='Trakt')
def search_for_movie(movie_title, page):
    results = call_trakt('search', params={'type': 'movie', 'query': movie_title})
    return results

@plugin.cached(TTL=60, cache='Trakt')
def search_for_movie_paginated(movie_title, page):
    results, pages = call_trakt('search', params={'type': 'movie', 'query': movie_title, 'limit': '20'}, pagination=True, page=page)
    return results, pages

@plugin.cached(TTL=60, cache='Trakt')
def search_for_tvshow_paginated(show_name, page):
    results, pages = call_trakt('search', params={'type': 'show', 'query': show_name, 'limit': '20'}, pagination=True, page=page)
    return results, pages