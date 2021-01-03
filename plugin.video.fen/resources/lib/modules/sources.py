# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
try: from urllib import unquote
except ImportError: from urllib.parse import unquote
import os
from sys import argv
from sys import exit as sysexit
import time
from datetime import datetime, timedelta
from threading import Thread
from modules import debrid
from apis import simplejson as json
from windows.source_results import SourceResults
from modules.source_utils import sources, toggle_all, external_scrapers_reset_stats, scraperNames
from modules.nav_utils import build_url, setView, notification, close_all_dialog, show_busy_dialog, hide_busy_dialog, remove_unwanted_info_keys
from modules.utils import clean_file_name, string_to_float, to_utf8, safe_string, remove_accents
from modules.utils import local_string as ls
from modules.settings_reader import get_setting, set_setting
from modules import settings
# from modules.utils import logger

window = xbmcgui.Window(10000)

dialog = xbmcgui.Dialog()

default_furk_icon = os.path.join(settings.get_theme(), 'furk.png')

monitor = xbmc.Monitor()

class Sources():
	def __init__(self):
		self.progress_dialog = None
		self.threads = []
		self.providers = []
		self.sources = []
		self.params = {}
		self.prescrape = 'true'
		self.prescrape_scrapers = []
		self.prescrape_threads = []
		self.prescrape_sources = []
		self.remove_scrapers = []
		self.exclude_list = ['furk', 'easynews']
		self.direct_ext_scrapers = ['ororo', 'filepursuit', 'gdrive']
		self.folder_scrapers = ('folder1', 'folder2', 'folder3', 'folder4', 'folder5')
		self.file_scrapers = ('folder1', 'folder2', 'folder3', 'folder4', 'folder5')
		self.internal_scrapers = ('furk', 'easynews', 'rd-cloud', 'pm-cloud', 'ad-cloud', 'folder1', 'folder2', 'folder3', 'folder4', 'folder5')
		self.active_scrapers = settings.active_scrapers()
		self.sleep_time = settings.display_sleep_time()
		self.scraper_settings = settings.scraping_settings()
		self.scraper_cancel = False

	def playback_prep(self, params=None):
		self._clear_properties()
		if params: self.params = params
		self.vid_type = self.params['vid_type']
		self.tmdb_id = self.params['tmdb_id']
		self.query = self.params['query']
		self.ep_name = self.params.get('ep_name')
		self.plot = self.params.get('plot')
		self.from_library = self.params.get('library', 'False') == 'True'
		self.prescrape = self.params.get('prescrape', 'true') == 'true'
		self.background = self.params.get('background', 'false') == 'true'
		if 'remove_scrapers' in self.params: self.remove_scrapers = json.loads(self.params['remove_scrapers'])
		if 'prescrape_sources' in self.params: self.prescrape_sources = json.loads(self.params['prescrape_sources'])
		if 'autoplay' in self.params: self.autoplay = self.params.get('autoplay', 'False') == 'True'
		else: self.autoplay = settings.auto_play()
		if 'season' in self.params: self.season = int(self.params['season'])
		else: self.season = ''
		if 'episode' in self.params: self.episode = int(self.params['episode'])
		else: self.episode = ''
		if 'meta' in self.params: self.meta = json.loads(self.params['meta'])
		else: self._grab_meta()
		self.filter_hevc = settings.filter_hevc()
		self.include_prerelease_results = settings.include_prerelease_results()
		self.internal_scraper_order = settings.internal_scraper_order()
		self.language = settings.ext_addon('script.module.tikimeta').getSetting('meta_language')
		display_name = clean_file_name(unquote(self.query)) if self.vid_type == 'movie' else '%s - %dx%.2d' % (self.meta['title'], self.season, self.episode)
		if self.from_library: self.meta.update({'plot': self.plot if self.plot else self.meta.get('plot'), 'from_library': self.from_library, 'ep_name': self.ep_name})
		self.meta.update({'query': self.query, 'vid_type': self.vid_type, 'media_id': self.tmdb_id, 'rootname': display_name, 'tvshowtitle': self.meta['title'],
						  'season': self.season, 'episode': self.episode, 'background': self.background})
		self.search_info = self._search_info()
		window.setProperty('fen_media_meta', json.dumps(self.meta))
		hide_busy_dialog()
		self.get_sources()

	def get_sources(self):
		results = []
		self.active_scrapers = [i for i in self.active_scrapers if not i in self.remove_scrapers]
		if any(x in self.active_scrapers for x in self.internal_scrapers):
			if self.prescrape:
				results = self.pre_scrape_check()
				results = self.filter_results(results)
				results = self.sort_results(results)
				results = self.sort_hevc(results)
		if not results:
			self.prescrape = False
			if 'external' in self.active_scrapers:
				self._check_reset_external_scrapers()
				self.activate_debrid_info()
				self.activate_external_providers()
			results = self.collect_results()
			results = self.filter_results(results)
			results = self.sort_results(results)
			results = self.sort_hevc(results)
			if not results:
				return self._no_results()
		window.setProperty('fen_search_results', json.dumps(results))
		hide_busy_dialog()
		self.play_source()

	def collect_results(self):
		if any(x in self.folder_scrapers for x in self.active_scrapers):
			self.check_folder_scrapers(self.active_scrapers, self.providers, False)
		if 'furk' in self.active_scrapers:
			from scrapers.furk import FurkSource
			self.providers.append(('furk', FurkSource()))
		if 'easynews' in self.active_scrapers:
			from scrapers.easynews import EasyNewsSource
			self.providers.append(('easynews', EasyNewsSource()))
		if 'pm-cloud' in self.active_scrapers:
			from scrapers.pm_cache import PremiumizeSource
			self.providers.append(('pm-cloud', PremiumizeSource()))
		if 'rd-cloud' in self.active_scrapers:
			from scrapers.rd_cache import RealDebridSource
			self.providers.append(('rd-cloud', RealDebridSource()))
		if 'ad-cloud' in self.active_scrapers:
			from scrapers.ad_cache import AllDebridSource
			self.providers.append(('ad-cloud', AllDebridSource()))
		if 'external' in self.active_scrapers:
			from scrapers.external import ExternalSource
			internal_scrapers = self.active_scrapers[:]
			internal_scrapers.remove('external')
			if not internal_scrapers: internal_scrapers = []
			self.providers.append(('external', ExternalSource(self.external_providers, self.debrid_torrent_enabled, self.debrid_valid_hosts, internal_scrapers, self.prescrape_sources, self.progress_dialog)))
		for i in range(len(self.providers)):
			self.threads.append(Thread(target=self.activate_providers, args=(self.providers[i][1],), name=self.providers[i][0]))
		[i.start() for i in self.threads]
		self.sources.extend(self.prescrape_sources)
		if 'external' in self.active_scrapers or self.background:
			[i.join() for i in self.threads]
		else:
			self.scrapers_dialog('internal')
		return self.sources

	def filter_results(self, results):
		quality_filter = self._quality_filter()
		include_furk_in_filter = settings.include_sources_in_filter('include_furk')
		include_easynews_in_filter = settings.include_sources_in_filter('include_easynews')
		include_rdcloud_in_filter = settings.include_sources_in_filter('include_rd-cloud')
		include_pmcloud_in_filter = settings.include_sources_in_filter('include_pm-cloud')
		include_adcloud_in_filter = settings.include_sources_in_filter('include_ad-cloud')
		include_folders_in_filter = settings.include_sources_in_filter('include_folders')
		filter_size = get_setting('results.filter.size')
		include_3D_results = get_setting('include_3d_results')
		if filter_size == 'true':
			include_unknown_size = get_setting('results.include.unknown.size')
			min_size = string_to_float(get_setting('results.size.minimum.movies' if self.vid_type == 'movie' else 'results.size.minimum.episodes'), 0)
			max_size = string_to_float(get_setting('results.size.maximum.movies' if self.vid_type == 'movie' else 'results.size.maximum.episodes'), 200)
		filtered_results = []
		for item in results:
			append_item = False
			if any(x in item for x in self.folder_scrapers) and not include_folders_in_filter: append_item = True
			elif item.get("source") == 'furk' and not include_furk_in_filter: append_item = True
			elif item.get("source") == 'easynews' and not include_easynews_in_filter: append_item = True
			elif item.get("source") == 'rd-cloud' and not include_rdcloud_in_filter: append_item = True
			elif item.get("source") == 'pm-cloud' and not include_pmcloud_in_filter: append_item = True
			elif item.get("source") == 'ad-cloud' and not include_adcloud_in_filter: append_item = True
			elif item.get("quality") in quality_filter: append_item = True
			if filter_size == 'true' and append_item is not False:
				size_key = 'external_size' if item.get('external', False) else 'size'
				if item[size_key] == 0:
					if include_unknown_size == 'true': append_item = True
					else: append_item = False
				elif not min_size < item[size_key] < max_size: append_item = False
			if not include_3D_results == 'true' and append_item is not False:
				if '3D' in item['extraInfo']: append_item = False
			if append_item: filtered_results.append(item)
		return filtered_results

	def sort_results(self, results):
		def _add_keys(item):
			provider = item['scrape_provider']
			if 'folder' in provider: provider = 'files'
			item['quality_rank'] = self._get_quality_rank(item.get("quality", "SD"))
			if provider == 'external':
				item['debrid_rank'] = self._get_debrid_rank(item)
				item['name_rank'] = item['provider']
				item['host_rank'] = self._get_host_rank(item)
				item['internal_rank'] = ['z'] * 10
			else:
				item['debrid_rank'] = 1
				item['name_rank'] = ['1'] * 10
				item['host_rank'] = 1
				item['internal_rank'] = self._get_internal_rank(provider.upper())
				item['external_size'] = 600.0 * 1024
		sort_keys = settings.results_sort_order()
		threads = []
		for item in results: threads.append(Thread(target=_add_keys, args=(item,)))
		[i.start() for i in threads]
		[i.join() for i in threads]
		for item in reversed(sort_keys):
			if item in ('size', 'external_size'): reverse = True
			else: reverse = False
			results = sorted(results, key=lambda k: k[item], reverse=reverse)
		results = self._sort_first(results)
		return results

	def sort_hevc(self, results):
		if self.filter_hevc == 1:
			results = [i for i in results if not 'HEVC' in i['extraInfo']]
		elif self.filter_hevc == 2 and self.autoplay:
			test = [i['extraInfo'] for i in results]
			hevc_list = [i for i in results if '[B]HEVC[/B]' in i['extraInfo']]
			non_hevc_list = [i for i in results if not i in hevc_list]
			results = hevc_list + non_hevc_list
		return results

	def activate_providers(self, function):
		sources = function.results(self.search_info)
		if sources: self.sources.extend(sources)

	def activate_prescrape_providers(self, function):
		sources = function.results(self.search_info)
		if sources: self.prescrape_sources.extend(sources)

	def activate_external_providers(self):
		external_providers = sources()
		if self.debrid_torrent_enabled == []:
			torrent_scrapers = scraperNames('torrents')
			self.exclude_list.extend(torrent_scrapers)
		if self.debrid_valid_hosts == []:
			hoster_scrapers = scraperNames('hosters')
			hoster_scrapers = [i for i in hoster_scrapers if not i in self.direct_ext_scrapers]
			self.exclude_list.extend(hoster_scrapers)
		self.external_providers = [i for i in external_providers if not i[0] in self.exclude_list]

	def activate_debrid_info(self):
		self.debrid_enabled = debrid.debrid_enabled()
		debrid_hoster_enabled = debrid.debrid_type_enabled('hoster', self.debrid_enabled)
		self.debrid_torrent_enabled = debrid.debrid_type_enabled('torrent', self.debrid_enabled)
		self.debrid_valid_hosts = debrid.debrid_valid_hosts(debrid_hoster_enabled)

	def play_source(self):
		if self.from_library and self.background:
			return self.play_execute_nextep()
		if self.background:
			return xbmc.executebuiltin('RunPlugin(%s)' % build_url({'mode': 'play_execute_nextep'}))
		if self.autoplay:
			return self.play_auto()
		return self.display_results()

	def pre_scrape_check(self):
		if self.autoplay:
			if any(x in self.folder_scrapers for x in self.active_scrapers):
				self.check_folder_scrapers(self.active_scrapers, self.prescrape_scrapers, False)
				self.remove_scrapers.extend(self.folder_scrapers)
		else:
			if any(x in self.folder_scrapers for x in self.active_scrapers) and settings.check_prescrape_sources('folders'):
				self.check_folder_scrapers(self.active_scrapers, self.prescrape_scrapers)
				self.remove_scrapers.extend(self.folder_scrapers)
		if 'furk' in self.active_scrapers and settings.check_prescrape_sources('furk'):
			from scrapers.furk import FurkSource
			self.prescrape_scrapers.append(('furk', FurkSource()))
			self.remove_scrapers.append('furk')
		if 'easynews' in self.active_scrapers and settings.check_prescrape_sources('easynews'):
			from scrapers.easynews import EasyNewsSource
			self.prescrape_scrapers.append(('easynews', EasyNewsSource()))
			self.remove_scrapers.append('easynews')
		if 'rd-cloud' in self.active_scrapers and settings.check_prescrape_sources('rd-cloud'):
			from scrapers.rd_cache import RealDebridSource
			self.prescrape_scrapers.append(('rd-cloud', RealDebridSource()))
			self.remove_scrapers.append('rd-cloud')
		if 'pm-cloud' in self.active_scrapers and settings.check_prescrape_sources('pm-cloud'):
			from scrapers.pm_cache import PremiumizeSource
			self.prescrape_scrapers.append(('pm-cloud', PremiumizeSource()))
			self.remove_scrapers.append('pm-cloud')
		if 'ad-cloud' in self.active_scrapers and settings.check_prescrape_sources('ad-cloud'):
			from scrapers.ad_cache import AllDebridSource
			self.prescrape_scrapers.append(('ad-cloud', AllDebridSource()))
			self.remove_scrapers.append('ad-cloud')
		len_prescrape_scrapers = len(self.prescrape_scrapers)
		if len_prescrape_scrapers == 0: return []
		for i in range(len_prescrape_scrapers):
			self.prescrape_threads.append(Thread(target=self.activate_prescrape_providers, args=(self.prescrape_scrapers[i][1],), name=self.prescrape_scrapers[i][0]))
		[i.start() for i in self.prescrape_threads]
		if self.background:
			[i.join() for i in self.prescrape_threads]
		else:
			self.scrapers_dialog('pre_scrape')
		return self.prescrape_sources

	def check_folder_scrapers(self, active_scrapers, append_list, prescrape=True):
		from scrapers.folder_scraper import FolderScraper
		location_setting = '%s.movies_directory' if self.vid_type == 'movie' else '%s.tv_shows_directory'
		for i in active_scrapers:
			if i.startswith('folder'):
				scraper_name = get_setting('%s.display_name' % i)
				if prescrape:
					if settings.check_prescrape_sources('folders'): append_list.append((scraper_name, FolderScraper(i, scraper_name)))
				else: append_list.append((scraper_name, FolderScraper(i, scraper_name)))

	def scrapers_dialog(self, scrape_type):
		def _scraperDialog():
			close_dialog = True
			while not self.progress_dialog.iscanceled():
			# percent = 0
			# while percent < 100:
				try:
					if monitor.abortRequested() is True: return sysexit()
					if self.progress_dialog.iscanceled(): break
					remaining_providers = [x.getName() for x in _threads if x.is_alive() is True]
					source_4k_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality'] == '4K' and not 'uncached' in e]))
					source_1080_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality']  == '1080p' and not 'uncached' in e]))
					source_720_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality'] == '720p' and not 'uncached' in e]))
					source_sd_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality'] in ['SD', 'SCR', 'CAM', 'TELE'] and not 'uncached' in e]))
					source_total_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality'] in ['4K', '1080p', '720p', 'SD', 'SCR', 'CAM', 'TELE'] and not 'uncached' in e]))
					try:
						current_time = time.time()
						current_progress = current_time - start_time
						line1 = '[COLOR %s]%s[/COLOR]' % (int_dialog_highlight, _line1_insert)
						line2 = ('[COLOR %s][B]%s[/B][/COLOR] 4K: %s | 1080p: %s | 720p: %s | SD: %s | Total: %s') % (int_dialog_highlight, _line2_insert, source_4k_label, source_1080_label, source_720_label, source_sd_label, source_total_label)
						if len(remaining_providers) > 3: line3_insert = str(len(remaining_providers))
						else: line3_insert = ', '.join(remaining_providers).upper()
						line3 = remaining_providers_str % line3_insert
						percent = int((current_progress/float(timeout))*100)
						self.progress_dialog.update(max(1, percent), line1, line2, line3)
						if len(remaining_providers) == 0: close_dialog = False; break
						if end_time < current_time: close_dialog = False; break
						time.sleep(self.sleep_time)
					except: pass
				except Exception:
					pass
			if close_dialog: self._kill_progress_dialog()
		hide_busy_dialog()
		timeout = 25
		remaining_providers_str = ls(32676)
		int_dialog_highlight = get_setting('int_dialog_highlight')
		if not int_dialog_highlight or int_dialog_highlight == '': int_dialog_highlight = 'dodgerblue'
		total_format = '[COLOR %s][B]%s[/B][/COLOR]'
		_progress_title = self.meta.get('rootname')
		_threads = self.threads if scrape_type == 'internal' else self.prescrape_threads
		_sources = self.sources if scrape_type == 'internal' else self.prescrape_sources
		_line1_insert = ls(32096) if scrape_type == 'internal' else '%s %s' % (ls(32829), ls(32830))
		_line2_insert = 'Int:' if scrape_type == 'internal' else 'Pre:'
		start_time = time.time()
		end_time = start_time + timeout
		self.progress_dialog = xbmcgui.DialogProgress()
		self.progress_dialog.create(_progress_title, '')
		self.progress_dialog.update(0)
		_scraperDialog()
		# from windows.get_sources import getSources
		# self.progress_dialog = getSources()
		# self.progress_dialog.create('Test', line1='gib1', line2='gib2', line3='gib3')
		# _scraperDialog()

	def display_results(self):
		try: results = json.loads(window.getProperty('fen_search_results'))
		except: results = []
		meta_json = window.getProperty('fen_media_meta')
		meta = json.loads(meta_json)
		xml_file = 'source_results.default.xml'
		win = SourceResults(xml_file, settings.skin_location(),
							results=results, meta=meta, scraper_settings=self.scraper_settings, file_scrapers=self.file_scrapers, prescrape=self.prescrape)
		chosen = win.run()
		action = chosen[0]
		chosen_item = chosen[1]
		del win
		if not action:
			return close_all_dialog()
		if action == 'play':
			if self.prescrape: self._kill_progress_dialog()
			return self.play_file(chosen_item.get('title'), json.dumps([chosen_item]))
		elif self.prescrape and action == 'perform_full_search':
			self.params['prescrape'] = 'false'
			self.params['prescrape_sources'] = json.dumps(self.prescrape_sources)
			self.params['remove_scrapers'] = json.dumps(self.remove_scrapers)
			return self.playback_prep()

	def play_execute_nextep(self):
		try: results = json.loads(window.getProperty('fen_search_results'))
		except: return
		from modules.player import FenPlayer
		meta = json.loads(window.getProperty('fen_media_meta'))
		url = self.play_auto(background=True)
		notification('%s %s S%02dE%02d' % (ls(32801), meta['title'], meta['season'], meta['episode']), 10000, meta['poster'])
		player = xbmc.Player()
		while player.isPlaying():
			xbmc.sleep(100)
		xbmc.sleep(1200)
		if 'plugin://' in url:
			return xbmc.executebuiltin("RunPlugin({0})".format(url))
		FenPlayer().run(url)

	def _no_results(self):
		hide_busy_dialog()
		if self.background:
			return notification('%s %s' % (ls(32801), ls(32760)), 5000)
		notification(ls(32760))
		self._clear_properties()

	def _search_info(self):
		return {'db_type': self.vid_type, 'title': self._get_search_title(), 'year': self._get_search_year(), 'tmdb_id': self.tmdb_id,
				'imdb_id': self.meta.get('imdb_id'), 'season': self.season, 'episode': self.episode, 'premiered': self.meta.get('premiered'),
				'tvdb_id': self.meta.get('tvdb_id'), 'aliases': self._make_alias_dict(self.meta.get('alternative_titles', [])), 'ep_name': self._get_ep_name(),
				'language': self.language}

	def _get_search_title(self):
		if 'search_title' in self.meta:
			if self.language != 'en': search_title = self.meta['original_title']
			else: search_title = self.meta['search_title']
		else: search_title = self.meta['title']
		if '(' in search_title: search_title = search_title.split('(')[0]
		return search_title

	def _get_search_year(self):
		year = self.meta.get('year')
		if self.vid_type == "movie" and 'external' in self.active_scrapers:
			if get_setting('search.enable.yearcheck', 'false') == 'true':
				show_busy_dialog()
				from apis.imdb_api import imdb_movie_year
				try: year = imdb_movie_year(self.meta.get('imdb_id'))
				except: year = self.meta.get('year')
				hide_busy_dialog()
		return year

	def _get_ep_name(self):
		ep_name = None
		if self.vid_type == 'episode':
			try: ep_name = to_utf8(safe_string(remove_accents(self.meta.get('ep_name'))))
			except: ep_name = to_utf8(safe_string(self.meta.get('ep_name')))
		return ep_name

	def _make_alias_dict(self, aliases):
		return json.dumps([{'title': i, 'country': ''} for i in aliases])

	def _quality_filter(self):
		setting = 'results_quality' if not self.autoplay else 'autoplay_quality'
		quality_filter = settings.quality_filter(setting)
		if self.include_prerelease_results: quality_filter += ['SCR', 'CAM', 'TELE']
		return quality_filter

	def _get_quality_rank(self, quality):
		if quality == '4K': return 1
		if quality == '1080p': return 2
		if quality == '720p': return 3
		if quality == 'SD': return 4
		if quality in ['SCR', 'CAM', 'TELE']: return 5
		return 6

	def _get_debrid_rank(self, item):
		try:
			debrid = item['debrid']
			if debrid == self.debrid_enabled[0]: return 2
			if debrid == self.debrid_enabled[1]: return 3
			else: return 4
		except: return 5

	def _get_host_rank(self, item):
		source = item['source'].lower()
		if source == 'torrent':
			cache_provider = item['cache_provider']
			if 'Uncached' in cache_provider:
				return 5
			return 2
		if item.get('debrid', False): return 3
		else: return 4

	def _get_internal_rank(self, provider):
		if self.internal_scraper_order[0] in provider: return ['1'] * 10
		if self.internal_scraper_order[1] in provider: return ['1'] * 11
		if self.internal_scraper_order[2] in provider: return ['1'] * 12
		if self.internal_scraper_order[3] in provider: return ['1'] * 13

	def _sort_first(self, results):
		providers = []
		if settings.sorted_first('sort_rd-cloud_first'): providers.append('rd-cloud')
		if settings.sorted_first('sort_pm-cloud_first'): providers.append('pm-cloud')
		if settings.sorted_first('sort_ad-cloud_first'): providers.append('ad-cloud')
		if settings.sorted_first('sort_folders_first'): providers.extend(self.folder_scrapers)
		for provider in providers:
			try:
				inserts = []
				result = [i for i in results if i['scrape_provider'] == provider]
				for i in result:
					inserts.append(i)
					results.remove(i)
				inserts = sorted(inserts, key=lambda k: k['quality_rank'], reverse=True)
				for i in inserts: results.insert(0, i)
			except: pass
		return results

	def _grab_meta(self):
		import tikimeta
		meta_user_info = tikimeta.retrieve_user_info()
		if self.vid_type == "movie":
			self.meta = tikimeta.movie_meta('tmdb_id', self.tmdb_id, meta_user_info)
			if not 'rootname' in self.meta: self.meta['rootname'] = '{0} ({1})'.format(self.meta['title'], self.meta['year'])
		else:
			self.meta = tikimeta.tvshow_meta('tmdb_id', self.tmdb_id, meta_user_info)
			episodes_data = tikimeta.season_episodes_meta(self.meta['tmdb_id'], self.meta['tvdb_id'], self.season, self.meta['tvdb_summary']['airedSeasons'], self.meta['season_data'], meta_user_info)
			try:
				display_name = '%s - %dx%.2d' % (self.meta['title'], self.season, self.episode)
				episode_data = [i for i in episodes_data if i['episode'] == int(self.episode)][0]
				self.meta.update({'vid_type': 'episode', 'rootname': display_name, 'season': episode_data['season'],
							'episode': episode_data['episode'], 'premiered': episode_data['premiered'], 'ep_name': episode_data['title'],
							'plot': episode_data['plot']})
			except: pass

	def _check_reset_external_scrapers(self):
		def _reset_scrapers():
			try:
				toggle_all('all', 'true', silent=True)
				external_scrapers_reset_stats(silent=True)
				notification('%s %s %s' % (ls(32129), ls(32533), ls(32531)), 3000)
				xbmc.sleep(250)
			except:
				pass
		def _get_timestamp(date_time):
			return int(time.mktime(date_time.timetuple()))
		try:
			if get_setting('remove.failing_scrapers') != 'true': return
			reset = int(get_setting('failing_scrapers.reset'))
			if reset == 0: return
			if reset in (1,2):
				current_time = _get_timestamp(datetime.now())
				hours = 24 if reset == 1 else 168
				expiration = timedelta(hours=hours)
				try:
					expires_time = int(get_setting('failing_scrapers.reset_time'))
				except:
					expires_time = _get_timestamp(datetime.now() + expiration)
					return set_setting('failing_scrapers.reset_time', str(expires_time))
				if current_time < expires_time: return
				expires_time = _get_timestamp(datetime.now() + expiration)
				set_setting('failing_scrapers.reset_time', str(expires_time))
			else:
				current_os_version = settings.ext_addon('script.module.fenomscrapers').getAddonInfo('version')
				saved_os_version = get_setting('fenomscrapers.version')
				if saved_os_version in (None, ''): return set_setting('fenomscrapers.version', str(current_os_version))
				if current_os_version == saved_os_version: return
				set_setting('fenomscrapers.version', str(current_os_version))
			_reset_scrapers()
		except: pass

	def _pack_playback(self, filename, url_dl):
		import re
		from modules.player import FenPlayer
		from modules.source_utils import seas_ep_filter
		meta = json.loads(window.getProperty('fen_media_meta'))
		season, episode = meta['season'], meta['episode']
		if seas_ep_filter(season, episode, filename): FenPlayer().run(url_dl)
		else: FenPlayer().play(url_dl)

	def _clear_properties(self):
		window.clearProperty('fen_search_results')
		for item in self.internal_scrapers:
			window.clearProperty('%s.internal_results' % item)

	def _kill_progress_dialog(self):
		try: self.progress_dialog.close()
		except Exception: pass
		del self.progress_dialog
		self.progress_dialog = None

	def furkTFile(self, file_name, file_id):
		from apis.furk_api import FurkAPI
		show_busy_dialog()
		t_files = FurkAPI().t_files(file_id)
		t_files = [i for i in t_files if 'video' in i['ct'] and 'bitrate' in i]
		hide_busy_dialog()
		display_list = ['%02d | [B]%.2f GB[/B] | [I]%s[/I]' % \
						(count,
						float(i['size'])/1073741824,
						clean_file_name(i['name']).upper())
						for count, i in enumerate(t_files, 1)]
		chosen = dialog.select(file_name, display_list)
		if chosen < 0: return None
		chosen_result = t_files[chosen]
		link = chosen_result['url_dl']
		name = chosen_result['name']
		return self._pack_playback(name, link)

	def debridPacks(self, debrid_provider, name, magnet_url, info_hash):
		if debrid_provider == 'Real-Debrid':
			from apis.real_debrid_api import RealDebridAPI as debrid_function
		elif debrid_provider == 'Premiumize.me':
			from apis.premiumize_api import PremiumizeAPI as debrid_function
		elif debrid_provider == 'AllDebrid':
			from apis.alldebrid_api import AllDebridAPI as debrid_function
		show_busy_dialog()
		debrid_files = None
		try: debrid_files = debrid_function().display_magnet_pack(magnet_url, info_hash)
		except: pass
		hide_busy_dialog()
		if not debrid_files:
			return notification(ls(32574))
		debrid_files = sorted(debrid_files, key=lambda k: k['filename'].lower())
		display_list = ['%02d | [B]%.2f GB[/B] | [I]%s[/I]' % \
						(count,
						float(i['size'])/1073741824,
						clean_file_name(i['filename']).upper())
						for count, i in enumerate(debrid_files, 1)]
		chosen = dialog.select(name, display_list)
		if chosen < 0: return None
		chosen_result = debrid_files[chosen]
		url_dl = chosen_result['link']
		if debrid_provider in ('Real-Debrid', 'AllDebrid'):
			link = debrid_function().unrestrict_link(url_dl)
		elif debrid_provider == 'Premiumize.me':
			link = debrid_function().add_headers_to_url(url_dl)
		name = chosen_result['filename']
		return self._pack_playback(name, link)

	def play_file(self, title, source):
		from modules.player import FenPlayer
		def _uncached_confirm(item):
			if not dialog.yesno('Fen', ls(32831) % item['debrid'].upper()):
				return None
			else:
				self.caching_confirmed = True
				return item
		try:
			next = []
			prev = []
			total = []
			results = json.loads(window.getProperty('fen_search_results'))
			results = [i for i in results if not 'Uncached' in i.get('cache_provider', '') or i == json.loads(source)[0]]
			source_index = results.index(json.loads(source)[0])
			for i in range(1, 25):
				try:
					u = results[i+source_index]
					if u in total:
						raise Exception()
					total.append(u)
					next.append(u)
				except Exception:
					break
			for i in range(-25, 0)[::-1]:
				try:
					u = results[i+source_index]
					if u in total:
						raise Exception()
					total.append(u)
					prev.append(u)
				except Exception:
					break
			items = json.loads(source)
			items = [i for i in items+next+prev][:40]
			header = 'Fen'
			progressDialog = xbmcgui.DialogProgress()
			progressDialog.create(header, '')
			progressDialog.update(0)
			block = None
			for i in range(len(items)):
				try:
					self.url = None
					self.caching_confirmed = False
					try:
						if progressDialog.iscanceled(): break
						progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['name'].replace('.', ' ').replace('-', ' ').upper()), str(' '))
					except Exception:
						progressDialog.update(int((100 / float(len(items))) * i), str(header), str(items[i]['name'].replace('.', ' ').replace('-', ' ').upper()))
					if items[i]['source'] == block:
						raise Exception()
					w = Thread(target=self.resolve_sources, args=(items[i],))
					w.start()
					m = ''
					for x in range(3600):
						try:
							if monitor.abortRequested() is True: return sysexit()
							if progressDialog.iscanceled(): return progressDialog.close()
						except Exception: pass
						k = xbmc.getCondVisibility('Window.IsActive(virtualkeyboard)')
						if k:
							m += '1'
							m = m[-1]
						if w.is_alive() is False and not k: break
						k = xbmc.getCondVisibility('Window.IsActive(yesnoDialog)')
						if k:
							m += '1'
							m = m[-1]
						if w.is_alive() is False and not k: break
						time.sleep(0.5)
					for x in range(30):
						try:
							if monitor.abortRequested() is True: return sysexit()
							if progressDialog.iscanceled(): return progressDialog.close()
						except Exception: pass
						if m == '': break
						if w.is_alive() is False: break
						time.sleep(0.5)
					if w.is_alive() is True: block = items[i]['source']
					if self.url == 'uncached':
						self.url = _uncached_confirm(items[i])
						if self.url is None: break
					if self.url is None: raise Exception()
					try: progressDialog.close()
					except Exception: pass
					xbmc.sleep(200)
					if self.url: break
				except Exception: pass
			try: progressDialog.close()
			except Exception: pass
			if self.caching_confirmed:
				return self.resolve_sources(self.url, cache_item=True)
			return FenPlayer().run(self.url)
		except Exception:
			pass

	def play_auto(self, background=False):
		meta = json.loads(window.getProperty('fen_media_meta'))
		items = json.loads(window.getProperty('fen_search_results'))
		items = [i for i in items if not 'Uncached' in i.get('cache_provider', '')]
		filter = [i for i in items if i['source'].lower() in ['hugefiles.net', 'kingfiles.net', 'openload.io', 'openload.co', 'oload.tv', 'thevideo.me', 'vidup.me', 'streamin.to', 'torba.se'] and i['debrid'] == '']
		items = [i for i in items if i not in filter]
		u = None
		if background:
			for i in range(len(items)):
				try:
					if monitor.abortRequested() is True: return sysexit()
					url = self.resolve_sources(items[i])
					if u is None: u = url
					if url is not None: break
				except Exception: pass
			return self.url
		header = 'Fen'
		try:
			progressDialog = xbmcgui.DialogProgress()
			progressDialog.create(header, '')
			progressDialog.update(0)
		except Exception: pass
		for i in range(len(items)):
			try:
				if progressDialog.iscanceled(): break
				progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['name'].replace('.', ' ').replace('-', ' ').upper()), str(' '))
			except Exception:
				progressDialog.update(int((100 / float(len(items))) * i), str(header), str(items[i]['name'].replace('.', ' ').replace('-', ' ').upper()))
			try:
				if monitor.abortRequested() is True: return sysexit()
				url = self.resolve_sources(items[i])
				if 'plugin://' in url:
					try: progressDialog.close()
					except Exception: pass
					hide_busy_dialog()
					return xbmc.executebuiltin("RunPlugin({0})".format(url))
				if u is None: u = url
				if url is not None: break
			except Exception: pass
		try: progressDialog.close()
		except Exception: pass
		hide_busy_dialog()
		try:
			from modules.player import FenPlayer
			FenPlayer().run(self.url)
		except: pass
		return u

	def resolve_sources(self, item, cache_item=False):
		from modules import resolver
		try:
			if 'cache_provider' in item:
				cache_provider = item['cache_provider']
				if 'package' in item:
					meta = json.loads(window.getProperty('fen_media_meta'))
					season, episode, ep_title = meta['season'], meta['episode'], meta['ep_name']
				else: season, episode, ep_title = None, None, None
				if cache_provider in ('Real-Debrid', 'Premiumize.me', 'AllDebrid'):
					url = resolver.resolve_cached_torrents(cache_provider, item['url'], item['hash'], season, episode, ep_title)
					self.url = url
					return url
				if 'Uncached' in cache_provider:
					if cache_item:
						url = resolver.resolve_uncached_torrents(item['debrid'], item['url'], item['hash'], season, episode, ep_title)
						if not url: return None
						if url == 'cache_pack_success': return
						from modules.player import FenPlayer
						return FenPlayer().run(url)
					else:
						url = 'uncached'
						self.url = url
						return url
					return None
			if item.get('scrape_provider', None) in self.internal_scrapers:
				url = resolver.resolve_internal_sources(item['scrape_provider'], item['id'], item['url_dl'], item.get('direct_debrid_link', False))
				self.url = url
				return url
			if item['debrid'] in ('Real-Debrid', 'Premiumize.me', 'AllDebrid') and not item['source'].lower() == 'torrent':
				url = resolver.resolve_debrid(item['debrid'], item['provider'], item['url'])
				if url is not None:
					self.url = url
					return url
				else: return None
			else:
				url = item['url']
				self.url = url
				return url
		except Exception:
			return
