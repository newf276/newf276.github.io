# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
try: from urllib import unquote
except ImportError: from urllib.parse import unquote
import os
from sys import argv
from sys import exit as sysexit
import json
import time
from datetime import datetime, timedelta
from threading import Thread
from modules import debrid
from modules.source_utils import sources, toggle_all, external_scrapers_reset_stats, scraperNames
from indexers.furk import add_uncached_file
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

class Sources:
	def __init__(self):
		self.external_active = False
		self.play_physical = False
		self.suppress_notifications = False
		self.progress_dialog = None
		self.providers = []
		self.sources = []
		self.params = {}
		self.prescrape = 'true'
		self.prescrape_scrapers = []
		self.uncached_results = []
		self.threads = []
		self.prescrape_threads = []
		self.parental_threads = []
		self.restricted_content = []
		self.exclude_list = ['furk', 'easynews', 'library']
		self.direct_ext_scrapers = ['ororo', 'filepursuit', 'gdrive']
		self.folder_scrapers = ('folder1', 'folder2', 'folder3', 'folder4', 'folder5')
		self.file_scrapers = ('local', 'downloads', 'folder1', 'folder2', 'folder3', 'folder4', 'folder5')
		self.internal_scrapers = ('furk', 'easynews', 'rd-cloud', 'pm-cloud', 'ad-cloud', 'local', 'downloads', 'folder1', 'folder2', 'folder3', 'folder4', 'folder5')
		self.display_mode = settings.display_mode()
		self.active_scrapers = settings.active_scrapers()
		self.sleep_time = settings.display_sleep_time()

	def playback_prep(self, params=None):
		self._clear_properties()
		if params: self.params = params
		self.vid_type = self.params['vid_type']
		self.tmdb_id = self.params['tmdb_id']
		self.query = self.params['query']
		if 'season' in self.params: self.season = int(self.params['season'])
		else: self.season = ''
		if 'episode' in self.params: self.episode = int(self.params['episode'])
		else: self.episode = ''
		self.ep_name = self.params.get('ep_name')
		self.plot = self.params.get('plot')
		if 'meta' in self.params: self.meta = json.loads(self.params['meta'])
		else: self._grab_meta()
		self.from_library = self.params.get('library', 'False') == 'True'
		self.prescrape = self.params.get('prescrape', 'true') == 'true'
		self.parental_check_completed = self.params.get('parental_check_completed', 'false') == 'true'
		self.background = self.params.get('background', 'false') == 'true'
		if 'autoplay' in self.params: self.autoplay = self.params.get('autoplay', 'False') == 'True'
		else: self.autoplay = settings.auto_play()
		if 'remove_scrapers' in self.params: self.remove_scrapers = json.loads(self.params['remove_scrapers'])
		else: self.remove_scrapers = []
		if 'prescrape_sources' in self.params: self.prescrape_sources = json.loads(self.params['prescrape_sources'])
		else: self.prescrape_sources = []
		self.autoplay_nextep = self.params.get('autoplay_nextep', 'False') == 'True'
		self.minimal_notifications = settings.minimal_notifications()
		self.dialog_background = True if self.autoplay and self.minimal_notifications \
							else True if 'random_play' in self.meta \
							else False
		self.suppress_notifications = True if self.background or self.dialog_background else False
		self.widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
		self.action = 'Container.Update(%s)' if not self.widget else 'RunPlugin(%s)'
		self.filter_hevc = settings.filter_hevc()
		self.include_prerelease_results = settings.include_prerelease_results()
		self.include_uncached_results = settings.include_uncached_results()
		self.internal_scraper_order = settings.internal_scraper_order()
		self.language = settings.ext_addon('script.module.tikimeta').getSetting('meta_language')
		display_name = clean_file_name(unquote(self.query)) if self.vid_type == 'movie' else '%s - %dx%.2d' % (self.meta['title'], self.season, self.episode)
		if self.from_library: self.meta.update({'plot': self.plot if self.plot else self.meta.get('plot'), 'from_library': self.from_library, 'ep_name': self.ep_name})
		self.meta.update({'query': self.query, 'vid_type': self.vid_type, 'media_id': self.tmdb_id, 'rootname': display_name, 'tvshowtitle': self.meta['title'],
						  'season': self.season, 'episode': self.episode, 'background': self.background, 'dialog_background': self.dialog_background})
		self.search_info = self._search_info()
		window.setProperty('fen_media_meta', json.dumps(self.meta))
		self.get_sources()

	def get_sources(self):
		results = []
		self.active_scrapers = [i for i in self.active_scrapers if not i in self.remove_scrapers]
		if not self._parental_control_check():
			self.prescrape = False
			return self._no_results()
		if any(x in self.active_scrapers for x in self.internal_scrapers):
			if self.prescrape:
				results = self.pre_scrape_check()
				results = self.filter_results(results)
				results = self.sort_results(results)
				results = self._sort_hevc(results)
				results = self.enumerate_labels(results)
		if not results:
			self.prescrape = False
			if 'external' in self.active_scrapers:
				self._check_reset_external_scrapers()
				self.activate_debrid_info()
				self.activate_external_providers()
			results = self.collect_results()
			results = self._sort_hevc(results)
			results = self.filter_results(results)
			results = self.sort_results(results)
			if not results:
				return self._no_results()
			if self.include_uncached_results:
				results += self.uncached_results
			results = self.enumerate_labels(results)
		window.setProperty('fen_search_results', json.dumps(results))
		hide_busy_dialog()
		self.play_source()

	def collect_results(self):
		if any(x in self.folder_scrapers for x in self.active_scrapers):
			self.check_folder_scrapers(self.active_scrapers, self.providers, False)
		if 'local' in self.active_scrapers:
			from scrapers.local_library import LocalLibrarySource
			self.providers.append(('local', LocalLibrarySource()))
		if 'downloads' in self.active_scrapers:
			from scrapers.downloads import DownloadsSource
			self.providers.append(('downloads', DownloadsSource()))
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
			if 'external' in self.active_scrapers:
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
		cached_results = [i for i in results if not 'uncached' in i]
		self.uncached_results = [i for i in results if 'uncached' in i]
		quality_filter = self._quality_filter()
		include_local_in_filter = settings.include_sources_in_filter('include_local')
		include_downloads_in_filter = settings.include_sources_in_filter('include_downloads')
		include_folders_in_filter = settings.include_sources_in_filter('include_folders')
		filter_size = get_setting('results.filter.size')
		include_3D_results = get_setting('include_3d_results')
		if filter_size == 'true':
			include_unknown_size = get_setting('results.include.unknown.size')
			min_size = string_to_float(get_setting('results.size.minimum.movies' if self.vid_type == 'movie' else 'results.size.minimum.episodes'), 0)
			max_size = string_to_float(get_setting('results.size.maximum.movies' if self.vid_type == 'movie' else 'results.size.maximum.episodes'), 200)
		results = []
		for item in cached_results:
			append_item = False
			if any(x in item for x in self.folder_scrapers) and not include_folders_in_filter: append_item = True
			elif item.get("local") and not include_local_in_filter: append_item = True
			elif item.get("downloads") and not include_downloads_in_filter: append_item = True
			elif item.get("quality") in quality_filter: append_item = True
			if filter_size == 'true' and append_item is not False:
				size_key = 'external_size' if item.get('external', False) else 'size'
				if item[size_key] == 0:
					if include_unknown_size == 'true': append_item = True
					else: append_item = False
				elif not min_size < item[size_key] < max_size: append_item = False
			if not include_3D_results == 'true' and append_item is not False:
				info = item['info'] if 'info' in item else item['label']
				if '3D' in info: append_item = False
			if append_item: results.append(item)
		return results

	def sort_results(self, results):
		def _add_keys(item):
			provider = item['scrape_provider']
			if provider in ('local', 'downloads') or 'folder' in provider: provider = 'files'
			item['quality_rank'] = self._get_quality_rank(item.get("quality", "SD"))
			if provider == 'external':
				item['name_rank'] = item['provider']
				item['host_rank'] = self._get_host_rank(item)
				item['internal_rank'] = ['z'] * 10
			else:
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
		debrid_enabled = debrid.debrid_enabled()
		debrid_hoster_enabled = debrid.debrid_type_enabled('hoster', debrid_enabled)
		self.debrid_torrent_enabled = debrid.debrid_type_enabled('torrent', debrid_enabled)
		self.debrid_valid_hosts = debrid.debrid_valid_hosts(debrid_hoster_enabled)

	def enumerate_labels(self, results):
		try:
			for n, i in enumerate(results, 1):
				i['label'] = '%s. %s' % (str(n).zfill(3), i['label'])
				i['multiline_label'] = '%s. %s' % (str(n).zfill(3), i['multiline_label'])
		except: pass
		return results

	def deenumerate_labels(self, sources):
		try:
			for n, i in enumerate(sources, 1):
				i['label'] = i['label'].lstrip('0123456789. ')
				i['multiline_label'] = i['multiline_label'].lstrip('0123456789. ')
		except: pass
		return sources

	def play_source(self):
		if self.from_library and self.background:
			return self.play_execute_nextep('True' if self.autoplay_nextep else 'False', 'True')
		if self.background:
			return xbmc.executebuiltin(self.action % build_url({'mode': 'play_execute_nextep', 'autoplay_nextep': self.autoplay_nextep, 'library': self.from_library}))
		if self.play_physical or self.autoplay:
			return self.play_auto()
		if self.from_library or self.widget:
			return self.dialog_results()
		return self.display_results()

	def pre_scrape_check(self):
		if self.autoplay:
			if 'local' in self.active_scrapers:
				from scrapers.local_library import LocalLibrarySource
				self.prescrape_scrapers.append(('local', LocalLibrarySource()))
				self.remove_scrapers.append('local')
			if 'downloads' in self.active_scrapers:
				from scrapers.downloads import DownloadsSource
				self.prescrape_scrapers.append(('downloads', DownloadsSource()))
				self.remove_scrapers.append('downloads')
			if any(x in self.folder_scrapers for x in self.active_scrapers):
				self.check_folder_scrapers(self.active_scrapers, self.prescrape_scrapers, False)
				self.remove_scrapers.extend(self.folder_scrapers)
		else:
			if 'local' in self.active_scrapers and settings.check_prescrape_sources('local'):
				from scrapers.local_library import LocalLibrarySource
				self.prescrape_scrapers.append(('local', LocalLibrarySource()))
				self.remove_scrapers.append('local')
			if 'downloads' in self.active_scrapers and settings.check_prescrape_sources('downloads'):
				from scrapers.downloads import DownloadsSource
				self.prescrape_scrapers.append(('downloads', DownloadsSource()))
				self.remove_scrapers.append('downloads')
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
				try:
					if monitor.abortRequested() is True: return sysexit()
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
		def _scraperDialogBG():
			while not monitor.abortRequested() is True:
				try:
					remaining_providers = [x.getName() for x in _threads if x.is_alive() is True]
					source_4k_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality'] == '4K' and  not 'uncached' in e]))
					source_1080_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality']  == '1080p' and  not 'uncached' in e]))
					source_720_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality'] == '720p' and  not 'uncached' in e]))
					source_sd_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality'] in ['SD', 'SCR', 'CAM', 'TELE'] and not 'uncached' in e]))
					source_total_label = total_format % (int_dialog_highlight, len([e for e in _sources if e['quality'] in ['4K', '1080p', '720p', 'SD', 'SCR', 'CAM', 'TELE'] and not 'uncached' in e]))
					try:
						current_time = time.time()
						current_progress = current_time - start_time
						if len(remaining_providers) == 0: break
						if end_time < current_time: break
						line1 = remaining_providers_str % str(len(remaining_providers))
						line2 = '4K:%s|1080p:%s|720p:%s|SD:%s|T:%s' % (source_4k_label, source_1080_label, source_720_label, source_sd_label, source_total_label)
						percent = int((current_progress/float(timeout))*100)
						self.progress_dialog.update(max(1, percent), line1, line2)
					except: pass
					time.sleep(self.sleep_time)
				except Exception:
					pass
			self._kill_progress_dialog()
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
		if self.suppress_notifications:
			self.progress_dialog = xbmcgui.DialogProgressBG()
			function = _scraperDialogBG
		else:
			self.progress_dialog = xbmcgui.DialogProgress()
			function = _scraperDialog
		start_time = time.time()
		end_time = start_time + timeout
		self.progress_dialog.create(_progress_title, '')
		self.progress_dialog.update(0)
		function()

	def display_results(self, page_no=None, previous_nav=None):
		def _build_simple_directory():
			for item in results:
				try:
					cm = []
					title = item.get('title')
					item_id = item.get('id', None)
					uncached = item.get('uncached', False)
					mode = 'furk.add_uncached_file' if uncached else 'play_file'
					source = json.dumps([item])
					url = build_url({'mode': mode, 'name': title, 'title': title, 'id': item_id, 'source': source})
					try: listitem = xbmcgui.ListItem(item.get("label"), offscreen=True)
					except: listitem = xbmcgui.ListItem(item.get("label"))
					listitem.setArt({'poster': poster})
					if paginate_results:
						return_from_pagination_params = {'mode': 'play_return_from_pagination', 'previous_nav': previous_nav}
						cm.append((exit_str,'XBMC.RunPlugin(%s)' % build_url(return_from_pagination_params)))
					listitem.addContextMenuItems(cm)
					yield (url, listitem, False)
				except: pass
		def _build_directory():
			for item in results:
				try:
					title = item.get('title')
					item_id = item.get('id', None)
					scrape_provider = item['scrape_provider']
					cache_provider = item.get('cache_provider', '')
					uncached_furk = True if scrape_provider == 'furk' and 'uncached' in item else False
					uncached_torrent = True if 'Uncached' in cache_provider else False
					uncached = True if True in (uncached_furk, uncached_torrent) else False
					mode = 'furk.add_uncached_file' if uncached_furk else 'play_file'
					source = json.dumps([item])
					url = build_url({'mode': mode, 'name': title, 'title': title, 'id': item_id, 'source': source})
					name = item.get('name')
					url_dl = item.get('url_dl')

					cm = []
					if multiline_label: display = item.get("multiline_label")
					else: display = item.get("label")
					try: listitem = xbmcgui.ListItem(display, offscreen=True)
					except: listitem = xbmcgui.ListItem(display)
					if paginate_results:
						return_from_pagination_params = {'mode': 'play_return_from_pagination', 'previous_nav': previous_nav}
						cm.append((exit_str,'RunPlugin(%s)' % build_url(return_from_pagination_params)))
					
					if not uncached:
						if scrape_provider not in self.file_scrapers:

							down_file_params = {'mode': 'downloader',
												'action': 'meta.single',
												'name': rootname,
												'source': source,
												'url': None,
												'provider': scrape_provider,
												'meta': meta_json}
							
							cm.append((down_str, 'RunPlugin(%s)' % build_url(down_file_params)))

							if 'package' in item:
								browse_debrid_pack_params = {'mode': 'browse_debrid_pack',
															'provider': cache_provider,
															'name': name,
															'magnet_url': item['url'],
															'info_hash': item['hash']}

								down_arch_params = {'mode': 'downloader',
												'action': 'meta.pack',
												'name': rootname,
												'source': source,
												'url': None,
												'provider': scrape_provider,
												'meta': meta_json}
								
								# cm.append((down_archive_str, 'RunPlugin(%s)' % build_url(down_arch_params)))
								cm.append((browse_debrid_str, 'RunPlugin(%s)'  % build_url(browse_debrid_pack_params)))
							
							elif scrape_provider == 'furk':
								if 'PACK' in display:
									browse_pack_params = {'mode': 'furk.browse_packs',
														'file_name': name,
														'file_id': item_id}
									
									down_arch_params = {'mode': 'downloader',
													'db_type': 'furk.pack',
													'action': 'furk.pack',
													'name': rootname,
													'source': source,
													'url': url_dl,
													'provider': scrape_provider,
													'image': default_furk_icon}
									
									add_files_params = {'mode': 'furk.add_to_files',
														'name': name,
														'item_id': item_id}
									
									cm.append((down_archive_str,'RunPlugin(%s)' % build_url(down_arch_params)))
									cm.append((browse_str, 'RunPlugin(%s)'  % build_url(browse_pack_params)))
									cm.append((addto_str, 'RunPlugin(%s)'  % build_url(add_files_params)))

					listitem.setInfo('video', info_meta)
					listitem.setArt({'poster': poster, 'fanart': fanart, 'icon': poster, 'banner': banner, 'clearart': clearart, 'clearlogo': clearlogo, 'landscape': landscape, 'discart': discart})
					listitem.addContextMenuItems(cm)
					yield (url, listitem, False)
				except: pass
		try: results = json.loads(window.getProperty('fen_search_results'))
		except: results = []
		down_str, exit_str, browse_str, browse_debrid_str, addto_str, down_archive_str = ls(32747), ls(32810), ls(32811), ls(33004), ls(32769), ls(32982)
		paginate_results = get_setting('results.paginate') == 'true'
		if paginate_results and results:
			from modules.nav_utils import paginate_list
			if not previous_nav: previous_nav = xbmc.getInfoLabel('Container.FolderPath')
			try: limit = int(get_setting('results.page_limit'))
			except: limit = 100
			if not page_no: page_no = 1
			page_no = int(page_no)
			next_page = page_no + 1
			results, total_pages = paginate_list(results, page_no, 'None', limit)
			if page_no > 1: self.prescrape = False
		meta_json = window.getProperty('fen_media_meta')
		meta = json.loads(meta_json)
		poster, fanart, banner, clearart = meta['poster'], meta['fanart'], meta['banner'], meta['clearart']
		clearlogo, landscape, discart = meta['clearlogo'], meta['landscape'], meta['discart']
		rootname, plot = meta.get('rootname', ''), meta['plot']
		info_meta = remove_unwanted_info_keys(meta)
		entries_to_remove = ('playcount', 'overlay', 'duration')
		for k in entries_to_remove:
			info_meta.pop(k, None)
		multiline_label = settings.multiline_results()
		build_results = _build_simple_directory if self.display_mode == 1 else _build_directory
		item_list = list(build_results())
		xbmcplugin.addDirectoryItems(int(argv[1]), item_list)
		try:
			if self.prescrape:
				self.params['prescrape'] = 'false'
				self.params['parental_check_completed'] = 'true'
				self.params['prescrape_sources'] = json.dumps(self.deenumerate_labels(self.prescrape_sources))
				self.params['remove_scrapers'] = json.dumps(self.remove_scrapers)
				scrape_url = build_url({'mode': 'play_media', 'params': json.dumps(self.params)})
				listitem = xbmcgui.ListItem('[B]***%s***[/B]' % ls(33023).upper())
				listitem.setArt({'poster': poster, 'fanart': fanart, 'icon': poster, 'banner': banner, 'clearart': clearart, 'clearlogo': clearlogo, 'landscape': landscape, 'discart': discart})
				listitem.setInfo('video', info_meta)
				xbmcplugin.addDirectoryItem(handle=int(argv[1]), url=scrape_url, listitem=listitem, isFolder=True)
		except: pass
		if paginate_results and results:
			if limit == len(results):
				next_page_url = build_url({'mode': 'play_display_results', 'page_no': str(next_page), 'previous_nav': previous_nav})
				listitem = xbmcgui.ListItem('[B]%s[/B]' % ls(32799))
				listitem.setArt({'icon': os.path.join(settings.get_theme(), 'item_next.png'), 'banner': banner, 'clearart': clearart, 'clearlogo': clearlogo, 'landscape': landscape, 'discart': discart})
				listitem.setInfo('video', info_meta)
				xbmcplugin.addDirectoryItem(handle=int(argv[1]), url=next_page_url, listitem=listitem, isFolder=True)
		xbmcplugin.setContent(int(argv[1]), 'files')
		xbmcplugin.endOfDirectory(int(argv[1]))
		setView('view.search_results')

	def dialog_results(self):
		def _process():
			for item in results:
				try: listitem = xbmcgui.ListItem(item.get(label), offscreen=True)
				except: listitem = xbmcgui.ListItem(item.get(label))
				listitem.setProperty('IsPlayable', 'false')
				yield listitem
		hide_busy_dialog()
		close_all_dialog()
		multiline_label = settings.multiline_results()
		label = 'multiline_label' if multiline_label else 'label'
		results = json.loads(window.getProperty('fen_search_results'))
		try:
			if self.prescrape:
				self.params['prescrape'] = 'false'
				self.params['parental_check_completed'] = 'true'
				self.params['prescrape_sources'] = json.dumps(self.deenumerate_labels(self.prescrape_sources))
				self.params['remove_scrapers'] = json.dumps(self.remove_scrapers)
				line1 = '[B]***%s***[/B]' % ls(33023).upper()
				results.append({'label': line1, 'multiline_label': line1, 'perform_full_search': 'true'})
		except: pass
		item_list = list(_process())
		chosen = dialog.select('Fen', item_list)
		if chosen < 0: return
		chosen_result = results[chosen]
		if self.prescrape:
			self._kill_progress_dialog()
		if 'perform_full_search' in chosen_result:
			return self.playback_prep()
		if chosen_result.get('uncached', False):
			return add_uncached_file(chosen_result.get('name'), chosen_result.get('id'))
		return self.play_file(chosen_result.get('title'), json.dumps([chosen_result]))

	def return_from_pagination(self, previous_nav):
		return xbmc.executebuiltin('Container.Update(%s,replace)' % previous_nav)

	def play_execute_nextep(self, autoplay_nextep, from_library):
		self.autoplay_nextep = autoplay_nextep == 'True'
		from_library = from_library == 'True'
		try: results = json.loads(window.getProperty('fen_search_results'))
		except: return
		from modules.player import FenPlayer
		meta = json.loads(window.getProperty('fen_media_meta'))
		if self.autoplay_nextep:
			url = self.play_auto(background=True)
			line = ls(32801)
		else: line = ls(33044)
		notification('%s %s S%02dE%02d' % (line, meta['title'], meta['season'], meta['episode']), 10000, meta['poster'])
		player = xbmc.Player()
		while player.isPlaying():
			xbmc.sleep(100)
		if self.autoplay_nextep:
			xbmc.sleep(1200)
			if 'plugin://' in url:
				return xbmc.executebuiltin("RunPlugin({0})".format(url))
			FenPlayer().run(url)
		else:
			if not settings.advancescrape_show_results(): return
			xbmc.sleep(2500)
			widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
			if widget or from_library:
				return self.dialog_results()
			else:
				return xbmc.executebuiltin('Container.Update(%s)' % build_url({'mode': 'play_display_results'}))

	def _no_results(self):
		hide_busy_dialog()
		if self.background:
			return notification('%s %s' % (ls(32801), ls(32760)), 5000)
		notification(ls(32760))
		self._clear_properties()
		return self.display_results()

	def _parental_control_check(self):
		def _get_parental_guide():
			levels = {'mild': 0, 'moderate': 1, 'severe': 2}
			sex_limit = int(get_setting('parentcontrols.sex', '0'))
			violence_limit = int(get_setting('parentcontrols.violence', '0'))
			language_limit = int(get_setting('parentcontrols.language', '0'))
			drugs_limit = int(get_setting('parentcontrols.drugs', '0'))
			fright_limit = int(get_setting('parentcontrols.fright', '0'))
			pcc_settings = {'sex & nudity': sex_limit, 'violence & gore': violence_limit, 'profanity': language_limit,
						  'alcohol, drugs & smoking': drugs_limit, 'frightening & intense scenes': fright_limit}
			parental_info = imdb_parentsguide(self.meta['imdb_id'])
			for item in parental_info:
				if levels[item['ranking'].lower()] > pcc_settings[item['title'].lower()]:
					self.restricted_content.append(item['title'].upper())
		def _scraperDialog():
			close_dialog = True
			while not progress_dialog.iscanceled():
				try:
					if monitor.abortRequested() is True: return sysexit()
					alive_threads = [x for x in self.parental_threads if x.is_alive() is True]
					try:
						current_time = time.time()
						current_progress = current_time - start_time
						percent = int((current_progress/float(timeout))*100)
						progress_dialog.update(max(1, percent))
						if len(alive_threads) == 0: break
						if end_time < current_time: break
						time.sleep(0.1)
					except: pass
				except Exception:
					pass
			try: progress_dialog.close()
			except Exception: pass
		if get_setting('parentcontrols.active') in ('false', ''): return True
		if self.parental_check_completed: return True
		if not self.meta['imdb_id']:
			notification('%s %s' % (ls(32999), ls(32574)), time=2000)
			return True
		from apis.imdb_api import imdb_parentsguide
		if not self.suppress_notifications:
			timeout = 10
			start_time = time.time()
			end_time = start_time + timeout
			progress_dialog = xbmcgui.DialogProgress()
			progress_dialog.create(self.meta.get('title', 'Fen'), ls(33002), ls(32577))
			progress_dialog.update(0)
		self.parental_threads.append(Thread(target=_get_parental_guide))
		[i.start() for i in self.parental_threads]
		if self.suppress_notifications:
			[i.join() for i in self.parental_threads]
		else:
			_scraperDialog()
		if self.restricted_content:
			if get_setting('parentcontrols.confirm') == 'true' and not self.suppress_notifications:
				if not dialog.yesno('Fen', ls(32995) % (self.meta['title'], ', '.join(self.restricted_content))): return False
				else: return True
			else: dialog.ok('Fen', '[B]%s:[/B]' % ls(32736), ', '.join(self.restricted_content)); return False
		return True

	def _search_info(self):
		return {'db_type': self.vid_type, 'title': self._get_search_title(), 'year': self._get_search_year(), 'tmdb_id': self.tmdb_id,
				'imdb_id': self.meta.get('imdb_id'), 'season': self.season, 'episode': self.episode, 'premiered': self.meta.get('premiered'),
				'tvdb_id': self.meta.get('tvdb_id'), 'aliases': self._make_alias_dict(self.meta.get('alternative_titles', [])), 'ep_name': self._get_ep_name(),
				'language': self.language, 'scraper_settings': json.dumps(settings.scraping_settings())}

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

	def _get_debrid_rank(self, debrid):
		if debrid != '': return 2
		else: return 3

	def _get_host_rank(self, item):
		source = item['source'].lower()
		if source == 'torrent':
			cache_provider = item['cache_provider']
			if cache_provider == 'Unchecked':
				return 4
			if 'Uncached' in cache_provider:
				return 3
			return 2
		if item.get('debrid', False): return 5
		else: return 6

	def _get_internal_rank(self, provider):
		if self.internal_scraper_order[0] in provider: return ['1'] * 10
		if self.internal_scraper_order[1] in provider: return ['1'] * 11
		if self.internal_scraper_order[2] in provider: return ['1'] * 12
		if self.internal_scraper_order[3] in provider: return ['1'] * 13

	def _sort_hevc(self, results):
		if self.filter_hevc == 1:
			results = [i for i in results if not 'HEVC' in i['label']]
		elif self.filter_hevc == 2 and self.autoplay:
			hevc_list = [i for i in results if 'HEVC' in i['label']]
			non_hevc_list = [i for i in results if not i in hevc_list]
			results = hevc_list + non_hevc_list
		return results

	def _sort_first(self, results):
		providers = []
		if settings.sorted_first('sort_rd-cloud_first'): providers.append('rd-cloud')
		if settings.sorted_first('sort_pm-cloud_first'): providers.append('pm-cloud')
		if settings.sorted_first('sort_ad-cloud_first'): providers.append('ad-cloud')
		if settings.sorted_first('sort_folders_first'): providers.extend(self.folder_scrapers)
		if settings.sorted_first('sort_downloads_first'): providers.append('downloads')
		if settings.sorted_first('sort_local_first'): providers.append('local')
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
		window.setProperty('fen_fanart_error', 'true')
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
			results = [i for i in results if not i.get('uncached', False)]
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
						progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
					except Exception:
						progressDialog.update(int((100 / float(len(items))) * i), str(header), str(items[i]['label']))
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
		items = [i for i in items if not i.get('uncached', False)]
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
		if not self.suppress_notifications:
			self.suppress_notifications = True if (get_setting('auto_play'), get_setting('autoplay_minimal_notifications')) == ('true', 'true') else False
		if self.suppress_notifications:
			for i in range(len(items)):
				try:
					if monitor.abortRequested() is True: return sysexit()
					url = self.resolve_sources(items[i])
					if 'plugin://' in url:
						hide_busy_dialog()
						return xbmc.executebuiltin("RunPlugin({0})".format(url))
					if u is None: u = url
					if url is not None: break
				except Exception: pass
		else:
			header = 'Fen'
			try:
				progressDialog = xbmcgui.DialogProgress()
				progressDialog.create(header, '')
				progressDialog.update(0)
			except Exception: pass
			for i in range(len(items)):
				try:
					if progressDialog.iscanceled(): break
					progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
				except Exception:
					progressDialog.update(int((100 / float(len(items))) * i), str(header), str(items[i]['label']))
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
				if cache_provider == 'Unchecked':
					url = resolver.resolve_unchecked_torrents(item['debrid'], item['url'], item['hash'], season, episode, ep_title)
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
