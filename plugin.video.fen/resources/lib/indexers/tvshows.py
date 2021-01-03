# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import os
from sys import argv
from importlib import import_module
from threading import Thread
from datetime import date
from apis import simplejson as json
from modules.nav_utils import build_url, setView, remove_unwanted_info_keys
from modules.utils import adjust_premiered_date, make_day
from modules.indicators_bookmarks import get_watched_status, get_resumetime, get_watched_status_season, get_watched_status_tvshow, get_watched_info_tv
from apis.trakt_api import get_trakt_tvshow_id
from modules.utils import local_string as ls
from modules import settings
import tikimeta
# from modules.utils import logger

dialog = xbmcgui.Dialog()
window = xbmcgui.Window(10000)

class TVShows:
	def __init__(self, params):
		tikimeta.check_meta_database()
		self.assign_labels()
		self.params = params
		self.items = []
		self.new_page = {}
		self.total_pages = None
		self.exit_list_params = None
		self.is_widget = 'unchecked'
		self.id_type = 'tmdb_id'
		self.list = params.get('list', [])
		self.action = params.get('action', None)

	def fetch_list(self):
		try:
			self.is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
			content_type = 'tvshows'
			mode = self.params.get('mode')
			try: page_no = int(self.params.get('new_page', '1'))
			except ValueError: page_no = self.params.get('new_page')
			letter = self.params.get('new_letter', 'None')
			self.exit_list_params = self.params.get('exit_list_params', None)
			if not self.exit_list_params: self.exit_list_params = xbmc.getInfoLabel('Container.FolderPath')
			var_module = 'tmdb_api' if 'tmdb' in self.action else 'trakt_api' if 'trakt' in self.action else 'imdb_api' if 'imdb' in self.action else None
			if var_module:
				try:
					module = 'apis.%s' % (var_module)
					function = getattr(import_module(module), self.action)
				except: pass
			if self.action in ('tmdb_tv_popular','tmdb_tv_top_rated', 'tmdb_tv_premieres','tmdb_tv_upcoming',
				'tmdb_tv_airing_today','tmdb_tv_on_the_air','trakt_tv_anticipated','trakt_tv_trending'):
				data = function(page_no)
				if 'tmdb' in self.action:
					for item in data['results']: self.list.append(item['id'])
				else:
					for item in data: self.list.append(get_trakt_tvshow_id(item['show']['ids']))
				self.new_page = {'mode': mode, 'action': self.action, 'new_page': str((data['page'] if 'tmdb' in self.action else page_no) + 1), 'foldername': self.action}
			elif self.action == 'tmdb_tv_discover':
				from indexers.discover import set_history
				name = self.params['name']
				query = self.params['query']
				if page_no == 1: set_history('tvshow', name, query)
				data = function(query, page_no)
				for item in data['results']: self.list.append(item['id'])
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'query': query, 'name': name, 'new_page': str(data['page'] + 1), 'foldername': self.action}
			elif self.action in ('trakt_collection', 'trakt_watchlist', 'trakt_collection_widgets'):
				data, total_pages = function('shows', page_no, letter)
				self.list = [i['media_id'] for i in data]
				if total_pages > 2: self.total_pages = total_pages
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'new_letter': letter, 'foldername': self.action}
			elif self.action in ('imdb_watchlist', 'imdb_user_list_contents', 'imdb_keywords_list_contents'):
				self.id_type = 'imdb_id'
				list_id = self.params.get('list_id', None)
				data, next_page = function('tvshows', list_id, page_no)
				self.list = [i['imdb_id'] for i in data]
				if next_page: self.new_page = {'mode': mode, 'action': self.action, 'list_id': list_id, 'new_page': str(page_no + 1), 'new_letter': letter, 'foldername': self.action}
			elif self.action == 'trakt_tv_mosts':
				for item in function(self.params['period'], self.params['duration'], page_no): self.list.append((get_trakt_tvshow_id(item['show']['ids'])))
				self.new_page = {'mode': mode, 'action': self.action, 'period': self.params['period'], 'duration': self.params['duration'], 'new_page': str(page_no + 1), 'foldername': self.action}
			elif self.action == 'trakt_tv_related':
				imdb_id = self.params.get('imdb_id')
				data, total_pages = function(imdb_id, page_no)
				for item in data: self.list.append(get_trakt_tvshow_id(item['ids']))
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'imdb_id': imdb_id, 'foldername': self.action, 'imdb_id': self.params.get('imdb_id')}
			elif self.action == 'tmdb_tv_genres':
				genre_id = self.params['genre_id'] if 'genre_id' in self.params else self.multiselect_genres(self.params.get('genre_list'))
				if not genre_id: return
				data = function(genre_id, page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'genre_id': genre_id, 'foldername': genre_id}
			elif self.action == 'tmdb_tv_languages':
				language = self.params['language']
				if not language: return
				data = function(language, page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'language': language, 'foldername': language}
			elif self.action == 'tmdb_tv_networks':
				data = function(self.params['network_id'], page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'network_id': self.params['network_id'], 'foldername': self.params['network_id']}
			elif self.action == 'trakt_tv_certifications':
				for item in function(self.params['certification'], page_no): self.list.append((get_trakt_tvshow_id(item['show']['ids'])))
				self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'foldername': self.params['certification'], 'certification': self.params['certification']}
			elif self.action == 'tmdb_tv_year':
				data = function(self.params['year'], page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'year': self.params['year'], 'foldername': self.params['year']}
			elif self.action in ('in_progress_tvshows', 'favourites_tvshows', 'watched_tvshows'):
				(var_module, import_function) = ('in_progress', 'in_progress_tvshow') if 'in_progress' in self.action else ('favourites', 'retrieve_favourites') if 'favourites' in self.action else ('indicators_bookmarks', 'get_watched_items') if 'watched' in self.action else ''
				try:
					module = 'modules.%s' % (var_module)
					function = getattr(import_module(module), import_function)
				except: pass
				data, total_pages = function('tvshow', page_no, letter)
				self.list = [i['media_id'] for i in data]
				if total_pages > 2: self.total_pages = total_pages
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'new_letter': letter, 'foldername': self.action}
			elif self.action in ('tmdb_tv_similar', 'tmdb_tv_recommendations'):
				tmdb_id = self.params.get('tmdb_id')
				data = function(tmdb_id, page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'tmdb_id': tmdb_id, 'foldername': self.action}
			elif self.action == 'trakt_recommendations':
				for item in function('shows'): self.list.append(get_trakt_tvshow_id(item['ids']))
			elif self.action == 'tmdb_tv_search':
				query = self.params['query']
				data = function(query, page_no)
				total_pages = data['total_pages']
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'query': query, 'foldername': query}
				self.list = [i['id'] for i in data['results']]
			elif self.action  == 'trakt_tv_search':
				query = self.params['query']
				data, total_pages = function(query, page_no, letter)
				for item in data: self.list.append(get_trakt_tvshow_id(item['show']['ids']))
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'new_letter': letter, 'query': query, 'foldername': query}
			if self.total_pages and not self.is_widget:
				url_params = {'mode': 'build_navigate_to_page', 'db_type': 'TV Shows', 'current_page': page_no, 'total_pages': self.total_pages, 'transfer_mode': mode, 'transfer_action': self.action, 'foldername': self.action, 'query': self.params.get('search_name', ''), 'actor_id': self.params.get('actor_id', '')}
				self.add_dir(url_params, ls(32964), '', 'item_jump.png')
			self.worker()
			if self.new_page:
					self.new_page['exit_list_params'] = self.exit_list_params
					self.add_dir(self.new_page)
		except: pass
		__handle__ = int(argv[1])
		xbmcplugin.setContent(__handle__, content_type)
		xbmcplugin.endOfDirectory(__handle__)
		setView('view.tvshows', content_type)

	def build_tvshow_content(self, item_position, _id):
		try:
			cm = []
			item = self.set_meta(_id)
			try: listitem = xbmcgui.ListItem(offscreen=True)
			except: listitem = xbmcgui.ListItem()
			rootname = item['rootname']
			tmdb_id = item['tmdb_id']
			tvdb_id = item['tvdb_id']
			imdb_id = item['imdb_id']
			title = item['title']
			year = item['year']
			trailer = item['trailer']
			total_seasons = item['total_seasons']
			meta_json = json.dumps(item)
			if self.show_all_episodes:
				if self.all_episodes == 1 and total_seasons > 1: url_params = {'mode': 'build_season_list', 'meta': meta_json, 'tmdb_id': tmdb_id}
				else: url_params = {'mode': 'build_episode_list', 'tmdb_id': tmdb_id, 'season': 'all', 'meta': meta_json}
			else: url_params = {'mode': 'build_season_list', 'meta': meta_json, 'tmdb_id': tmdb_id}
			options_params = {'mode': 'options_menu_choice'}
			extras_params = {'mode': 'extras_menu_choice', 'media_type': 'tv', 'meta': meta_json}
			watched_params = {'mode': 'mark_tv_show_as_watched_unwatched', 'action': 'mark_as_watched', 'title': title, 'year': year, 'media_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'meta_user_info': self.meta_user_info_json}
			unwatched_params = {'mode': 'mark_tv_show_as_watched_unwatched', 'action': 'mark_as_unwatched', 'title': title, 'year': year, 'media_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'meta_user_info': self.meta_user_info_json}
			add_remove_params = {'mode': 'build_add_to_remove_from_list', 'media_type': 'tvshow', 'meta': meta_json, 'orig_mode': self.action}
			cm.append((self.watched_str % self.watched_title, 'RunPlugin(%s)' % build_url(watched_params)))
			cm.append((self.unwatched_str % self.watched_title, 'RunPlugin(%s)' % build_url(unwatched_params)))			
			cm.append((self.addremove_str, 'RunPlugin(%s)' % build_url(add_remove_params)))
			cm.append((self.extras_str,'Container.Update(%s)' % build_url(extras_params)))
			cm.append((self.options_str,'RunPlugin(%s)' % build_url(options_params)))
			if self.action == 'trakt_recommendations':
				hide_recommended_params = {'mode': 'trakt.hide_recommendations', 'db_type': 'shows', 'imdb_id': imdb_id}
				cm.append((self.hide_str, 'RunPlugin(%s)' % build_url(hide_recommended_params)))
			cm.append((self.exit_str, 'Container.Refresh(%s)' % self.exit_list_params))
			url = build_url(url_params)
			listitem.setLabel(title)
			listitem.setContentLookup(False)
			listitem.addContextMenuItems(cm)
			listitem.setCast(item['cast'])
			listitem.setUniqueIDs({'imdb': str(imdb_id), 'tmdb': str(tmdb_id), 'tvdb': str(tvdb_id)})
			listitem.setArt({'poster': item['poster'], 'fanart': item['fanart'], 'icon': item['poster'], 'banner': item['banner'], 'clearart': item['clearart'], 'clearlogo': item['clearlogo'], 'landscape': item['landscape']})
			listitem.setProperty('watchedepisodes', item['total_watched'])
			listitem.setProperty('unwatchedepisodes', item['total_unwatched'])
			listitem.setProperty('totalepisodes', str(item['total_episodes']))
			listitem.setProperty('totalseasons', str(total_seasons))
			if self.is_widget:
				listitem.setProperty('fen_widget', 'true')
				listitem.setProperty('fen_playcount', str(item['playcount']))
				listitem.setProperty('fen_options_menu_params', json.dumps(options_params))
				listitem.setProperty('fen_extras_menu_params', json.dumps(extras_params))
			else:
				listitem.setProperty('fen_listitem_meta', meta_json)
			listitem.setInfo('video', remove_unwanted_info_keys(item))
			self.items.append({'listitem': (url, listitem, True), 'item_no': item_position})
		except: pass

	def set_meta(self, _id):
		meta = tikimeta.tvshow_meta(self.id_type, _id, self.meta_user_info)
		if not meta: return
		playcount, overlay, total_watched, total_unwatched = get_watched_status_tvshow(self.watched_info, self.use_trakt, meta['tmdb_id'], meta.get('total_episodes'))
		meta.update({'playcount': playcount, 'overlay': overlay, 'total_watched': str(total_watched), 'total_unwatched': str(total_unwatched)})
		return meta

	def worker(self):
		threads = []
		if self.is_widget == 'unchecked': self.is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
		if not self.exit_list_params: self.exit_list_params = xbmc.getInfoLabel('Container.FolderPath')
		self.watched_info, self.use_trakt = get_watched_info_tv()
		self.meta_user_info = tikimeta.retrieve_user_info()
		self.watched_title = 'Trakt' if self.use_trakt in (1, 2) else 'Fen'
		self.meta_user_info_json = json.dumps(self.meta_user_info)
		self.all_episodes = settings.default_all_episodes()
		self.show_all_episodes = True if self.all_episodes in (1, 2) else False
		window.clearProperty('fen_fanart_error')
		for item_position, item in enumerate(self.list): threads.append(Thread(target=self.build_tvshow_content, args=(item_position, item)))
		[i.start() for i in threads]
		[i.join() for i in threads]
		item_list = sorted(self.items, key=lambda k: k['item_no'])
		item_list = [i['listitem'] for i in item_list]
		xbmcplugin.addDirectoryItems(int(argv[1]), item_list, len(item_list))

	def multiselect_genres(self, genre_list):
		import os
		genre_list = json.loads(genre_list)
		choice_list = []
		icon_directory = settings.get_theme()
		for genre, value in sorted(genre_list.items()):
			listitem = xbmcgui.ListItem(genre)
			listitem.setArt({'icon': os.path.join(icon_directory, value[1])})
			listitem.setProperty('genre_id', value[0])
			choice_list.append(listitem)
		chosen_genres = dialog.multiselect(ls(32847), choice_list, useDetails=True)
		if not chosen_genres: return
		genre_ids = [choice_list[i].getProperty('genre_id') for i in chosen_genres]
		return ','.join(genre_ids)

	def assign_labels(self):
		self.watched_str, self.unwatched_str, self.addremove_str, self.extras_str, self.options_str = ls(32642), ls(32643), ls(32644), ls(32645), ls(32646)
		self.hide_str, self.exit_str, self.tv_shows_str, self.browse_str = ls(32648), ls(32650), ls(32029), ls(32652)

	def add_dir(self, url_params, list_name=ls(32799), info=ls(32800), iconImage='item_next.png'):
		icon = os.path.join(settings.get_theme(), iconImage)
		url = build_url(url_params)
		listitem = xbmcgui.ListItem(list_name)
		listitem.setArt({'icon': icon, 'fanart': os.path.join(xbmc.translatePath('special://home/addons/plugin.video.fen'), "fanart.png")})
		if url_params['mode'] == 'build_navigate_to_page':
			listitem.setProperty('SpecialSort', 'top')
			listitem.addContextMenuItems([(ls(32784), 'RunPlugin(%s)' % build_url({'mode': 'toggle_jump_to'}))])
		else:
			listitem.setProperty('SpecialSort', 'bottom')
		xbmcplugin.addDirectoryItem(handle=int(argv[1]), url=url, listitem=listitem, isFolder=True)

def build_season_list(params):
	def _aired_episodes(item):
		episodes_data = item['episodes_data']
		aired = 0
		for ep in episodes_data:
			episode_date, premiered = adjust_premiered_date(ep['firstAired'], adjust_hours)
			if episode_date and current_adjusted_date >= episode_date: aired += 1
		return aired
	def _process():
		for item in season_data:
			try:
				try: listitem = xbmcgui.ListItem(offscreen=True)
				except: listitem = xbmcgui.ListItem()
				cm = []
				overview = item['overview']
				name = item['name']
				poster_path = item['poster_path']
				season_number = item['season_number']
				episode_count = item['episode_count']
				try: year = [i['firstAired'].split('-')[0] for i in item['episodes_data'] if i['airedSeason'] == season_number][0]
				except: year = show_year
				try: aired_episodes = _aired_episodes(item)
				except: aired_episodes = item['episode_count']
				plot = overview if overview != '' else show_plot
				title = name if use_season_title and name != '' else '%s %s' % (season_str, str(season_number))
				season_poster = poster_path if poster_path is not None else show_poster
				playcount, overlay, watched, unwatched = get_watched_status_season(watched_info, use_trakt, tmdb_id, season_number, aired_episodes)
				url_params = {'mode': 'build_episode_list', 'tmdb_id': tmdb_id, 'season': season_number}
				watched_params = {'mode': 'mark_season_as_watched_unwatched', 'action': 'mark_as_watched', 'title': show_title, 'year': show_year, 'media_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'season': season_number, 'meta_user_info': meta_user_info_json}
				unwatched_params = {'mode': 'mark_season_as_watched_unwatched', 'action': 'mark_as_unwatched', 'title': show_title, 'year': show_year, 'media_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'season': season_number, 'meta_user_info': meta_user_info_json}
				extras_params = {'mode': 'extras_menu_choice', 'media_type': 'season', 'meta': meta_json, 'default_season': season_number}
				options_params = {'mode': 'options_menu_choice'}
				cm.append((watched_str % watched_title,'RunPlugin(%s)' % build_url(watched_params)))
				cm.append((unwatched_str % watched_title,'RunPlugin(%s)' % build_url(unwatched_params)))
				cm.append((extras_str,'Container.Update(%s)' % build_url(extras_params)))
				cm.append((options_str,'RunPlugin(%s)' % build_url(options_params)))
				url = build_url(url_params)
				listitem.setLabel(title)
				listitem.setContentLookup(False)
				listitem.setProperty('watchedepisodes', str(watched))
				listitem.setProperty('unwatchedepisodes', str(unwatched))
				listitem.setProperty('totalepisodes', str(aired_episodes))
				listitem.addContextMenuItems(cm)
				listitem.setArt({'poster': season_poster, 'icon': season_poster, 'thumb': season_poster, 'fanart': fanart, 'banner': banner, 'clearart': clearart, 'clearlogo': clearlogo, 'landscape': landscape})
				listitem.setCast(cast)
				listitem.setUniqueIDs({'imdb': str(imdb_id), 'tmdb': str(tmdb_id), 'tvdb': str(tvdb_id)})
				listitem.setInfo('video', {'mediatype': 'season', 'trailer': trailer, 'title': title, 'size': '0', 'duration': episode_run_time, 'plot': plot, 'rating': rating,
								'premiered': premiered, 'studio': studio, 'year': year,'genre': genre, 'mpaa': mpaa, 'tvshowtitle': show_title, 'imdbnumber': imdb_id,
								'votes': votes, 'season': season_number,'playcount': playcount, 'overlay': overlay})
				if is_widget:
					listitem.setProperty('fen_widget', 'true')
					listitem.setProperty('fen_playcount', str(playcount))
					listitem.setProperty('fen_options_menu_params', json.dumps(options_params))
					listitem.setProperty('fen_extras_menu_params', json.dumps(extras_params))
				else:
					listitem.setProperty('fen_listitem_meta', meta_json)
				yield (url, listitem, True)
			except: pass
	__handle__ = int(argv[1])
	is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
	meta_user_info = tikimeta.retrieve_user_info()
	meta_user_info_json = json.dumps(meta_user_info)
	if 'meta' in params:
		meta = json.loads(params.get('meta'))
	else:
		window.clearProperty('fen_fanart_error')
		meta = tikimeta.tvshow_meta('tmdb_id', params.get('tmdb_id'), meta_user_info)
	season_data = tikimeta.all_episodes_meta(meta['tmdb_id'], meta['tvdb_id'], meta['tvdb_summary']['airedSeasons'], meta['season_data'], meta_user_info)
	if not season_data: return
	watched_str, unwatched_str, extras_str, options_str, season_str = ls(32642), ls(32643), ls(32645), ls(32646), ls(32537)
	meta_json = json.dumps(meta)
	tmdb_id, tvdb_id, imdb_id = meta['tmdb_id'], meta['tvdb_id'], meta['imdb_id']
	show_title, show_year, show_plot = meta['title'], meta['year'], meta['plot']
	show_poster, fanart, banner = meta['poster'], meta['fanart'], meta['banner']
	clearlogo, clearart, landscape = meta['clearlogo'], meta['clearart'], meta['landscape']
	cast, mpaa, votes = meta['cast'], meta['mpaa'], meta.get('votes')
	trailer, genre, studio = str(meta['trailer']), meta.get('genre'), meta.get('studio')
	episode_run_time, rating, premiered = meta.get('episode_run_time'), meta.get('rating'), meta.get('premiered')
	if not settings.show_specials(): season_data = [i for i in season_data if not i['season_number'] == 0]
	season_data = sorted(season_data, key=lambda k: k['season_number'])
	use_season_title = settings.use_season_title()
	watched_indicators = settings.watched_indicators()
	watched_title = 'Trakt' if watched_indicators in (1, 2) else 'Fen'
	watched_info, use_trakt = get_watched_info_tv()
	adjust_hours = int(settings.addon().getSetting('datetime.offset'))
	current_adjusted_date = settings.adjusted_datetime(dt=True)
	item_list = list(_process())
	xbmcplugin.addDirectoryItems(__handle__, item_list)
	xbmcplugin.setContent(__handle__, 'seasons')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.seasons', 'seasons')
	window.setProperty('fen_media_meta', meta_json)

def build_episode_list(params):
	def _process():
		for item in episodes_data:
			try:
				try: listitem = xbmcgui.ListItem(offscreen=True)
				except: listitem = xbmcgui.ListItem()
				cm = []
				season = item['season']
				episode = item['episode']
				ep_name = item['title']
				premiered = item['premiered']
				episode_date, premiered = adjust_premiered_date(premiered, adjust_hours)
				playcount, overlay = get_watched_status(watched_info, use_trakt, 'episode', tmdb_id, season, episode)
				resumetime = get_resumetime('episode', tmdb_id, season, episode)
				query = title + ' S%.2dE%.2d' % (int(season), int(episode))
				display_name = '%s - %dx%.2d' % (title, season, episode)
				thumb = item['thumb'] if item.get('thumb', None) else fanart
				meta.update({'vid_type': 'episode', 'rootname': display_name, 'season': season,
							'episode': episode, 'premiered': premiered, 'ep_name': ep_name,
							'plot': item['plot'], 'thumb': thumb, 'playcount': playcount})
				item.update({'trailer': trailer, 'tvshowtitle': title, 'premiered': premiered,
							'genre': genre, 'duration': duration, 'mpaa': mpaa,
							'studio': studio, 'playcount': playcount, 'overlay': overlay})
				meta_json = json.dumps(meta)
				extras_params = {'mode': 'extras_menu_choice', 'media_type': 'episode', 'meta': meta_json, 'default_season': season}
				options_params = {'mode': 'options_menu_choice', 'suggestion': query, 'content': 'episode', 'meta': meta_json}
				url_params = {'mode': 'play_media', 'vid_type': 'episode', 'tmdb_id': tmdb_id, 'query': query, 'tvshowtitle': meta['rootname'],
							'season': season, 'episode': episode, 'meta': meta_json}
				url = build_url(url_params)
				display = ep_name
				unaired = False
				if not episode_date or current_adjusted_date < episode_date:
					unaired = True
					display = '[I][COLOR %s]%s[/COLOR][/I]' % (unaired_color, ep_name)
					item['title'] = display
				item['sortseason'] = season
				item['sortepisode'] = episode
				if not unaired:
					watched_params = {'mode': 'mark_episode_as_watched_unwatched', 'action': 'mark_as_watched', 'media_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'season': season, 'episode': episode,  'title': title, 'year': year}
					unwatched_params = {'mode': 'mark_episode_as_watched_unwatched', 'action': 'mark_as_unwatched', 'media_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'season': season, 'episode': episode,  'title': title, 'year': year}
					cm.append((watched_str % watched_title, 'RunPlugin(%s)' % build_url(watched_params)))
					cm.append((unwatched_str % watched_title, 'RunPlugin(%s)' % build_url(unwatched_params)))
				cm.append((extras_str,'Container.Update(%s)' % build_url(extras_params)))
				cm.append((options_str,'RunPlugin(%s)' % build_url(options_params)))
				if not unaired and resumetime != '0': cm.append((clearprog_str, 'RunPlugin(%s)' % build_url({'mode': 'watched_unwatched_erase_bookmark', 'db_type': 'episode', 'media_id': tmdb_id, 'season': season, 'episode': episode, 'refresh': 'true'})))
				listitem.setLabel(display)
				listitem.setContentLookup(False)
				listitem.setProperty('resumetime', resumetime)
				listitem.addContextMenuItems(cm)
				listitem.setArt({'poster': show_poster, 'fanart': fanart, 'thumb': thumb, 'icon':thumb, 'banner': banner, 'clearart': clearart, 'clearlogo': clearlogo, 'landscape': thumb})
				listitem.setCast(cast)
				listitem.setUniqueIDs({'imdb': str(imdb_id), 'tmdb': str(tmdb_id), 'tvdb': str(tvdb_id)})
				listitem.setInfo('video', remove_unwanted_info_keys(item))
				if is_widget:
					listitem.setProperty('fen_widget', 'true')
					listitem.setProperty('fen_playcount', str(playcount))
					listitem.setProperty('fen_options_menu_params', json.dumps(options_params))
					listitem.setProperty('fen_extras_menu_params', json.dumps(extras_params))
				yield (url, listitem, False)
			except: pass
	__handle__ = int(argv[1])
	is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
	unaired_color = settings.unaired_episode_colour()
	meta_user_info = tikimeta.retrieve_user_info()
	meta_user_info_json = json.dumps(meta_user_info)
	all_episodes = True if params.get('season') == 'all' else False
	if all_episodes:
		if 'meta' in params:
			meta = json.loads(params.get('meta'))
		else:
			window.clearProperty('fen_fanart_error')
			meta = tikimeta.tvshow_meta('tmdb_id', params.get('tmdb_id'), meta_user_info)
	else:
		try:
			meta = json.loads(window.getProperty('fen_media_meta'))
		except:
			window.clearProperty('fen_fanart_error')
			meta = tikimeta.tvshow_meta('tmdb_id', params.get('tmdb_id'), meta_user_info)
	watched_str, unwatched_str, extras_str, options_str, clearprog_str = ls(32642), ls(32643), ls(32645), ls(32646), ls(32651)
	tmdb_id, tvdb_id, imdb_id = meta['tmdb_id'], meta['tvdb_id'], meta['imdb_id']
	title, year, rootname = meta['title'], meta['year'], meta['rootname']
	show_poster, fanart, banner = meta['poster'], meta['fanart'], meta['banner']
	clearlogo, clearart, landscape = meta['clearlogo'], meta['clearart'], meta['landscape']
	cast, mpaa, duration = meta['cast'], meta['mpaa'], meta.get('duration')
	trailer, genre, studio = str(meta['trailer']), meta.get('genre'), meta.get('studio')
	adjust_hours = int(settings.addon().getSetting('datetime.offset'))
	current_adjusted_date = settings.adjusted_datetime(dt=True)
	watched_indicators = settings.watched_indicators()
	watched_title = 'Trakt' if watched_indicators in (1, 2) else 'Fen'
	episodes_data = tikimeta.season_episodes_meta(tmdb_id, tvdb_id, params.get('season'), meta['tvdb_summary']['airedSeasons'], meta['season_data'], meta_user_info, all_episodes)
	if all_episodes:
		if not settings.show_specials(): episodes_data = [i for i in episodes_data if not i['season'] == 0]
	watched_info, use_trakt = get_watched_info_tv()
	item_list = list(_process())
	xbmcplugin.addDirectoryItems(__handle__, item_list)
	xbmcplugin.setContent(__handle__, 'episodes')
	xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_EPISODE)
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.episodes', 'episodes')

def build_episode(item, watched_info, use_trakt, meta_user_info, meta_user_info_json, is_widget):
	def check_for_unaired(premiered, season):
		if item.get('ignore_unaired', False): return False
		unaired = False
		adjust_hours = item.get('adjust_hours', None)
		if not adjust_hours : adjust_hours = int(settings.addon().getSetting('datetime.offset'))
		current_adjusted_date = item.get('current_adjusted_date', None)
		if not current_adjusted_date : current_adjusted_date = settings.adjusted_datetime(dt=True)
		episode_date, premiered = adjust_premiered_date(premiered, adjust_hours)
		if not episode_date or current_adjusted_date < episode_date:
			unaired = True
		return unaired, current_adjusted_date, episode_date, premiered
	def build_display():
		if nextep_info:
			if episode_date: display_premiered = make_day(episode_date)
			else: display_premiered == 'UNKNOWN'
			airdate = '[[COLOR %s]%s[/COLOR]] ' % (nextep_info['airdate_colour'], display_premiered) if nextep_info['include_airdate'] else ''
			highlight_color = nextep_info['unwatched_colour'] if item.get('unwatched', False) else nextep_info['unaired_colour'] if unaired else ''
			italics_open, italics_close = ('[I]', '[/I]') if highlight_color else ('', '')
			if highlight_color: episode_info = '%s[COLOR %s]%dx%.2d - %s[/COLOR]%s' % (italics_open, highlight_color, info['season'], info['episode'], info['title'], italics_close)
			else: episode_info = '%s%dx%.2d - %s%s' % (italics_open, info['season'], info['episode'], info['title'], italics_close)
			display = '%s%s: %s' % (airdate, title, episode_info)
		elif trakt_calendar:
			if episode_date: display_premiered = make_day(episode_date)
			else: display_premiered == 'UNKNOWN'
			display = '[%s] %s: %dx%.2d - %s' % (display_premiered, title.upper(), info['season'], info['episode'], info['title'])
			if unaired:
				unaired_color = settings.unaired_episode_colour()
				displays = display.split(']')
				display = '[COLOR %s]' % unaired_color + displays[0] + '][/COLOR]' + displays[1]
		else:
			unaired_color = settings.unaired_episode_colour()
			color_tags = ('[COLOR %s]' % unaired_color, '[/COLOR]') if unaired else ('', '')
			display = '%s: %s%dx%.2d - %s%s' % (title.upper(), color_tags[0], info['season'], info['episode'], info['title'], color_tags[1])
		return display
	try:
		try: listitem = xbmcgui.ListItem(offscreen=True)
		except: listitem = xbmcgui.ListItem()
		cm = []
		nextep_info = item.get('nextep_display_settings', None)
		trakt_calendar = item.get('trakt_calendar', False)
		action = item.get('action', '')
		meta = item['meta']
		tmdb_id = meta['tmdb_id']
		tvdb_id = meta['tvdb_id']
		imdb_id = meta['imdb_id']
		title = meta['title']
		year = meta['year']
		episodes_data = tikimeta.season_episodes_meta(tmdb_id, tvdb_id, item['season'], meta['tvdb_summary']['airedSeasons'], meta['season_data'], meta_user_info)
		info = [i for i in episodes_data if i['episode'] == item['episode']][0]
		season = info['season']
		episode = info['episode']
		premiered = info['premiered']
		unaired, current_adjusted_date, episode_date, premiered = check_for_unaired(premiered, season)
		if unaired and not item.get('include_unaired', False): return
		thumb = info['thumb'] if info.get('thumb', None) else meta['fanart']
		playcount, overlay = get_watched_status(watched_info, use_trakt, 'episode', tmdb_id, season, episode)
		info.update({'trailer': str(meta.get('trailer')), 'tvshowtitle': title, 'premiered': premiered,
					'genre': meta.get('genre'), 'duration': meta.get('duration'), 'mpaa': meta.get('mpaa'),
					'studio': meta.get('studio'), 'playcount': playcount, 'overlay': overlay})
		resumetime = get_resumetime('episode', tmdb_id, season, episode)
		query = title + ' S%.2dE%.2d' % (season, episode)
		display = build_display()
		rootname = '%s (%s)' % (title, year)
		meta.update({'vid_type': 'episode', 'rootname': rootname, 'season': season,
					'episode': episode, 'premiered': premiered, 'ep_name': info['title'],
					'plot': info['plot'], 'thumb': thumb, 'playcount': playcount})
		meta_json = json.dumps(meta)
		url_params = {'mode': 'play_media', 'vid_type': 'episode', 'tmdb_id': tmdb_id, 'query': query, 'tvshowtitle': meta['rootname'],
					'season': season, 'episode': episode, 'meta': meta_json}
		url = build_url(url_params)
		browse_url = build_url({'mode': 'build_season_list', 'meta': meta_json})
		extras_params = {'mode': 'extras_menu_choice', 'media_type': 'episode', 'meta': meta_json, 'default_season': season}
		options_params = {'mode': 'options_menu_choice', 'suggestion': query, 'content': 'episode', 'meta': meta_json}
		if not unaired:
			watched_indicators = item['watched_indicators'] if 'watched_indicators' in item else settings.watched_indicators()
			watched_title = 'Trakt' if watched_indicators in (1, 2) else 'Fen'
			watched_params = {'mode': 'mark_episode_as_watched_unwatched', 'action': 'mark_as_watched', 'media_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'season': season, 'episode': episode,  'title': title, 'year': year}
			unwatched_params = {'mode': 'mark_episode_as_watched_unwatched', 'action': 'mark_as_unwatched', 'media_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id, 'season': season, 'episode': episode,  'title': title, 'year': year}
			cm.append((ls(32642) % watched_title, 'RunPlugin(%s)' % build_url(watched_params)))
			cm.append((ls(32643) % watched_title, 'RunPlugin(%s)' % build_url(unwatched_params)))
		if action == 'next_episode':
			nextep_manage_params = {'mode': 'next_episode_context_choice'}
			cm.append(('[B]%s[/B]' % ls(32599),'RunPlugin(%s)'% build_url(nextep_manage_params)))
			cm.append((ls(32653), 'Container.Refresh()'))
		cm.append((ls(32652),'Container.Update(%s)' % browse_url))
		cm.append((ls(32645),'Container.Update(%s)' % build_url(extras_params)))
		cm.append((ls(32646),'RunPlugin(%s)' % build_url(options_params)))
		if not unaired and resumetime != '0': cm.append((ls(32651), 'RunPlugin(%s)' % build_url({'mode': 'watched_unwatched_erase_bookmark', 'db_type': 'episode', 'media_id': tmdb_id, 'season': season, 'episode': episode, 'refresh': 'true'})))
		listitem.setLabel(display)
		listitem.setContentLookup(False)
		listitem.setProperty('resumetime', resumetime)
		listitem.setArt({'poster': meta['poster'], 'fanart': meta['fanart'], 'thumb':thumb, 'icon':thumb, 'banner': meta['banner'], 'clearart': meta['clearart'], 'clearlogo': meta['clearlogo'], 'landscape': thumb})
		listitem.addContextMenuItems(cm)
		listitem.setCast(meta['cast'])
		listitem.setUniqueIDs({'imdb': str(imdb_id), 'tmdb': str(tmdb_id), 'tvdb': str(tvdb_id)})
		info['title'] = display
		listitem.setInfo('video', remove_unwanted_info_keys(info))
		if is_widget:
			listitem.setProperty('fen_widget', 'true')
			listitem.setProperty('fen_playcount', str(playcount))
			listitem.setProperty('fen_options_menu_params', json.dumps(options_params))
			listitem.setProperty('fen_extras_menu_params', json.dumps(extras_params))
		return {'listitem': (url, listitem, False), 'curr_last_played_parsed': item.get('curr_last_played_parsed', ''), 'label': display, 'order': item.get('order', ''), 'name': query, 'first_aired': premiered}
	except: pass



