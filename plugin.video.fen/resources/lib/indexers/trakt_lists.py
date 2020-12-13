# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import os
import json
from sys import argv
from apis.trakt_api import get_trakt 
from modules.nav_utils import build_url, setView, add_dir
from modules.settings_reader import get_setting
from modules.utils import local_string as ls
from modules import settings
# from modules.utils import logger

dialog = xbmcgui.Dialog()
icon_directory = settings.get_theme()
trakt_icon = os.path.join(icon_directory, 'trakt.png')
fanart = os.path.join(xbmc.translatePath('special://home/addons/plugin.video.fen'), "fanart.png")

def search_trakt_lists(params):
	from apis.trakt_api import call_trakt
	__handle__ = int(argv[1])
	mode = params.get('mode')
	page = params.get('new_page') if 'new_page' in params else '1'
	search_title = params.get('search_title') if 'search_title' in params else dialog.input("Fen", type=xbmcgui.INPUT_ALPHANUM)
	if not search_title: return
	lists, pages = call_trakt("search", params={'type': 'list', 'fields': 'name, description', 'query': search_title, 'limit': 50}, pagination=True, page=page)
	for count, item in enumerate(lists, 1):
		try:
			list_info = item["list"]
			name = list_info["name"]
			user = list_info["username"]
			slug = list_info["ids"]["slug"]
			item_count = list_info["item_count"]
			if list_info['privacy'] == 'private' or item_count == 0: continue
			cm = []
			url_params = {'mode': 'trakt.list.build_trakt_list', 'user': user, 'slug': slug}
			trakt_selection_url = {'mode': 'navigator.adjust_main_lists', 'method': 'add_trakt_external', 'name': name, 'user': user, 'slug': slug}
			trakt_folder_selection_url = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'add_trakt_external', 'name': name, 'user': user, 'slug': slug}
			like_list_url = {'mode': 'trakt.trakt_like_a_list', 'user': user, 'list_slug': slug}
			unlike_list_url = {'mode': 'trakt.trakt_unlike_a_list', 'user': user, 'list_slug': slug}
			url = build_url(url_params)
			cm.append((ls(32730),'RunPlugin(%s)' % build_url(trakt_selection_url)))
			cm.append((ls(32731),'RunPlugin(%s)' % build_url(trakt_folder_selection_url)))
			cm.append((ls(32776),'RunPlugin(%s)' % build_url(like_list_url)))
			cm.append((ls(32783),'RunPlugin(%s)' % build_url(unlike_list_url)))
			display = '%s | [B]%s[/B] | [I]%s (x%s)[/I]' % (count, name.upper(), user, str(item_count))
			listitem = xbmcgui.ListItem(display)
			listitem.setArt({'icon': trakt_icon, 'poster': trakt_icon, 'thumb': trakt_icon, 'fanart': fanart, 'banner': trakt_icon})
			listitem.addContextMenuItems(cm)
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
		except: pass
	if pages > page:
		new_page = int(page) + 1
		add_dir({'mode': mode, 'search_title': search_title, 'new_page': str(new_page),
			'foldername': mode}, ls(32799), iconImage='item_next.png')
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.main')

def get_trakt_list_selection(list_choice='none'):
	my_lists = sorted([{'name': item["name"], 'display': ls(32778) % item["name"].upper(), 'user': item["user"]["ids"]["slug"], 'slug': item["ids"]["slug"]} for item in get_trakt_lists({'list_type': 'my_lists', 'build_list': 'false'})], key=lambda k: k['name'])
	if list_choice == 'nav_edit':
		liked_lists = sorted([{'name': item["list"]["name"], 'display': ls(32779) % item["list"]["name"].upper(), 'user': item["list"]["user"]["ids"]["slug"], 'slug': item["list"]["ids"]["slug"]} for item in get_trakt_lists({'list_type': 'liked_lists', 'build_list': 'false'})], key=lambda k: (k['display']))
		my_lists.extend(liked_lists)
	if not list_choice == 'nav_edit':
		my_lists.insert(0, {'name': 'Collection', 'display': '[B][I]%s [/I][/B]' % ls(32499).upper(), 'user': 'Collection', 'slug': 'Collection'})
		my_lists.insert(0, {'name': 'Watchlist', 'display': '[B][I]%s [/I][/B]' % ls(32500).upper(),  'user': 'Watchlist', 'slug': 'Watchlist'})
	selection = dialog.select("Select list", [l["display"] for l in my_lists])
	if selection >= 0: return my_lists[selection]
	else: return None

def get_trakt_lists(params):
	from caches.trakt_cache import cache_trakt_object
	def _process_my_lists():
		for item in lists:
			try:
				cm = []
				name = item["name"]
				user = item["user"]["ids"]["slug"]
				slug = item["ids"]["slug"]
				item_count = item.get('item_count', None)
				if item_count: display_name = '%s (x%s)' % (name, item_count)
				else: display_name = name
				url_params = {'mode': 'trakt.list.build_trakt_list', 'user': user, 'slug': slug}
				trakt_selection_url = {'mode': 'navigator.adjust_main_lists', 'method': 'add_trakt_external', 'name': name, 'user': user, 'slug': slug}
				trakt_folder_selection_url = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'add_trakt_external', 'name': name, 'user': user, 'slug': slug}
				make_new_list_url = {'mode': 'trakt.make_new_trakt_list'}
				delete_list_url = {'mode': 'trakt.delete_trakt_list', 'user': user, 'list_slug': slug}
				url = build_url(url_params)
				cm.append((ls(32730),'RunPlugin(%s)' % build_url(trakt_selection_url)))
				cm.append((ls(32731),'RunPlugin(%s)' % build_url(trakt_folder_selection_url)))
				cm.append((ls(32780),'RunPlugin(%s)' % build_url(make_new_list_url)))
				cm.append((ls(32781),'RunPlugin(%s)' % build_url(delete_list_url)))
				try: listitem = xbmcgui.ListItem(display_name, offscreen=True)
				except: listitem = xbmcgui.ListItem(display_name)
				listitem.setArt({'icon': trakt_icon, 'poster': trakt_icon, 'thumb': trakt_icon, 'fanart': fanart, 'banner': trakt_icon})
				listitem.addContextMenuItems(cm)
				yield (url, listitem, True)
			except: pass
	def _process_liked_lists():
		for item in lists:
			try:
				cm = []
				_item = item['list']
				name = _item["name"]
				user = _item["user"]["ids"]["slug"]
				slug = _item["ids"]["slug"]
				item_count = _item.get('item_count', None)
				if item_count: display_name = '%s (x%s) - [I]%s[/I]' % (name, item_count, user)
				else: display_name = '%s - [I]%s[/I]' % (name, user)
				url_params = {'mode': 'trakt.list.build_trakt_list', 'user': user, 'slug': slug}
				trakt_selection_url = {'mode': 'navigator.adjust_main_lists', 'method': 'add_trakt_external', 'name': name, 'user': user, 'slug': slug}
				trakt_folder_selection_url = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'add_trakt_external', 'name': name, 'user': user, 'slug': slug}
				unlike_list_url = {'mode': 'trakt.trakt_unlike_a_list', 'user': user, 'list_slug': slug}
				url = build_url(url_params)
				try: listitem = xbmcgui.ListItem(display_name, offscreen=True)
				except: listitem = xbmcgui.ListItem(display_name)
				listitem.setArt({'icon': trakt_icon, 'poster': trakt_icon, 'thumb': trakt_icon, 'fanart': fanart, 'banner': trakt_icon})
				cm.append((ls(32730),'RunPlugin(%s)' % build_url(trakt_selection_url)))
				cm.append((ls(32731),'RunPlugin(%s)' % build_url(trakt_folder_selection_url)))
				cm.append((ls(32783),'RunPlugin(%s)' % build_url(unlike_list_url)))
				listitem.addContextMenuItems(cm, replaceItems=False)
				yield (url, listitem, True)
			except: pass
	try:
		list_type = params['list_type']
		build_list = params['build_list']
		if list_type == 'my_lists':
			_process = _process_my_lists
			string = "trakt_my_lists"
			path = "users/me/lists%s"
		elif list_type == 'liked_lists':
			_process = _process_liked_lists
			string = "trakt_liked_lists"
			path = "users/likes/lists%s"
		url = {"path": path, "params": {'limit': 1000}, "pagination": False, "with_auth": True}
		lists = cache_trakt_object(get_trakt, string, url)
		if build_list == 'false': return lists
		item_list = list(_process())
		__handle__ = int(argv[1])
		xbmcplugin.addDirectoryItems(__handle__, item_list)
		xbmcplugin.setContent(__handle__, 'files')
		xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
		xbmcplugin.endOfDirectory(__handle__)
		setView('view.main')
	except: pass

def get_trakt_trending_popular_lists(params):
	from caches.fen_cache import cache_object
	__handle__ = int(argv[1])
	try:
		list_type = params['list_type']
		string = "trakt_%s_user_lists" % list_type
		path = "lists/%s/" % list_type
		url = {'path': path + "%s", "params": {'limit': 100}}
		lists = cache_object(get_trakt, string, url, False)
		def _process():
			for item in lists:
				try:
					cm = []
					_item = item['list']
					name = _item["name"]
					user = _item["user"]["ids"]["slug"]
					slug = _item["ids"]["slug"]
					item_count = _item.get('item_count', None)
					if item_count: display_name = '%s (x%s) - [I] %s[/I]' % (name, item_count, user)
					else: display_name = '%s - [I] %s[/I]' % (name, user)
					url_params = {'mode': 'trakt.list.build_trakt_list', 'user': user, 'slug': slug}
					trakt_selection_url = {'mode': 'navigator.adjust_main_lists', 'method': 'add_trakt_external', 'name': name, 'user': user, 'slug': slug}
					trakt_folder_selection_url = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'add_trakt_external', 'name': name, 'user': user, 'slug': slug}
					like_list_url = {'mode': 'trakt.trakt_like_a_list', 'user': user, 'list_slug': slug}
					unlike_list_url = {'mode': 'trakt.trakt_unlike_a_list', 'user': user, 'list_slug': slug}
					url = build_url(url_params)
					try: listitem = xbmcgui.ListItem(display_name, offscreen=True)
					except: listitem = xbmcgui.ListItem(display_name)
					listitem.setArt({'icon': trakt_icon, 'poster': trakt_icon, 'thumb': trakt_icon, 'fanart': fanart, 'banner': trakt_icon})
					cm.append((ls(32730),'RunPlugin(%s)' % build_url(trakt_selection_url)))
					cm.append((ls(32731),'RunPlugin(%s)' % build_url(trakt_folder_selection_url)))
					cm.append((ls(32776),'RunPlugin(%s)' % build_url(like_list_url)))
					cm.append((ls(32783),'RunPlugin(%s)' % build_url(unlike_list_url)))
					listitem.addContextMenuItems(cm)
					yield (url, listitem, True)
				except: pass
		item_list = list(_process())
		xbmcplugin.addDirectoryItems(__handle__, item_list)
		xbmcplugin.setContent(__handle__, 'files')
		xbmcplugin.endOfDirectory(__handle__)
		setView('view.main')
	except: pass

def build_trakt_list(params):
	from indexers.movies import Movies
	from indexers.tvshows import TVShows
	from apis.trakt_api import get_trakt_movie_id, get_trakt_tvshow_id
	def _add_misc_dir(url_params, list_name=ls(32799), iconImage='item_next.png'):
		icon = os.path.join(icon_directory, iconImage)
		listitem = xbmcgui.ListItem(list_name)
		listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': fanart, 'banner': icon})
		if url_params['mode'] == 'build_navigate_to_page':
			listitem.setProperty('SpecialSort', 'top')
			listitem.addContextMenuItems([(ls(32784),"XBMC.RunPlugin(%s)" % build_url({'mode': 'toggle_jump_to'}))])
		else:
			listitem.setProperty('SpecialSort', 'bottom')
		xbmcplugin.addDirectoryItem(handle=__handle__, url=build_url(url_params), listitem=listitem, isFolder=True)
	__handle__ = int(argv[1])
	is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
	user = params.get('user')
	slug = params.get('slug')
	cache_page_string = slug
	letter = params.get('new_letter', 'None')
	page_no = int(params.get('new_page', '1'))
	try:
		original_list = []
		result = get_trakt_list_contents(user, slug)
		for item in result:
			try:
				media_type = item['type']
				if not media_type in ('movie', 'show'): continue
				original_list.append({'media_type': media_type, 'title': item[media_type]['title'], 'media_ids': item[media_type]['ids']})
			except: pass
		if settings.paginate():
			from modules.nav_utils import paginate_list
			limit = settings.page_limit()
			final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
		else:
			final_list, total_pages = original_list, 1
		for item in final_list:
			item['media_id'] = get_trakt_movie_id(item['media_ids']) if item['media_type'] == 'movie' else get_trakt_tvshow_id(item['media_ids'])
		movie_list = [i['media_id'] for i in final_list if i['media_type'] == 'movie']
		show_list = [i['media_id'] for i in final_list if i['media_type'] == 'show']
		content = 'movies' if len(movie_list) > len(show_list) else 'tvshows'
		if total_pages > 2 and not is_widget: _add_misc_dir({'mode': 'build_navigate_to_page', 'db_type': 'Media', 'user': user, 'slug': slug, 'current_page': page_no, 'total_pages': total_pages, 'transfer_mode': 'trakt.list.build_trakt_list'}, 'Jump To...', 'item_jump.png')
		if len(movie_list) >= 1: Movies({'list': movie_list, 'action': slug}).worker()
		if len(show_list) >= 1: TVShows({'list': show_list, 'action': slug}).worker()
		if total_pages > page_no: _add_misc_dir({'mode': 'trakt.list.build_trakt_list', 'user': user, 'slug': slug, 'new_page': str(page_no + 1), 'new_letter': letter})
		xbmcplugin.setContent(__handle__, content)
		xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
		if params.get('refreshed'): xbmc.sleep(1500)
		setView('view.trakt_list', content)
	except:
		from modules.nav_utils import notification
		notification(ls(32574), 3000)

def get_trakt_list_contents(user, slug):
	from caches.trakt_cache import cache_trakt_object
	string = "trakt_list_contents_%s_%s" % (user, slug)
	url = {"path": "users/%s/lists/%s/items", "path_insert": (user, slug), "params": {'extended':'full'}, "with_auth": True, "method": "sort_by_headers"}
	return cache_trakt_object(get_trakt, string, url)

def get_trakt_my_calendar(params):
	from threading import Thread
	from tikimeta import tvshow_meta, retrieve_user_info
	from modules.indicators_bookmarks import get_watched_info_tv
	from indexers.tvshows import build_episode
	from apis.trakt_api import get_trakt_tvshow_id
	from caches.trakt_cache import cache_trakt_object
	def _process(item, order):
		meta = tvshow_meta('tmdb_id', item['tmdb_id'], meta_user_info)
		episode_item = {"season": item['season'], "episode": item['episode'], "meta": meta, "action": "trakt_calendar",
						"include_unaired": True, "first_aired": item['first_aired'], 'trakt_calendar': trakt_calendar,
						"adjust_hours": adjust_hours, "current_adjusted_date": current_adjusted_date, "order": order,
						"watched_indicators": watched_indicators}
		result.append(build_episode(episode_item, watched_info, use_trakt, meta_user_info, meta_user_info_json, is_widget))
	__handle__ = int(argv[1])
	recently_aired = params.get('recently_aired', None)
	if recently_aired:
		trakt_calendar = False
		import datetime
		current_date = settings.adjusted_datetime()
		start = (current_date - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
		finish = 14
	else:
		trakt_calendar = True
		start, finish = settings.trakt_calendar_days()
	threads = []
	result = []
	string = "get_trakt_my_calendar_%s_%s" % (start, str(finish))
	url = {"path": "calendars/my/shows/%s/%s", "path_insert": (start, str(finish)), "with_auth": True, "pagination": False}
	data = cache_trakt_object(get_trakt, string, url, expiration=3)
	data = [{'sort_title': '%s s%s e%s' % (i['show']['title'], str(i['episode']['season']).zfill(2), str(i['episode']['number']).zfill(2)), 'tmdb_id': get_trakt_tvshow_id(i['show']['ids']), 'season': i['episode']['season'], 'episode': i['episode']['number'], 'first_aired': i['first_aired']} for i in data if i['episode']['season'] > 0]
	data = [i for i in data if i['tmdb_id'] != None]
	data = [i for n, i in enumerate(data) if i not in data[n + 1:]] # remove duplicates
	if trakt_calendar:
		data = sorted(data, key=lambda k: k['sort_title'], reverse=False)
	else:
		try: limit = int(get_setting('trakt_widget_limit'))
		except: limit = 20
		data = sorted(data, key=lambda k: k['first_aired'], reverse=True)
		data = data[:limit]
	data = sorted(data, key=lambda k: k['first_aired'], reverse=False)
	watched_info, use_trakt = get_watched_info_tv()
	meta_user_info = retrieve_user_info()
	meta_user_info_json = json.dumps(meta_user_info)
	adjust_hours = int(get_setting('datetime.offset'))
	current_adjusted_date = settings.adjusted_datetime(dt=True)
	is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
	watched_indicators = settings.watched_indicators()
	for count, item in enumerate(data): threads.append(Thread(target=_process, args=(item, count)))
	[i.start() for i in threads]
	[i.join() for i in threads]
	r = [i for i in result if i is not None]
	r = sorted(r, key=lambda k: k['order'], reverse=True)
	item_list = [i['listitem'] for i in r]
	for i in item_list: xbmcplugin.addDirectoryItem(__handle__, i[0], i[1], i[2])
	xbmcplugin.setContent(__handle__, 'episodes')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.episode_lists', 'episodes')
	if settings.calendar_focus_today() and trakt_calendar:
		try: index = max([i for i, x in enumerate([i['label'] for i in r]) if ls(32849).upper() in x])
		except: index = None
		if index:
			from modules.nav_utils import focus_index
			focus_index(index)

