# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import os
from sys import argv
import tikimeta
from importlib import import_module
from threading import Thread
from modules.nav_utils import build_url, setView, remove_unwanted_info_keys
from modules.indicators_bookmarks import get_watched_status, get_resumetime, get_watched_info_movie
from apis import simplejson as json
from apis.trakt_api import get_trakt_movie_id
from modules.utils import local_string as ls
from modules import settings
# from modules.utils import logger

dialog = xbmcgui.Dialog()

window = xbmcgui.Window(10000)

class Movies:
	def __init__(self, params):
		tikimeta.check_meta_database()
		self.assign_labels()
		self.params = params
		self.items = []
		self.new_page = {}
		self.total_pages = None
		self.exit_list_params = None
		self.is_widget = 'unchecked'
		self.id_type = params.get('id_type', 'tmdb_id')
		self.list = params.get('list', [])
		self.action = params.get('action', None)

	def fetch_list(self):
		try:
			self.is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
			content_type = 'movies'
			mode = self.params.get('mode')
			try: page_no = int(self.params.get('new_page', '1'))
			except ValueError: page_no = self.params.get('new_page')
			letter = self.params.get('new_letter', 'None')
			self.exit_list_params = self.params.get('exit_list_params', None)
			if not self.exit_list_params: self.exit_list_params = xbmc.getInfoLabel('Container.FolderPath')
			var_module = 'tmdb_api' if 'tmdb' in self.action else 'trakt_api' if 'trakt' in self.action else 'imdb_api' if 'imdb' in self.action else ''
			if var_module:
				try:
					module = 'apis.%s' % (var_module)
					function = getattr(import_module(module), self.action)
				except: pass
			if self.action in ('tmdb_movies_popular','tmdb_movies_blockbusters','tmdb_movies_in_theaters',
				'tmdb_movies_top_rated','tmdb_movies_upcoming','tmdb_movies_latest_releases','tmdb_movies_premieres',
				'trakt_movies_trending','trakt_movies_anticipated','trakt_movies_top10_boxoffice'):
				data = function(page_no)
				if 'tmdb' in self.action:
					data = function(page_no)
					for item in data['results']: self.list.append(item['id'])
				else:
					data = function(page_no)
					for item in data: self.list.append(get_trakt_movie_id(item['movie']['ids']))
				if self.action not in ('trakt_movies_top10_boxoffice'): self.new_page = {'mode': mode, 'action': self.action, 'new_page': str((data['page'] if 'tmdb' in self.action else page_no) + 1), 'foldername': self.action}
			elif self.action == 'tmdb_movies_discover':
				from indexers.discover import set_history
				name = self.params['name']
				query = self.params['query']
				if page_no == 1: set_history('movie', name, query)
				data = function(query, page_no)
				for item in data['results']: self.list.append(item['id'])
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'query': query, 'name': name, 'new_page': str(data['page'] + 1), 'foldername': self.action}
			elif self.action in ('trakt_collection', 'trakt_watchlist', 'trakt_collection_widgets'):
				data, total_pages = function('movies', page_no, letter)
				self.list = [i['media_id'] for i in data]
				if total_pages > 2: self.total_pages = total_pages
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'new_letter': letter, 'foldername': self.action}
			elif self.action == 'imdb_movies_oscar_winners':
				from modules.nav_utils import oscar_winners_tmdb_ids
				self.list = oscar_winners_tmdb_ids()
			elif self.action in ('imdb_watchlist', 'imdb_user_list_contents', 'imdb_keywords_list_contents'):
				self.id_type = 'imdb_id'
				list_id = self.params.get('list_id', None)
				data, next_page = function('movies', list_id, page_no)
				self.list = [i['imdb_id'] for i in data]
				if next_page: self.new_page = {'mode': mode, 'action': self.action, 'list_id': list_id, 'new_page': str(page_no + 1), 'new_letter': letter, 'foldername': self.action}
			elif self.action == ('trakt_movies_mosts'):
				for item in (function(self.params['period'], self.params['duration'], page_no)): self.list.append(get_trakt_movie_id(item['movie']['ids']))
				self.new_page = {'mode': mode, 'action': self.action, 'period': self.params['period'], 'duration': self.params['duration'], 'new_page': str(page_no + 1), 'foldername': self.action}
			elif self.action == 'trakt_movies_related':
				imdb_id = self.params.get('imdb_id')
				data, total_pages = function(imdb_id, page_no)
				for item in data: self.list.append(get_trakt_movie_id(item['ids']))
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'imdb_id': imdb_id, 'foldername': self.action}
			elif self.action == 'tmdb_movies_genres':
				genre_id = self.params['genre_id'] if 'genre_id' in self.params else self.multiselect_genres(self.params.get('genre_list'))
				if not genre_id: return
				data = function(genre_id, page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'genre_id': genre_id, 'foldername': genre_id}
			elif self.action == 'tmdb_movies_languages':
				language = self.params['language']
				if not language: return
				data = function(language, page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'language': language, 'foldername': language}
			elif self.action == 'tmdb_movies_networks':
				company = self.params['company'] if 'company' in self.params else self.get_company(self.params['network_name'])['id']
				data = function(company, page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'company': company, 'foldername': company}
			elif self.action == 'tmdb_movies_year':
				data = function(self.params['year'], page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'year': self.params.get('year'), 'foldername': self.params.get('year')}
			elif self.action == 'tmdb_movies_certifications':
				data = function(self.params['certification'], page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'certification': self.params.get('certification'), 'foldername': self.params.get('certification')}
			elif self.action == 'tmdb_movies_collection':
				data = function(str(self.params['collection_id']))
				self.list = [i['id'] for i in data['parts']]
			elif self.action in ('in_progress_movies', 'favourites_movies', 'watched_movies'):
				(var_module, import_function) = ('in_progress', 'in_progress_movie') if 'in_progress' in self.action else ('favourites', 'retrieve_favourites') if 'favourites' in self.action else ('indicators_bookmarks', 'get_watched_items') if 'watched' in self.action else ''
				try:
					module = 'modules.%s' % (var_module)
					function = getattr(import_module(module), import_function)
				except: pass
				data, total_pages = function('movie', page_no, letter)
				self.list = [i['media_id'] for i in data]
				if total_pages > 2: self.total_pages = total_pages
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'new_letter': letter, 'foldername': self.action}
			elif self.action in ('tmdb_movies_similar', 'tmdb_movies_recommendations'):
				tmdb_id = self.params.get('tmdb_id')
				data = function(tmdb_id, page_no)
				self.list = [i['id'] for i in data['results']]
				if data['page'] < data['total_pages']: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(data['page'] + 1), 'tmdb_id': tmdb_id, 'foldername': self.action}
			elif self.action == 'trakt_recommendations':
				for item in function('movies'): self.list.append(get_trakt_movie_id(item['ids']))
			elif self.action  == 'tmdb_movies_search':
				query = self.params['query']
				data = function(query, page_no)
				total_pages = data['total_pages']
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'new_letter': letter, 'query': query, 'foldername': query}
				self.list = [i['id'] for i in data['results']]
			elif self.action  == 'trakt_movies_search':
				query = self.params['query']
				data, total_pages = function(query, page_no, letter)
				for item in data: self.list.append(get_trakt_movie_id(item['movie']['ids']))
				if total_pages > page_no: self.new_page = {'mode': mode, 'action': self.action, 'new_page': str(page_no + 1), 'new_letter': letter, 'query': query, 'foldername': query}
			if self.total_pages and not self.is_widget:
				url_params = {'mode': 'build_navigate_to_page', 'db_type': 'Movies', 'current_page': page_no, 'total_pages': self.total_pages, 'transfer_mode': mode, 'transfer_action': self.action, 'foldername': self.action, 'query': self.params.get('search_name', ''), 'actor_id': self.params.get('actor_id', '')}
				self.add_dir(url_params, ls(32964), '', 'item_jump.png')
			self.worker()
			if self.new_page:
					self.new_page['exit_list_params'] = self.exit_list_params
					self.add_dir(self.new_page)
		except: pass
		__handle__ = int(argv[1])
		xbmcplugin.setContent(__handle__, content_type)
		xbmcplugin.endOfDirectory(__handle__)
		setView('view.movies', content_type)
	
	def build_movie_content(self, item_position, _id):
		try:
			cm = []
			item = self.set_meta(_id)
			try: listitem = xbmcgui.ListItem(offscreen=True)
			except: listitem = xbmcgui.ListItem()
			rootname = item['rootname']
			tmdb_id = item['tmdb_id']
			imdb_id = item['imdb_id']
			title = item['title']
			trailer = item['trailer']
			playcount = item['playcount']
			poster = item['poster']
			meta_json = json.dumps(item)
			resumetime = get_resumetime('movie', tmdb_id)
			url_params = {'mode': 'play_media', 'vid_type': 'movie', 'query': rootname, 'tmdb_id': tmdb_id, 'meta': meta_json}
			extras_params = {'mode': 'extras_menu_choice', 'media_type': 'movies', 'meta': meta_json}
			options_params = {'mode': 'options_menu_choice', 'suggestion': rootname, 'content': 'movie', 'meta': meta_json}
			watched_params = {'mode': 'mark_movie_as_watched_unwatched', 'action': 'mark_as_watched', 'media_id': tmdb_id, 'meta_user_info': self.meta_user_info_json, 'title': title, 'year': item['year']}
			unwatched_params = {'mode': 'mark_movie_as_watched_unwatched', 'action': 'mark_as_unwatched', 'media_id': tmdb_id, 'meta_user_info': self.meta_user_info_json, 'title': title, 'year': item['year']}
			add_remove_params = {'mode': 'build_add_to_remove_from_list', 'media_type': 'movie', 'meta': meta_json, 'orig_mode': self.action}
			cm.append((self.watched_str % self.watched_title, 'RunPlugin(%s)' % build_url(watched_params)))
			cm.append((self.unwatched_str % self.watched_title, 'RunPlugin(%s)' % build_url(unwatched_params)))
			cm.append((self.addremove_str,'RunPlugin(%s)' % build_url(add_remove_params)))
			cm.append((self.extras_str,'Container.Update(%s)' % build_url(extras_params)))
			cm.append((self.options_str,'RunPlugin(%s)' % build_url(options_params)))
			if resumetime != '0': cm.append((self.clearprog_str, 'RunPlugin(%s)' % build_url({"mode": "watched_unwatched_erase_bookmark", "db_type": "movie", "media_id": tmdb_id, "refresh": "true"})))
			if self.action == 'trakt_recommendations': cm.append((self.hide_str, 'RunPlugin(%s)' % build_url({'mode': 'trakt.hide_recommendations', 'db_type': 'movies', 'imdb_id': imdb_id})))
			cm.append((self.exit_str, 'Container.Refresh(%s)' % self.exit_list_params))
			url = build_url(url_params)
			listitem.setLabel(title)
			listitem.setContentLookup(False)
			listitem.addContextMenuItems(cm)
			listitem.setCast(item['cast'])
			listitem.setUniqueIDs({'imdb': str(imdb_id), 'tmdb': str(tmdb_id)})
			listitem.setArt({'poster': poster, 'fanart': item['fanart'], 'icon': poster, 'banner': item['banner'], 'clearart': item['clearart'], 'clearlogo': item['clearlogo'], 'landscape': item['landscape'], 'discart': item['discart']})
			listitem.setInfo('Video', remove_unwanted_info_keys(item))
			listitem.setProperty("resumetime", resumetime)
			if self.is_widget:
				listitem.setProperty('fen_widget', 'true')
				listitem.setProperty('fen_playcount', str(playcount))
				listitem.setProperty('fen_options_menu_params', json.dumps(options_params))
				listitem.setProperty('fen_extras_menu_params', json.dumps(extras_params))
			else:
				listitem.setProperty('fen_listitem_meta', meta_json)
			self.items.append({'listitem': (url, listitem, False), 'item_no': item_position})
		except: pass

	def set_meta(self, _id):
		meta = tikimeta.movie_meta(self.id_type, _id, self.meta_user_info)
		if not meta: return
		playcount, overlay = get_watched_status(self.watched_info, self.use_trakt, 'movie', meta['tmdb_id'])
		meta.update({'playcount': playcount, 'overlay': overlay})
		return meta

	def worker(self):
		threads = []
		if self.is_widget == 'unchecked': self.is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
		if not self.exit_list_params: self.exit_list_params = xbmc.getInfoLabel('Container.FolderPath')
		self.watched_info, self.use_trakt = get_watched_info_movie()
		self.meta_user_info = tikimeta.retrieve_user_info()
		self.watched_title = 'Trakt' if self.use_trakt in (1, 2) else "Fen"
		self.meta_user_info_json = json.dumps(self.meta_user_info)
		window.clearProperty('fen_fanart_error')
		for item_position, item in enumerate(self.list): threads.append(Thread(target=self.build_movie_content, args=(item_position, item)))
		[i.start() for i in threads]
		[i.join() for i in threads]
		item_list = sorted(self.items, key=lambda k: k['item_no'])
		item_list = [i['listitem'] for i in item_list]
		xbmcplugin.addDirectoryItems(int(argv[1]), item_list, len(item_list))

	def multiselect_genres(self, genre_list):
		import os
		dialog = xbmcgui.Dialog()
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

	def get_company(self, company_name):
		from apis.tmdb_api import tmdb_company_id
		company_choice = None
		try:
			results = tmdb_company_id(company_name)
			if results['total_results'] == 1: return results['results'][0]
			try: company_choice = [i for i in results['results'] if i['name'] == company_name][0]
			except: pass
		except: pass
		return company_choice

	def assign_labels(self):
		self.watched_str, self.unwatched_str, self.addremove_str, self.extras_str, self.options_str = ls(32642), ls(32643), ls(32644), ls(32645), ls(32646)
		self.hide_str, self.exit_str, self.clearprog_str, self.movies_str = ls(32648), ls(32649), ls(32651), ls(32028)

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
