# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import os
import requests
from sys import argv
import time
from apis import simplejson as json
from myaccounts.modules.trakt import Trakt
from caches import trakt_cache
from caches.fen_cache import cache_object
from modules.nav_utils import notification
from modules.utils import to_utf8
from modules.utils import local_string as ls
from modules.settings_reader import get_setting, set_setting
from modules import settings
# from modules.utils import logger

ma_trakt = Trakt()

dialog = xbmcgui.Dialog()
monitor = xbmc.Monitor()

icon_directory = settings.get_theme()
trakt_icon = os.path.join(icon_directory, 'trakt.png')

window = xbmcgui.Window(10000)

trakt_str = ls(32037)

API_ENDPOINT = "https://api-v2launch.trakt.tv"

CLIENT_ID = ma_trakt.client_id

def call_trakt(path, params={}, data=None, is_delete=False, with_auth=True, method=None, pagination=False, page=1, suppress_error_notification=False):
	def error_notification(line1, error):
		if suppress_error_notification: return
		from modules.nav_utils import notification
		return notification('%s: %s' % (line1, error[0:50]), 3000, trakt_icon)
	def send_query():
		resp = None
		if with_auth:
			try:
				expires_at = get_setting('trakt_expires_at')
				if time.time() > expires_at:
					trakt_refresh_token()
			except: pass
			token = get_setting('trakt_access_token')
			if token:
				headers['Authorization'] = 'Bearer ' + token
		try:
			if method:
				if method == 'post':
					resp = requests.post("{0}/{1}".format(API_ENDPOINT, path), headers=headers, timeout=timeout)
				elif method == 'delete':
					resp = requests.delete("{0}/{1}".format(API_ENDPOINT, path), headers=headers, timeout=timeout)
				elif method == 'sort_by_headers':
					resp = requests.get("{0}/{1}".format(API_ENDPOINT, path), params, headers=headers, timeout=timeout)
			elif data is not None:
				assert not params
				resp = requests.post("{0}/{1}".format(API_ENDPOINT, path), json=data, headers=headers, timeout=timeout)
			elif is_delete:
				resp = requests.delete("{0}/{1}".format(API_ENDPOINT, path), headers=headers, timeout=timeout)
			else:
				resp = requests.get("{0}/{1}".format(API_ENDPOINT, path), params, headers=headers, timeout=timeout)
			resp.raise_for_status()
		except requests.exceptions.RequestException as e:
			return error_notification('Trakt Error', str(e))
		except Exception as e:
			return error_notification('', str(e))
		return resp
	params = dict([(k, to_utf8(v)) for k, v in params.items() if v])
	timeout = 15.0
	numpages = 0
	headers = {'Content-Type': 'application/json', 'trakt-api-version': '2', 'trakt-api-key': CLIENT_ID}
	if pagination: params['page'] = page
	response = send_query()
	response.raise_for_status()
	if response.status_code == 401:
		if xbmc.Player().isPlaying() == False:
			if with_auth and dialog.yesno("%s %s" % (ls(32057), trakt_str), ls(32741)) and trakt_authenticate():
				response = send_query()
			else: pass
		else: return
	if response.status_code == 429:
		headers = response.headers
		if 'Retry-After' in headers:
			time.sleep(headers['Retry-After'])
			response = send_query()
	response.encoding = 'utf-8'
	try: result = response.json()
	except: result = None
	if method == 'sort_by_headers':
		headers = response.headers
		if 'X-Sort-By' in headers and 'X-Sort-How' in headers:
			from modules.utils import sort_list
			ignore_articles = settings.ignore_articles()
			result = sort_list(headers['X-Sort-By'], headers['X-Sort-How'], result, ignore_articles)
	if pagination: numpages = response.headers["X-Pagination-Page-Count"]
	return (result, numpages) if pagination else result

def trakt_refresh_token():
	import myaccounts
	from modules.nav_utils import sync_MyAccounts
	myaccounts.traktRefreshToken()
	sync_MyAccounts(silent=True)

def trakt_authenticate():
	from modules.nav_utils import sync_MyAccounts
	success = ma_trakt.auth()
	sync_MyAccounts()
	return success

def trakt_movies_search(query, page_no, letter):
	from modules.nav_utils import paginate_list
	from modules.history import add_to_search_history
	add_to_search_history(query, 'movie_queries')
	string = "%s_%s_%s" % ('trakt_movies_search', query, page_no)
	url = {'path': "search/movie?query=%s", "path_insert": query, "params": {'limit': 200}, "page": page_no}
	original_list = cache_object(get_trakt, string, url, False)
	limit = 20
	final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	return final_list, total_pages

def trakt_movies_trending(page_no):
	string = "%s_%s" % ('trakt_movies_trending', page_no)
	url = {'path': "movies/trending/%s", "params": {'limit': 20}, "page": page_no}
	return cache_object(get_trakt, string, url, False)

def trakt_movies_anticipated(page_no):
	string = "%s_%s" % ('trakt_movies_anticipated', page_no)
	url = {'path': "movies/anticipated/%s", "params": {'limit': 20}, "page": page_no}
	return cache_object(get_trakt, string, url, False)

def trakt_movies_top10_boxoffice(page_no):
	string = "%s" % 'trakt_movies_top10_boxoffice'
	url = {'path': "movies/boxoffice/%s", 'pagination': False}
	return cache_object(get_trakt, string, url, False)

def trakt_movies_mosts(period, duration, page_no):
	string = "%s_%s_%s_%s" % ('trakt_movies_mosts', period, duration, page_no)
	url = {'path': "movies/%s/%s", "path_insert": (period, duration), "params": {'limit': 20}, "page": page_no}
	return cache_object(get_trakt, string, url, False)

def trakt_movies_related(imdb_id, page_no, letter='None'):
	from modules.nav_utils import paginate_list
	limit = 20
	string = "%s_%s" % ('trakt_movies_related', imdb_id)
	url = {'path': "movies/%s/related", "path_insert": imdb_id, "params": {'limit': 100}}
	original_list = cache_object(get_trakt, string, url, False)
	paginated_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	return paginated_list, total_pages

def trakt_recommendations(db_type):
	limit = settings.page_limit() * 2
	return to_utf8(call_trakt("/recommendations/{0}".format(db_type), params={'limit': limit}))

def trakt_tv_search(query, page_no, letter):
	from modules.nav_utils import paginate_list
	from modules.history import add_to_search_history
	add_to_search_history(query, 'tvshow_queries')
	string = "%s_%s_%s" % ('trakt_tv_search', query, page_no)
	url = {'path': "search/show?query=%s", "path_insert": query, "params": {'limit': 200}, "page": page_no}
	original_list = cache_object(get_trakt, string, url, False)
	limit = 20
	final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	return final_list, total_pages

def trakt_tv_trending(page_no):
	string = "%s_%s" % ('trakt_tv_trending', page_no)
	url = {'path': "shows/trending/%s", "params": {'limit': 20}, "page": page_no}
	return cache_object(get_trakt, string, url, False)

def trakt_tv_anticipated(page_no):
	string = "%s_%s" % ('trakt_tv_anticipated', page_no)
	url = {'path': "shows/anticipated/%s", "params": {'limit': 20}, "page": page_no}
	return cache_object(get_trakt, string, url, False)

def trakt_tv_certifications(certification, page_no):
	string = "%s_%s_%s" % ('trakt_tv_certifications', certification, page_no)
	url = {'path': "shows/collected/all?certifications=%s", "path_insert": certification, "params": {'limit': 20}, "page": page_no}
	return cache_object(get_trakt, string, url, False)

def trakt_tv_mosts(period, duration, page_no):
	string = "%s_%s_%s_%s" % ('trakt_tv_mosts', period, duration, page_no)
	url = {'path': "shows/%s/%s", "path_insert": (period, duration), "params": {'limit': 20}, "page": page_no}
	return cache_object(get_trakt, string, url, False)

def trakt_tv_related(imdb_id, page_no, letter='None'):
	from modules.nav_utils import paginate_list
	limit = 20
	string = "%s_%s" % ('trakt_tv_related', imdb_id)
	url = {'path': "shows/%s/related", "path_insert": imdb_id, "params": {'limit': 100}}
	from modules.nav_utils import paginate_list
	original_list = cache_object(get_trakt, string, url, False)
	paginated_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	return paginated_list, total_pages

def trakt_get_hidden_items(list_type):
	string = 'trakt_hidden_items_%s' % list_type
	url = {'path': "users/hidden/%s", "path_insert": list_type, "params": {'limit': 1000, "type": "show"}, "with_auth": True, "pagination": False}
	return trakt_cache.cache_trakt_object(get_trakt, string, url)

def trakt_watched_unwatched(action, media, media_id, tvdb_id=0, season=None, episode=None, key=None):
	url = "sync/history" if action == 'mark_as_watched' else "sync/history/remove"
	if not key: key = "imdb"
	if media == 'movies': data = {"movies": [{"ids": {"tmdb": media_id}}]}
	elif media == 'episode': data = {"shows": [{"seasons": [{"episodes": [{"number": int(episode)}], "number": int(season)}], "ids": {key: media_id}}]}
	elif media =='shows': data = {"shows": [{"ids": {key: media_id}}]}
	elif media == 'season': data = {"shows": [{"ids": {key: media_id}, "seasons": [{"number": int(season)}]}]}
	result = call_trakt(url, data=data)
	if not media == 'movies':
		if tvdb_id == 0: return
		result_key = 'added' if action == 'mark_as_watched' else 'deleted'
		if not result[result_key]['episodes'] > 0:
			trakt_watched_unwatched(action, media, tvdb_id, tvdb_id, season, episode, key="tvdb")

def trakt_collection_widgets(db_type, param1, param2):
	# param1 = the type of list to be returned (from 'new_page' param), param2 is currently not used
	try: limit = int(get_setting('trakt_widget_limit'))
	except: limit = 20
	string_insert = 'movie' if db_type in ('movie', 'movies') else 'tvshow'
	window_property_name = 'fen_trakt_collection_%s' % string_insert
	try: data = json.loads(window.getProperty(window_property_name))
	except: data = trakt_fetch_collection_watchlist('collection', db_type)
	if param1 == 'recent':
		data = sorted(data, key=lambda k: k['collected_at'], reverse=True)
	elif param1 == 'random':
		import random
		random.shuffle(data)
	data = data[:limit]
	for item in data:
		item['media_id'] = get_trakt_movie_id(item['media_ids']) if db_type == 'movies' else get_trakt_tvshow_id(item['media_ids'])
	return data, 1

def trakt_collection(db_type, page_no, letter):
	string_insert = 'movie' if db_type in ('movie', 'movies') else 'tvshow'
	original_list = trakt_fetch_collection_watchlist('collection', db_type)
	if settings.paginate():
		from modules.nav_utils import paginate_list
		limit = settings.page_limit()
		final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	else: final_list, total_pages = original_list, 1
	for item in final_list:
		item['media_id'] = get_trakt_movie_id(item['media_ids']) if db_type == 'movies' else get_trakt_tvshow_id(item['media_ids'])
	return final_list, total_pages

def trakt_watchlist(db_type, page_no, letter):
	string_insert = 'movie' if db_type in ('movie', 'movies') else 'tvshow'
	original_list = trakt_fetch_collection_watchlist('watchlist', db_type)
	if settings.paginate():
		from modules.nav_utils import paginate_list
		limit = settings.page_limit()
		final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	else: final_list, total_pages = original_list, 1
	for item in final_list:
		item['media_id'] = get_trakt_movie_id(item['media_ids']) if db_type == 'movies' else get_trakt_tvshow_id(item['media_ids'])
	return final_list, total_pages

def trakt_fetch_collection_watchlist(list_type, db_type):
	from modules.utils import title_key
	from modules.settings import ignore_articles as ignore
	ignore_articles = ignore()
	key, string_insert = ('movie', 'movie') if db_type in ('movie', 'movies') else ('show', 'tvshow')
	collected_at = 'collected_at' if db_type in ('movie', 'movies') else 'last_collected_at'
	string = "trakt_%s_%s" % (list_type, string_insert)
	path = "sync/%s/" % list_type
	url = {"path": path + "%s", "path_insert": db_type, "with_auth": True, "pagination": False}
	data = trakt_cache.cache_trakt_object(get_trakt, string, url)
	if list_type == 'watchlist': data = [i for i in data if i['type'] == key]
	result = [{'media_ids': i[key]['ids'], 'title': i[key]['title'], 'collected_at': i.get(collected_at)} for i in data]
	result = sorted(result, key=lambda k: title_key(k['title'], ignore_articles))
	return result

def add_to_list(user, slug, data):
	result = call_trakt("/users/{0}/lists/{1}/items".format(user, slug), data = data)
	if result['added']['shows'] > 0 or result['added']['movies'] > 0:
		notification(ls(32576), 3000)
	else: notification(ls(32574), 3000)
	return result

def remove_from_list(user, slug, data):
	result = call_trakt("/users/{0}/lists/{1}/items/remove".format(user, slug), data=data)
	if result['deleted']['shows'] > 0 or result['deleted']['movies'] > 0:
		notification(ls(32576), 3000)
		xbmc.executebuiltin("Container.Refresh")
	else: notification(ls(32574), 3000)
	return result

def add_to_watchlist(data):
	result = call_trakt("/sync/watchlist", data=data)
	if result['added']['movies'] > 0: db_type = 'movie'
	elif result['added']['shows'] > 0: db_type = 'tvshow'
	else: return notification(ls(32574), 3000)
	trakt_cache.clear_trakt_collection_watchlist_data('watchlist', db_type)
	notification(ls(32576), 6000)
	return result

def remove_from_watchlist(data):
	result = call_trakt("/sync/watchlist/remove", data=data)
	if result['deleted']['movies'] > 0: db_type = 'movie'
	elif result['deleted']['shows'] > 0: db_type = 'tvshow'
	else: return notification(ls(32574), 3000)
	trakt_cache.clear_trakt_collection_watchlist_data('watchlist', db_type)
	notification(ls(32576), 3000)
	xbmc.executebuiltin("Container.Refresh")
	return result

def add_to_collection(data):
	result = call_trakt("/sync/collection", data=data)
	if result['added']['movies'] > 0: db_type = 'movie'
	elif result['added']['episodes'] > 0: db_type = 'tvshow'
	else: return notification(ls(32574), 3000)
	trakt_cache.clear_trakt_collection_watchlist_data('collection', db_type)
	notification(ls(32576), 6000)
	return result

def remove_from_collection(data):
	result = call_trakt("/sync/collection/remove", data=data)
	if result['deleted']['movies'] > 0: db_type = 'movie'
	elif result['deleted']['episodes'] > 0: db_type = 'tvshow'
	else: return notification(ls(32574), 3000)
	trakt_cache.clear_trakt_collection_watchlist_data('collection', db_type)
	notification(ls(32576), 3000)
	xbmc.executebuiltin("Container.Refresh")
	return result
	
def trakt_get_next_episodes(include_hidden=False, hidden_full_info=False):
	def _process():
		for item in result:
			max_season_item = max(item['seasons'], key=lambda x: x['number'])
			season = max_season_item['number']
			max_episode_item = max(max_season_item['episodes'], key=lambda x: x['number'])
			episode = max_episode_item['number']
			last_played = max_episode_item['last_watched_at']
			tvdb_id = item['show']['ids']['tvdb']
			tmdb_id = get_trakt_tvshow_id(item['show']['ids'])
			yield {"tmdb_id": tmdb_id, "tvdb_id": tvdb_id, "season": season, "episode": episode, "last_played": last_played}
	result = trakt_tv_watched_raw()
	try: hidden_data = trakt_get_hidden_items("progress_watched")
	except: hidden_data = []
	if include_hidden:
		ep_list = list(_process())
		if hidden_full_info:
			return ep_list
		all_shows = [i['tmdb_id'] for i in ep_list]
		hidden_shows = [get_trakt_tvshow_id(i['show']['ids']) for i in hidden_data]
		return all_shows, hidden_shows
	hidden_shows = [i['show']['ids']['tvdb'] for i in hidden_data]
	result = [i for i in result if not i['show']['ids']['tvdb'] in hidden_shows]
	ep_list = list(_process())
	return ep_list

def hide_unhide_trakt_items(action, db_type, media_id, list_type):
	db_type = 'movies' if db_type in ['movie', 'movies'] else 'shows'
	key = 'tmdb' if db_type == 'movies' else 'imdb'
	url = "users/hidden/{}".format(list_type) if action == 'hide' else "users/hidden/{}/remove".format(list_type)
	data = {db_type: [{'ids': {key: media_id}}]}
	call_trakt(url, data=data)
	trakt_cache.clear_trakt_hidden_data(list_type)
	xbmc.executebuiltin("Container.Refresh")

def hide_recommendations(params):
	db_type = params.get('db_type')
	imdb_id = params.get('imdb_id')
	result = call_trakt("/recommendations/{0}/{1}".format(db_type, imdb_id), method='delete')
	notification(ls(32576), 3000)
	xbmc.sleep(500)
	xbmc.executebuiltin("Container.Refresh")
	return result

def make_new_trakt_list(params):
	import urllib
	mode = params['mode']
	list_title = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM)
	if not list_title: return
	list_name = urllib.unquote(list_title)
	data = {'name': list_name, 'privacy': 'private', 'allow_comments': False}
	call_trakt("users/me/lists", data=data)
	trakt_cache.clear_trakt_list_data('my_lists')
	notification(ls(32576), 3000)
	xbmc.executebuiltin("Container.Refresh")

def delete_trakt_list(params):
	user = params['user']
	list_slug = params['list_slug']
	confirm = dialog.yesno('Fen', ls(32580))
	if confirm == True:
		url = "users/{0}/lists/{1}".format(user, list_slug)
		call_trakt(url, is_delete=True)
		trakt_cache.clear_trakt_list_data('my_lists')
		notification(ls(32576), 3000)
		xbmc.executebuiltin("Container.Refresh")
	else: return

def trakt_add_to_list(params):
	from indexers.trakt_lists import get_trakt_list_selection
	tmdb_id = params['tmdb_id']
	tvdb_id = params['tvdb_id']
	imdb_id = params['imdb_id']
	db_type = params['db_type']
	if db_type == 'movie':
		key, media_key, media_id = ('movies', 'tmdb', int(tmdb_id))
	else:
		key = 'shows'
		media_ids = [(imdb_id, 'imdb'), (tvdb_id, 'tvdb'), (tmdb_id, 'tmdb')]
		media_id, media_key = next(item for item in media_ids if item[0] != 'None')
		if media_id in (tmdb_id, tvdb_id):
			media_id = int(media_id)
	selected = get_trakt_list_selection()
	if selected is not None:
		data = {key: [{"ids": {media_key: media_id}}]}
		if selected['user'] == 'Watchlist':
			add_to_watchlist(data)
		elif selected['user'] == 'Collection':
			add_to_collection(data)
		else:
			user = selected['user']
			slug = selected['slug']
			add_to_list(user, slug, data)
			trakt_cache.clear_trakt_list_contents_data(user=user, list_slug=slug)

def trakt_remove_from_list(params):
	from indexers.trakt_lists import get_trakt_list_selection
	tmdb_id = params['tmdb_id']
	tvdb_id = params['tvdb_id']
	imdb_id = params['imdb_id']
	db_type = params['db_type']
	if db_type == 'movie':
		key, media_key, media_id = ('movies', 'tmdb', int(tmdb_id))
	else:
		key = 'shows'
		media_ids = [(imdb_id, 'imdb'), (tvdb_id, 'tvdb'), (tmdb_id, 'tmdb')]
		media_id, media_key = next(item for item in media_ids if item[0] != 'None')
		if media_id in (tmdb_id, tvdb_id):
			media_id = int(media_id)
	selected = get_trakt_list_selection()
	if selected is not None:
		data = {key: [{"ids": {media_key: media_id}}]}
		if selected['user'] == 'Watchlist':
			remove_from_watchlist(data)
		elif selected['user'] == 'Collection':
			remove_from_collection(data)
		else:
			user = selected['user']
			slug = selected['slug']
			remove_from_list(user, slug, data)
			trakt_cache.clear_trakt_list_contents_data(user=user, list_slug=slug)

def trakt_like_a_list(params):
	user = params['user']
	list_slug = params['list_slug']
	try:
		call_trakt("/users/{0}/lists/{1}/like".format(user, list_slug), method='post')
		trakt_cache.clear_trakt_list_data('liked_lists')
		notification(ls(32576), 3000)
	except: notification(ls(32574), 3000)

def trakt_unlike_a_list(params):
	user = params['user']
	list_slug = params['list_slug']
	try:
		call_trakt("/users/{0}/lists/{1}/like".format(user, list_slug), method='delete')
		trakt_cache.clear_trakt_list_data('liked_lists')
		notification(ls(32576), 3000)
		xbmc.executebuiltin("Container.Refresh")
	except: notification(ls(32574), 3000)

def get_trakt_movie_id(item):
	if item['tmdb']: return item['tmdb']
	from tikimeta import movie_meta_external_id
	tmdb_id = None
	if item['imdb']:
		try:
			meta = movie_meta_external_id('imdb_id', item['imdb'])
			tmdb_id = meta['id']
		except: pass
	return tmdb_id

def get_trakt_tvshow_id(item):
	if item['tmdb']: return item['tmdb']
	from tikimeta import tvshow_meta_external_id
	tmdb_id = None
	if item['imdb']:
		try: 
			meta = tvshow_meta_external_id('imdb_id', item['imdb'])
			tmdb_id = meta['id']
		except: tmdb_id = None
	if not tmdb_id:
		if item['tvdb']:
			try: 
				meta = tvshow_meta_external_id('tvdb_id', item['tvdb'])
				tmdb_id = meta['id']
			except: tmdb_id = None
	return tmdb_id

def trakt_indicators_movies():
	def _process(url):
		result = get_trakt(url)
		for i in result: i.update({'tmdb_id': get_trakt_movie_id(i['movie']['ids'])})
		result = [(i['tmdb_id'], i['movie']['title'], i['last_watched_at']) for i in result if i['tmdb_id'] != None]
		return result
	url = {'path': "sync/watched/movies%s", "with_auth": True, "pagination": False}
	result = trakt_cache.cache_trakt_object(_process, 'trakt_indicators_movies', url)
	return result

def trakt_indicators_tv():
	def _process(dummy_arg):
		result = trakt_tv_watched_raw()
		for i in result: i.update({'tmdb_id': get_trakt_tvshow_id(i['show']['ids'])})
		result = [(i['tmdb_id'], i['show']['aired_episodes'], sum([[(s['number'], e['number']) for e in s['episodes']] for s in i['seasons']], []), i['show']['title'], i['last_watched_at']) for i in result if i['tmdb_id'] != None]
		result = [(int(i[0]), int(i[1]), i[2], i[3], i[4]) for i in result]
		return result
	result = trakt_cache.cache_trakt_object(_process, 'trakt_indicators_tv', '')
	return result

def trakt_tv_watched_raw():
	url = {'path': "users/me/watched/shows?extended=full%s", "with_auth": True, "pagination": False}
	return trakt_cache.cache_trakt_object(get_trakt, 'trakt_tv_watched_raw', url)

def trakt_official_status(db_type):
	if not settings.addon_installed('script.trakt'): return True
	trakt_addon = settings.ext_addon('script.trakt')
	try: authorization = trakt_addon.getSetting('authorization')
	except: authorization = ''
	if authorization == '': return True
	try: exclude_http = trakt_addon.getSetting('ExcludeHTTP')
	except: exclude_http = ''
	if exclude_http in ('true', ''): return True
	media_setting = 'scrobble_movie' if db_type in ('movie', 'movies') else 'scrobble_episode'
	try: scrobble = trakt_addon.getSetting(media_setting)
	except: scrobble = ''
	if scrobble in ('false', ''): return True
	return False

def get_trakt(url):
	result = call_trakt(url['path'] % url.get('path_insert', ''), params=url.get('params', {}), data=url.get('data'), is_delete=url.get('is_delete', False), with_auth=url.get('with_auth', False), method=url.get('method'), pagination=url.get('pagination', True), page=url.get('page'))
	return result[0] if url.get('pagination', True) else result

def make_trakt_slug(name):
	import re
	name = name.strip()
	name = name.lower()
	name = re.sub('[^a-z0-9_]', '-', name)
	name = re.sub('--+', '-', name)
	return name

def sync_watched_trakt_to_fen(dialog=False):
	from datetime import datetime
	from modules.utils import clean_file_name
	try: from sqlite3 import dbapi2 as database
	except ImportError: from pysqlite2 import dbapi2 as database
	processed_trakt_tv = []
	compare_trakt_tv = []
	try:
		if dialog:
			bg_dialog = xbmcgui.DialogProgressBG()
			bg_dialog.create(ls(32967), ls(32577))
		WATCHED_DB = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/watched_status.db')
		settings.check_database(WATCHED_DB)
		dbcon = database.connect(WATCHED_DB)
		dbcur = dbcon.cursor()
		trakt_watched_movies = trakt_indicators_movies()
		trakt_watched_tv = trakt_indicators_tv()
		process_movies = False
		process_tvshows = False
		dbcur.execute("SELECT media_id FROM watched_status WHERE db_type = ?", ('movie',))
		fen_watched_movies = dbcur.fetchall()
		fen_watched_movies = [int(i[0]) for i in fen_watched_movies]
		compare_trakt_movies = [i[0] for i in trakt_watched_movies]
		process_trakt_movies = trakt_watched_movies
		if not sorted(fen_watched_movies) == sorted(compare_trakt_movies): process_movies = True
		if dialog: bg_dialog.update(50, ls(32967), ls(32968) % ls(32028))
		xbmc.sleep(100)
		dbcur.execute("SELECT media_id, season, episode FROM watched_status WHERE db_type = ?", ('episode',))
		fen_watched_episodes = dbcur.fetchall()
		fen_watched_episodes = [(int(i[0]), i[1], i[2]) for i in fen_watched_episodes]
		for i in trakt_watched_tv:
			for x in i[2]:
				compare_trakt_tv.append((i[0], x[0], x[1]))
				processed_trakt_tv.append((i[0], x[0], x[1], i[3]))
		if not sorted(fen_watched_episodes) == sorted(compare_trakt_tv): process_tvshows = True
		if dialog: bg_dialog.update(100, ls(32967), ls(32968) % ls(32506))
		xbmc.sleep(100)
		if not process_movies and not process_tvshows and dialog:
			bg_dialog.close()
		if process_movies:
			dbcur.execute("DELETE FROM watched_status WHERE db_type=?", ('movie',))
			for count, i in enumerate(process_trakt_movies):
				try:
					if dialog: bg_dialog.update(int(float(count) / float(len(trakt_watched_movies)) * 100), ls(32967), ls(32969) % ls(32028))
					last_played = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					dbcur.execute("INSERT OR IGNORE INTO watched_status VALUES (?, ?, ?, ?, ?, ?)", ('movie', str(i[0]), '', '', last_played, clean_file_name(to_utf8(i[1]))))
				except: pass
		if process_tvshows:
			dbcur.execute("DELETE FROM watched_status WHERE db_type=?", ('episode',))
			for count, i in enumerate(processed_trakt_tv):
				try:
					if dialog: bg_dialog.update(int(float(count) / float(len(processed_trakt_tv)) * 100), ls(32967), ls(32969) % ls(32506))
					last_played = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					dbcur.execute("INSERT OR IGNORE INTO watched_status VALUES (?, ?, ?, ?, ?, ?)", ('episode', str(i[0]), i[1], i[2], last_played, clean_file_name(to_utf8(i[3]))))
				except: pass
		if process_movies or process_tvshows:
			dbcon.commit()
		if dialog:
			bg_dialog.close()
			from modules.nav_utils import notification
			notification(ls(32576), time=4000)
		window.setProperty('fen_trakt_sync_complete', 'true')
		set_setting('trakt_indicators_active', 'true')
	except:
		if dialog:
			try: bg_dialog.close()
			except: pass
		from modules.nav_utils import notification
		notification(ls(32574), time=3500)
		pass

