# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import os
import sys
import re
import json
import time
import datetime
from importlib import import_module
from threading import Thread
try: from sqlite3 import dbapi2 as database
except Exception: from pysqlite2 import dbapi2 as database
from modules.nav_utils import show_busy_dialog, hide_busy_dialog, notification
from modules.utils import byteify, clean_file_name
from modules.utils import local_string as ls
from modules import source_utils
from modules.settings_reader import get_setting
from modules.settings import ext_addon, display_sleep_time
# from modules.utils import logger

window = xbmcgui.Window(10000)
monitor = xbmc.Monitor()

class ExternalSource:
	def __init__(self, sourceDict, debrid_torrents, debrid_hosters, internal_scrapers, prescrape_sources, progressDialog=None):
		self.scrape_provider = 'external'
		self.sourceDict = sourceDict
		self.debrid_torrents = debrid_torrents
		self.debrid_hosters = debrid_hosters
		self.internal_scrapers = internal_scrapers
		self.prescrape_sources = prescrape_sources
		self.internal_activated = len(self.internal_scrapers) > 0
		self.internal_prescraped = len(self.prescrape_sources) > 0
		self.processed_prescrape = False
		self.progressDialog = progressDialog
		self.getConstants()

	def results(self, info):
		results = []
		self.info = info
		self.scraper_settings = json.loads(info['scraper_settings'])
		results = self.getSources((info['title'] if info['db_type'] == 'movie' else info['ep_name']),
							info['year'], info['imdb_id'], info['tvdb_id'], info['season'], info['episode'],
							(info['title'] if info['db_type'] == 'episode' else None), info['premiered'], info['language'], info['aliases'])
		return results

	def getSources(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, language, aliases):
		def _scraperDialog():
			diag_format = ' 4K: %s | 1080p: %s | 720p: %s | SD: %s | %s: %s'
			exonly_diag_format = '4K: %s | 1080p: %s | 720p: %s | SD: %s | %s: %s'
			loaded_scrapers = 0
			close_dialog = True
			start_time = time.time()
			end_time = start_time + timeout
			while not self.progressDialog.iscanceled():
				try:
					if monitor.abortRequested() is True: return sys.exit()
					self.internalResults()
					internalSource_4k_label = total_format % (int_dialog_highlight, self.internalSources4K)
					internalSource_1080_label = total_format % (int_dialog_highlight, self.internalSources1080p)
					internalSource_720_label = total_format % (int_dialog_highlight, self.internalSources720p)
					internalSource_sd_label = total_format % (int_dialog_highlight, self.internalSourcesSD)
					internalSource_total_label = total_format % (int_dialog_highlight, self.internalSourcesTotal)
					source_4k_label = total_format % (ext_dialog_highlight, self.source_4k)
					source_1080_label = total_format % (ext_dialog_highlight, self.source_1080)
					source_720_label = total_format % (ext_dialog_highlight, self.source_720)
					source_sd_label = total_format % (ext_dialog_highlight, self.source_sd)
					source_total_label = total_format % (ext_dialog_highlight, self.total)
					current_time = time.time()
					current_progress = max((current_time - start_time), 0)
					try:
						info = [x.getName() for x in threads if x.is_alive() is True]
						percent = int((current_progress/float(timeout))*100)
						if self.internal_activated or self.internal_prescraped:
							info.extend([i for i in self.internal_scrapers if not i in self.processed_internal_scrapers])
							line1 = string6 + diag_format % (internalSource_4k_label, internalSource_1080_label,
													  internalSource_720_label, internalSource_sd_label, str(string4), internalSource_total_label)
							line2 = string7 + diag_format % (source_4k_label, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
						else:
							line1 = string7
							line2 = exonly_diag_format % (source_4k_label, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
						len_alive_threads = len(info)
						if loaded_scrapers < self.active_scrapers:
							add_time = min(float((self.active_scrapers - loaded_scrapers))/10, 0.5)
							start_time += add_time
							end_time += add_time
							line3 = string_red % str(len_alive_threads)
							loaded_scrapers = self.active_scrapers
						elif len_alive_threads > 6: line3 = string3 % str(len_alive_threads)
						else: line3 = string3 % ', '.join(info).upper()
						self.progressDialog.update(percent, line1, line2, line3)
						if pre_emp == 'true':
							combined_source_4k = self.source_4k + self.internalSources4K
							combined_source_1080 = self.source_1080 + self.internalSources1080p
							combined_source_720 = self.source_720 + self.internalSources720p
							combined_source_sd = self.source_sd + self.internalSourcesSD
							combined_total = self.total + self.internalSourcesTotal
							pre_emp_compare = combined_source_4k if pre_emp_quality == '1' else combined_source_1080 if pre_emp_quality == '2' else \
											  combined_source_720 if pre_emp_quality == '3' else combined_source_sd if pre_emp_quality == '4' else combined_total
							if pre_emp_compare >= pre_emp_limit: close_dialog = False; break
						if finish_early:
							if finish_early_default:
								if percent >= 50:
									if len_alive_threads <= 5: close_dialog = False; break
									if len(self.sources) >= 100 * len_alive_threads: close_dialog = False; break
							else:
								if finish_percent and percent >= finish_percent: close_dialog = False; break
								if finish_scrapers and len_alive_threads <= finish_scrapers: close_dialog = False; break
								if finish_results and len(self.sources) >= finish_results: close_dialog = False; break
						if len_alive_threads == 0: close_dialog = False; break
						if end_time < current_time: close_dialog = False; break
						time.sleep(self.sleep_time)
					except: pass
				except Exception: pass
			if close_dialog:
				try: self.progressDialog.close()
				except Exception: pass
				del self.progressDialog
				self.progressDialog = None
			return
		def _scraperDialogBG():
			diag_format = '4K:%s|1080p:%s|720p:%s|SD:%s|T:%s'
			loaded_scrapers = 0
			start_time = time.time()
			end_time = start_time + timeout
			while not monitor.abortRequested() is True:
				try:
					self.internalResults()
					combined_source_4k = self.source_4k + self.internalSources4K
					combined_source_1080 = self.source_1080 + self.internalSources1080p
					combined_source_720 = self.source_720 + self.internalSources720p
					combined_source_sd = self.source_sd + self.internalSourcesSD
					combined_total = self.total + self.internalSourcesTotal
					source_4k_label = total_format % (ext_dialog_highlight, combined_source_4k)
					source_1080_label = total_format % (ext_dialog_highlight, combined_source_1080)
					source_720_label = total_format % (ext_dialog_highlight, combined_source_720)
					source_sd_label = total_format % (ext_dialog_highlight, combined_source_sd)
					source_total_label = total_format % (ext_dialog_highlight, combined_total)
					current_time = time.time()
					current_progress = current_time - start_time
					try:
						info = [x.getName() for x in threads if x.is_alive() is True]
						if self.internal_activated or self.internal_prescraped: info.extend([i for i in self.internal_scrapers if not i in self.processed_internal_scrapers])
						len_alive_threads = len(info)
						percent = int((current_progress/float(timeout))*100)
						line1 = string3 % (str(len(info)))
						line2 = diag_format % (source_4k_label, source_1080_label, source_720_label, source_sd_label, source_total_label)
						self.progressDialog.update(percent, line1, line2)
						if pre_emp == 'true':
							pre_emp_compare = combined_source_4k if pre_emp_quality == '1' else combined_source_1080 if pre_emp_quality == '2' else \
											  combined_source_720 if pre_emp_quality == '3' else combined_source_sd if pre_emp_quality == '4' else combined_total
							if pre_emp_compare >= pre_emp_limit: break
						if loaded_scrapers < self.active_scrapers:
							add_time = min(float((self.active_scrapers - loaded_scrapers))/10, 0.5)
							start_time += add_time
							end_time += add_time
							loaded_scrapers = self.active_scrapers
						if finish_early:
							if finish_early_default:
								if percent >= 50:
									if len_alive_threads <= 5: break
									if len(self.sources) >= 100 * len_alive_threads: break
							else:
								if finish_percent and percent >= finish_percent: break
								if finish_scrapers and len_alive_threads <= finish_scrapers: break
								if finish_results and len(self.sources) >= finish_results: break
						if len_alive_threads == 0: break
						if end_time < current_time: break
						time.sleep(self.sleep_time)
					except: pass
				except Exception: pass
			try: self.progressDialog.close()
			except Exception: pass
			del self.progressDialog
			self.progressDialog = None
			return
		def _background():
			start_time = time.time()
			end_time = start_time + timeout
			while time.time() < end_time:
				if pre_emp == 'true':
					combined_source_4k = self.source_4k + self.internalSources4K
					combined_source_1080 = self.source_1080 + self.internalSources1080p
					combined_source_720 = self.source_720 + self.internalSources720p
					combined_source_sd = self.source_sd + self.internalSourcesSD
					combined_total = self.total + self.internalSourcesTotal
					pre_emp_compare = combined_source_4k if pre_emp_quality == '1' else combined_source_1080 if pre_emp_quality == '2' else\
									  combined_source_720 if pre_emp_quality == '3' else combined_source_sd if pre_emp_quality == '4' else combined_total
					if pre_emp_compare >= pre_emp_limit: return
				alive_threads = [x.getName() for x in threads if x.is_alive() is True]
				time.sleep(self.sleep_time)
				if len(alive_threads) <= 5: return
				if len(self.sources) >= 100 * len(alive_threads): return
		threads = []
		content = 'movie' if tvshowtitle is None else 'tvshow'
		sourceDict = self.sourceDict
		if content == 'movie':
			title = source_utils.normalize(title)
			for i in range(len(sourceDict)):
				source_display, module_path = sourceDict[i][0], sourceDict[i][1]
				threads.append(Thread(target=self.getMovieSource, args=(title, aliases, year, imdb, source_display, module_path), name=source_display))
		else:
			tvshowtitle = source_utils.normalize(tvshowtitle)
			self.season_packs, self.show_packs = source_utils.pack_enable_check(self.meta, season, episode)
			if self.season_packs:
				sourceDict.extend([('%s (season)' % i[0], i[1], i[0]) for i in sourceDict if i[0] in self.sourceDictPack])
			if self.show_packs: sourceDict.extend([('%s (show)' % i[0], i[1], i[0]) for i in sourceDict if i[0] in self.sourceDictPack])
			for i in range(len(sourceDict)):
				if '(season)' in sourceDict[i][0]: pack_arg, source = 'season', sourceDict[i][2]
				elif '(show)' in sourceDict[i][0]: pack_arg, source = 'show', sourceDict[i][2]
				else: pack_arg, source = None, sourceDict[i][0]
				source_display, module_path = sourceDict[i][0], sourceDict[i][1]
				threads.append(Thread(target=self.getEpisodeSource, args=(title, year, imdb, tvdb, season, episode, tvshowtitle, aliases, premiered, source, module_path, pack_arg), name=source_display))
		pre_emp = get_setting('preemptive.termination')
		pre_emp_quality = get_setting('preemptive.quality')
		pre_emp_limit = int(get_setting('preemptive.limit', '1000'))
		timeout = int(get_setting('scrapers.timeout.1', '60'))
		int_dialog_highlight = get_setting('int_dialog_highlight', 'darkgoldenrod')
		ext_dialog_highlight = get_setting('ext_dialog_highlight', 'dodgerblue')
		finish_early = get_setting('search.finish.early') == 'true'
		if finish_early:
			finish_early_default = get_setting('search.finish.default') == 'true'
			if not finish_early_default:
				finish_percent = min(int(get_setting('search.finish.percent', '0')), 100)
				finish_scrapers = int(get_setting('search.finish.scrapers', '0'))
				finish_results = int(get_setting('search.finish.results', '0'))
		string1, string2, string3, string4, string_red = ls(32674), ls(32675), ls(32676), ls(32677), ls(32832)
		if self.internal_activated or self.internal_prescraped:
			string6 = '[COLOR %s][B]Int:[/B][/COLOR]' % int_dialog_highlight
			string7 = '[COLOR %s][B]Ext:[/B][/COLOR]' % ext_dialog_highlight
		else:
			string7 = '[COLOR %s]%s[/COLOR]' % (ext_dialog_highlight, ls(32118))
		line1 = line2 = line3 = ""
		total_format = '[COLOR %s][B]%s[/B][/COLOR]'
		[i.start() for i in threads]
		if self.background: _background()
		elif self.dialog_background: _scraperDialogBG()
		else: _scraperDialog()
		self.final_sources.extend(self.sources)
		self.sourcesStats(sourceDict, self.final_sources)
		self.sourcesFilter()
		self.sourcesAddInfo()
		self.sourcesLabels()
		return self.final_sources
	
	def getMovieSource(self, title, aliases, year, imdb, source, module_path):
		try:
			dbcon = database.connect(self.providerDatabase, timeout=self.database_timeout)
			dbcur = dbcon.cursor()
			dbcur.execute('''PRAGMA synchronous = OFF''')
			dbcur.execute('''PRAGMA journal_mode = OFF''')
		except Exception: pass
		if imdb == '0':
			try:
				dbcur.execute("DELETE FROM rel_src WHERE source = ? AND imdb_id = ?", (source, imdb))
				dbcon.commit()
			except Exception: pass
		try:
			sources = []
			dbcur.execute("SELECT * FROM rel_src WHERE source = ? AND imdb_id = ?", (source, imdb))
			match = dbcur.fetchone()
			if match:
				if int(match[5]) > self.sourcesTimestamp(self.time):
					sources = eval(byteify(match[4]))
					self.sourcesQualityCount(sources)
					return self.sources.extend(sources)
				else:
					dbcur.execute("DELETE FROM rel_src WHERE imdb_id = ?", (imdb,))
		except Exception: pass
		try:
			module = import_module(module_path)
			call = module.source()
			if not getattr(call, 'movie', None): return
			self.active_scrapers += 1
		except: return
		try:
			url = None
			dbcur.execute("SELECT * FROM rel_url WHERE source = ? AND imdb_id = ?", (source, imdb))
			url = dbcur.fetchone()
			url = eval(byteify(url[4]))
		except Exception: pass
		try:
			if url is None: url = call.movie(imdb, title, aliases, year)
			if url is None: return
			dbcur.execute("DELETE FROM rel_url WHERE source = ? AND imdb_id = ? AND season = ? AND episode = ?", (source, imdb, '', ''))
			dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
			dbcon.commit()
		except Exception: pass
		try:
			expiry_hours = 24
			sources = []
			sources = call.sources(url, self.hostDict)
			sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
			sources = self.sourcesUpdate(source, sources)
			self.sourcesQualityCount(sources)
			self.sources.extend(sources)
			dbcur.execute("DELETE FROM rel_src WHERE source = ? AND imdb_id = ? AND season = ? AND episode = ?", (source, imdb, '', ''))
			dbcur.execute("INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, '', '', repr(sources), self.sourcesTimestamp(self.time + datetime.timedelta(hours=expiry_hours))))
			dbcon.commit()
		except Exception: pass

	def getEpisodeSource(self, title, year, imdb, tvdb, season, episode, tvshowtitle, aliases, premiered, source, module_path, pack):
		if pack in ('season', 'show'):
			if pack == 'show': s_check = ''
			else: s_check = season
			e_check = ''
		else:
			s_check, e_check = season, episode
		try:
			dbcon = database.connect(self.providerDatabase, self.database_timeout)
			dbcur = dbcon.cursor()
			dbcur.execute('''PRAGMA synchronous = OFF''')
			dbcur.execute('''PRAGMA journal_mode = OFF''')
		except Exception: pass
		try:
			sources = []
			dbcur.execute("SELECT * FROM rel_src WHERE source = ? AND imdb_id = ? AND season = ? AND episode = ?", (source, imdb, s_check, e_check))
			match = dbcur.fetchone()
			if match:
				if int(match[5]) > self.sourcesTimestamp(self.time):
					sources = eval(byteify(match[4]))
					if pack == 'show': sources = [i for i in sources if i.get('last_season') >= season]
					self.sourcesQualityCount(sources)
					return self.sources.extend(sources)
				else:
					dbcur.execute("DELETE FROM rel_src WHERE imdb_id = ?", (imdb,))
		except Exception: pass
		try:
			module = import_module(module_path)
			call = module.source()
			if not getattr(call, 'tvshow', None): return
			self.active_scrapers += 1
		except: return
		try:
			url = None
			dbcur.execute("SELECT * FROM rel_url WHERE source = ? AND imdb_id = ? AND season = ? AND episode = ", (source, imdb, '', ''))
			url = dbcur.fetchone()
			url = eval(byteify(url[4]))
		except Exception: pass
		try:
			if url is None: url = call.tvshow(imdb, tvdb, tvshowtitle, aliases, year)
			if url is None: return
			dbcur.execute("DELETE FROM rel_url WHERE source = ? AND imdb_id = ? AND season = ? AND episode = ?", (source, imdb, '', ''))
			dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
			dbcon.commit()
		except Exception: pass
		try:
			ep_url = None
			dbcur.execute("SELECT * FROM rel_url WHERE source = ? AND imdb_id = ? AND season = ? AND episode = ?", (source, imdb, season, episode))
			ep_url = dbcur.fetchone()
			ep_url = eval(byteify(ep_url[4]))
		except Exception: pass
		try:
			if url is None: raise Exception()
			if ep_url is None: ep_url = call.episode(url, imdb, tvdb, title, premiered, season, episode)
			if ep_url is None: return
			dbcur.execute("DELETE FROM rel_url WHERE source = ? AND imdb_id = ? AND season = ? AND episode = ?", (source, imdb, season, episode))
			dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(ep_url)))
			dbcon.commit()
		except Exception: pass
		try:
			sources = []
			if not pack:
				expiry_hours = 24
				sources = call.sources(ep_url, self.hostDict)
			elif pack == 'season':
				expiry_hours = 336
				sources = call.sources_packs(ep_url, self.hostDict)
			else:
				expiry_hours = 336
				sources = call.sources_packs(ep_url, self.hostDict, search_series=True, total_seasons=self.meta.get('total_seasons', 1))
			sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
			sources = self.sourcesUpdate(source, sources)
			self.sourcesQualityCount(sources)
			self.sources.extend(sources)
			dbcur.execute("DELETE FROM rel_src WHERE source = ? AND imdb_id = ? AND season = ? AND episode = ?", (source, imdb, s_check, e_check))
			dbcur.execute("INSERT INTO rel_src VALUES (?, ?, ?, ?, ?, ?)", (source, imdb, s_check, e_check, repr(sources), self.sourcesTimestamp(self.time + datetime.timedelta(hours=expiry_hours))))
			dbcon.commit()
		except Exception: pass

	def sourcesFilter(self):
		def _processTorrentFilters(item):
			if item in ('Real-Debrid', 'Premiumize.me', 'AllDebrid'):
				self.filter += [dict(i, **{'debrid':item}) for i in torrentSources if item == i.get('cache_provider')]
				if self.uncachedTorrents == 'true':
					self.filter += [dict(i, **{'debrid':item}) for i in torrentSources if 'Uncached' in i.get('cache_provider') and item in i.get('cache_provider')]
		def _processHosterFilters(item):
			for k, v in item.items():
				valid_hosters = [i for i in result_hosters if i in v]
				self.filter += [dict(i, **{'debrid':k}) for i in hoster_sources if i['source'] in valid_hosters]
		if 'true' in (self.removeDuplicates, self.removeDuplicatesTorrents):
			if len(self.final_sources) > 0:
				self.final_sources = list(self.sourcesRemoveDuplicates(self.final_sources))
				if not self.suppress_notifications: notification(ls(32679) % self.duplicates, 2500)
		self.filter = [i for i in self.final_sources if i['provider'] in self.direct_ext_scrapers]
		threads = []
		hoster_sources = [i for i in self.final_sources if not 'hash' in i and not i in self.filter]
		torrentSources = self.sourcesProcessTorrents([i for i in self.final_sources if 'hash' in i])
		result_hosters = list(set([i['source'].lower() for i in self.final_sources]))
		if self.debrid_torrents:
			for item in self.debrid_torrents: threads.append(Thread(target=_processTorrentFilters, args=(item,)))
		if self.debrid_hosters:
			for item in self.debrid_hosters: threads.append(Thread(target=_processHosterFilters, args=(item,)))
		[i.start() for i in threads]
		[i.join() for i in threads]
		self.final_sources = self.filter

	def sourcesLabels(self):
		def _processLabels(item):
			try:
				label = ''
				multiline_label1 = ''
				multiline_label2 = '\n         '
				extraInfo = item.get('extraInfo', None)
				URLName = item.get('URLName', None)
				pack = item.get('package', None)
				provider = item['provider']
				try: size = item['size_label']
				except: size = None
				quality = item['quality']
				source = item['source'].rsplit('.', 1)[0]
				debrid = item.get('debrid', None)
				if debrid:
					debrid_string = self.debrid_label_dict[debrid.lower()]
					cache_provider = item.get('cache_provider', None)
					if cache_provider:
						if 'Uncached' in cache_provider and debrid in cache_provider: debrid = '%s UNCACHED'
						else: debrid = '[B]%s CACHED[/B]'
					else: debrid = '%s HOSTED'
					debrid = debrid % debrid_string
					label += debrid
					multiline_label1 += debrid
				else:
					label += source
					multiline_label1 += source
				if quality.upper() in ['4K', '1080P', '720P']:
					label += ' | [B]%s[/B]' % quality
					multiline_label1 += ' | [B]%s[/B]' % quality
				else:
					label += ' | [I]%s[/I] ' % quality
					multiline_label1 += ' | [I]%s[/I] ' % quality
				if size not in ('0', '0.0', '0 GB', '0.0 GB', '0.00 GB', '', 'None', None):
					label += ' | %s' % size
					multiline_label1 += ' | %s' % size
				if pack:
					label += ' | [B]PACK[/B]'
					multiline_label1 += ' | [B]PACK[/B]'
				if debrid:
					label += ' | %s' % provider
					multiline_label1 += ' | %s' % provider
				if source.lower() == 'torrent':
					if 'seeders' in item and 'Uncached' in cache_provider:
						label += ' | %s SEEDS' % item['seeders']
						multiline_label1 += ' | %s SEEDS' % item['seeders']
				elif debrid:
					label += ' | %s' % source
					multiline_label1 += ' | %s' % source
				if enableExtraInfo:
					if extraInfo: label += ' | %s' % extraInfo
					if enableShowFilenames:
						if URLName: label += ' | %s' % URLName
						if extraInfo: multiline_label1 += ' | %s' % extraInfo
						if URLName: multiline_label2 += URLName
					else:
						if extraInfo: multiline_label2 += extraInfo
				elif enableShowFilenames:
					if URLName: label += ' | %s' % URLName
					if URLName: multiline_label2 += URLName
				label = label.replace('| 0 |', '|').replace(' | [I]0 [/I]', '').replace('[I] [/I] | ', '')
				label = label.upper()
				multiline_label1 = multiline_label1.replace('| 0 |', '|').replace(' | [I]0 [/I]', '').replace('[I] [/I] | ', '')
				multiline_label1 = multiline_label1.upper()
				if multiline_label2 != '':
					multiline_label2 = multiline_label2.replace('| 0 |', '|').replace(' | [I]0 [/I]', '').replace('[I] [/I] | ', '')
					multiline_label2 = multiline_label2.upper()
				if highlightType == '1':
					if quality.upper() == '4K': LeadingColor = highlight_4K
					elif quality.upper()  == '1080P': LeadingColor = highlight_1080p
					elif quality.upper() == '720P': LeadingColor = highlight_720p
					else: LeadingColor = highlight_SD
					if multiLineHighlight == '': multilineOpen = LeadingColor
					else: multilineOpen = multiLineHighlight
					item['label'] = '[COLOR=%s]' % LeadingColor + label + '[/COLOR]'
					item['multiline_label'] = '[COLOR=%s]' % LeadingColor + multiline_label1 + '[/COLOR]' + '[COLOR=%s]' % multilineOpen + multiline_label2 + '[/COLOR]'
				else:
					if 'torrent' in source.lower():
						item['label'] = singleTorrentLeading + label + singleTorrentClosing
						item['multiline_label'] = multi1TorrentLeading + multiline_label1 + multi1TorrentClosing + multi2TorrentLeading + multiline_label2 + multi2TorrentClosing
					else:
						item['label'] = singleHosterLeading + label + singleHosterClosing
						item['multiline_label'] = multi1HosterLeading + multiline_label1 + multi1HosterClosing + multi2HosterLeading + multiline_label2 + multi2HosterClosing
			except: pass
		enableExtraInfo = self.scraper_settings['extra_info']
		enableShowFilenames = self.scraper_settings['show_filenames']
		multiLineHighlight = self.scraper_settings['multiline_highlight']
		highlightType = self.scraper_settings['highlight_type']
		if highlightType == '1':
			highlight_4K = self.scraper_settings['highlight_4K']
			highlight_1080p = self.scraper_settings['highlight_1080p']
			highlight_720p = self.scraper_settings['highlight_720p']
			highlight_SD = self.scraper_settings['highlight_SD']
		else:
			hosterHighlight = self.scraper_settings['hoster_highlight']
			torrentHighlight = self.scraper_settings['torrent_highlight']
			# Single Line...
			# Torrent...
			if torrentHighlight == '':
				singleTorrentLeading = ''
				singleTorrentClosing = ''
			else:
				singleTorrentLeading = '[COLOR=%s]' % torrentHighlight
				singleTorrentClosing = '[/COLOR]'
			# Hoster...
			if hosterHighlight == '':
				singleHosterLeading = ''
				singleHosterClosing = ''
			else:
				singleHosterLeading = '[COLOR=%s]' % hosterHighlight
				singleHosterClosing = '[/COLOR]'
			# Multiline...
			# Torrent...
			if torrentHighlight == '':
				multi1TorrentLeading = ''
				multi1TorrentClosing = ''
			else:
				multi1TorrentLeading = '[COLOR=%s]' % torrentHighlight
				multi1TorrentClosing = '[/COLOR]'
			if multiLineHighlight == '':
				multi2TorrentLeading = multi1TorrentLeading
				multi2TorrentClosing = multi1TorrentClosing
			else:
				multi2TorrentLeading = '[COLOR=%s]' % multiLineHighlight
				multi2TorrentClosing = '[/COLOR]'
			# Hoster...
			if hosterHighlight == '':
				multi1HosterLeading = ''
				multi1HosterClosing = ''
			else:
				multi1HosterLeading = '[COLOR=%s]' % hosterHighlight
				multi1HosterClosing = '[/COLOR]'
			if multiLineHighlight == '':
				multi2HosterLeading = multi1HosterLeading
				multi2HosterClosing = multi1HosterClosing
			else:
				multi2HosterLeading = '[COLOR=%s]' % multiLineHighlight
				multi2HosterClosing = '[/COLOR]'
		threads = []
		for i in self.final_sources: threads.append(Thread(target=_processLabels, args=(i,)))
		[i.start() for i in threads]
		[i.join() for i in threads]
		self.final_sources = [i for i in self.final_sources if 'label' in i and 'multiline_label' in i]

	def sourcesUpdate(self, source, sources):
		source = byteify(source)
		update_dict = {'provider': source, 'external': True, 'scrape_provider': self.scrape_provider}
		for i in sources:
			i.update(update_dict)
			if 'hash' in i:
				_hash = i['hash'].lower()
				i['hash'] = _hash
		return sources

	def sourcesAddInfo(self):
		def _addInfoandName(i):
			url = i['url']
			if 'name' in i: URLName = clean_file_name(i['name']).replace('html', ' ').replace('+', ' ').replace('-', ' ')
			else: URLName = source_utils.getFileNameMatch(self.info['title'], url, i.get('name', None))
			extraInfo = source_utils.get_file_info(url)
			return _updateSource(i, {'extraInfo': extraInfo, 'URLName': URLName})
		def _updateQuality(i):
			current_quality = i['quality']
			if 'name' in i: release_name = i['name']
			else: release_name = i['url']
			quality = source_utils.get_release_quality(release_name)
			i.update({'quality': quality})
		def _getSize(i):
			size = 0
			size_label = None
			divider = None
			try:
				size = i['size']
				if 'package' in i:
					if i['package'] == 'season': divider = [int(x['episode_count']) for x in self.meta['season_data'] if int(x['season_number']) == int(self.meta['season'])][0]
					else: divider = int(self.meta['tvdb_summary']['airedEpisodes'])
					size = float(size) / divider
					size_label = '%.2f GB' % size
				else:
					size_label = '%.2f GB' % size
			except: pass
			update_dict = {'external_size': size, 'size_label': size_label, 'size': 0}
			return _updateSource(i, update_dict)
		def _updateSource(i, update_dict):
			i.update(update_dict)
		for i in self.final_sources:
			if 'URLName' in i: continue
			_getSize(i)
			_addInfoandName(i)
			_updateQuality(i)
	
	def sourcesQualityCount(self, sources, internal=False):
		if internal:
			for i in sources:
				quality = i['quality']
				if quality == '4K' and not 'uncached' in i: self.internalSources4K += 1
				elif quality in ['1440p', '1080p'] and not 'uncached' in i: self.internalSources1080p += 1
				elif quality in ['720p', 'HD'] and not 'uncached' in i: self.internalSources720p += 1
				elif not 'uncached' in i: self.internalSourcesSD += 1
				if not 'uncached' in i: self.internalSourcesTotal += 1
		else:
			for i in sources:
				quality = i['quality']
				if quality == '4K': self.source_4k += 1
				elif quality in ['1440p', '1080p']: self.source_1080 += 1
				elif quality in ['720p', 'HD']: self.source_720 += 1
				else: self.source_sd += 1
				self.total += 1

	def sourcesRemoveDuplicates(self, sources):
		uniqueURLs = set()
		uniqueHashes = set()
		for source in sources:
			try:
				if self.removeDuplicates == 'true':
					if source['url'] not in uniqueURLs:
						uniqueURLs.add(source['url'])
						if self.removeDuplicatesTorrents == 'true':
							if 'hash' in source:
								if source['hash'] not in uniqueHashes:
									uniqueHashes.add(source['hash'])
									yield source
								else: self.duplicates += 1
							else: yield source
						else: yield source
					else: self.duplicates += 1
				elif self.removeDuplicatesTorrents == 'true':
					if 'hash' in source:
						if source['hash'] not in uniqueHashes:
							uniqueHashes.add(source['hash'])
							yield source
						else:
							self.duplicates += 1
					else: yield source
				else: yield source
			except:
				yield source
	
	def sourcesProcessTorrents(self, torrentSources):
		if len(torrentSources) == 0:
			try: self.progressDialog.close()
			except Exception: pass
			return torrentSources
		if len(self.debrid_torrents) == 0:
			try: self.progressDialog.close()
			except Exception: pass
			return []
		hashList = []
		for i in torrentSources:
			try:
				infoHash = str(i['hash'])
				if len(infoHash) == 40: hashList.append(infoHash)
				else: torrentSources.remove(i)
			except: torrentSources.remove(i)
		if len(torrentSources) == 0:
			try: self.progressDialog.close()
			except Exception: pass
			return torrentSources
		from modules.debrid import DebridCheck
		try:
			xbmc.sleep(100)
			DBCheck = DebridCheck()
			torrent_results = []
			hashList = list(set(hashList))
			xbmc.sleep(100)
			cached_hashes = DBCheck.run(hashList, self.suppress_notifications, self.debrid_torrents, self.progressDialog)
			del self.progressDialog
			for item in [('Real-Debrid', 'rd_cached_hashes'), ('Premiumize.me', 'pm_cached_hashes'), ('AllDebrid', 'ad_cached_hashes')]:
				if item[0] in self.debrid_torrents:
					torrent_results.extend([dict(i, **{'cache_provider':item[0]}) for i in torrentSources if i['hash'] in cached_hashes[item[1]]])
					if self.uncachedTorrents == 'true':
						torrent_results.extend([dict(i, **{'cache_provider':'Uncached %s' % item[0]}) for i in torrentSources if not i['hash'] in cached_hashes[item[1]]])
			return torrent_results
		except:
			notification(ls(32574), 2500)

	def sourcesStats(self, sourceDict, sources):
		try:
			insert_list = []
			all_sources = [i[0] for i in sourceDict if not any(x in i[0] for x in ('season', 'show'))]
			working_scrapers = sorted(list(set([i['provider'] for i in sources])))
			non_working_scrapers = sorted([i for i in all_sources if not i in working_scrapers])
			dbcon = database.connect(self.providerDatabase, timeout=self.database_timeout)
			dbcur = dbcon.cursor()
			dbcur.execute('''PRAGMA synchronous = OFF''')
			dbcur.execute('''PRAGMA journal_mode = OFF''')
			dbcur.execute("SELECT * FROM scr_perf")
			scraper_stats = dbcur.fetchall()
			if scraper_stats != []:
				for i in scraper_stats:
					try:
						scraper, success, fail = str(i[0]), i[1], i[2]
						if scraper in working_scrapers:
							insert_list.append((scraper, success+1, fail))
							working_scrapers.remove(scraper)
						else:
							insert_list.append((scraper, success, fail+1))
							non_working_scrapers.remove(scraper)
					except: pass
			if len(working_scrapers) > 0:
				for scraper in working_scrapers:
					insert_list.append((scraper, 1, 0))
			if len(non_working_scrapers) > 0:
				for scraper in non_working_scrapers:
					insert_list.append((scraper, 0, 1))
			dbcur.executemany("INSERT OR REPLACE INTO scr_perf VALUES (?, ?, ?)", insert_list)
			dbcon.commit()
			dbcon.close()
		except: pass

	def sourcesRemoveFailing(self):
		def _check_sources(item):
			if item[1] + item[2] >= threshold:
				if float(item[2])/2 >= float(item[1]):
					remove_sources.append(item[0])
		try:
			threads = []
			remove_sources = []
			try: threshold = int(get_setting('failing_scrapers.threshold'))
			except: threshold = 25
			activeSources = [i[0] for i in self.sourceDict]
			scrapers = source_utils.external_scrapers_fail_stats()
			scrapers = [i for i in scrapers if i[0] in activeSources]
			for i in scrapers: threads.append(Thread(target=_check_sources, args=(i,)))
			[i.start() for i in threads]
			[i.join() for i in threads]
			if len(remove_sources) > 0:
				for i in remove_sources: ext_addon('script.module.fenomscrapers').setSetting('provider.%s' % i, 'false')
				self.sourceDict = [i for i in self.sourceDict if not i[0] in remove_sources]
				if not self.suppress_notifications: notification(ls(32680) % len(remove_sources), 2500)
		except: pass

	def internalResults(self):
		if self.internal_prescraped and not self.processed_prescrape:
			self.sourcesQualityCount(self.prescrape_sources, internal=True)
			self.processed_prescrape = True
		for i in self.internal_scrapers:
			win_property = window.getProperty('%s.internal_results' % i)
			if win_property in ('checked', '', None): continue
			try: internal_sources = json.loads(win_property)
			except: continue
			window.setProperty('%s.internal_results' % i, 'checked')
			self.processed_internal_scrapers.append(i)
			self.sourcesQualityCount(internal_sources, internal=True)

	def makeProgressDialog(self):
		if self.background: return
		if self.dialog_background: self.progressDialog = xbmcgui.DialogProgressBG()
		else: self.progressDialog = xbmcgui.DialogProgress()
		progressTitle = self.meta.get('rootname')
		self.progressDialog.create(progressTitle, '')
		self.progressDialog.update(0)
		self.progressDialog.update(0, ls(32678))

	def make_hostDict(self):
		pr_list = []
		for item in self.debrid_hosters:
			for k, v in item.items():
				pr_list += v
		return list(set(pr_list))

	def getConstants(self):
		self.meta = json.loads(window.getProperty('fen_media_meta'))
		self.background = self.meta.get('background', False)
		self.dialog_background = self.meta.get('dialog_background', False)
		self.suppress_notifications = True if self.background or self.dialog_background else False
		if not self.suppress_notifications: show_busy_dialog()
		self.time = datetime.datetime.now()
		self.sources = []
		self.final_sources = []
		self.processed_internal_scrapers = []
		self.active_scrapers = 0
		self.duplicates = 0
		self.database_timeout = 60.0
		source_utils.checkDatabase()
		self.remove_failing_scrapers = get_setting('remove.failing_scrapers')
		if self.remove_failing_scrapers == 'true': self.sourcesRemoveFailing()
		self.providerDatabase = source_utils.database_path
		self.direct_ext_scrapers = ['ororo', 'filepursuit', 'gdrive']
		self.debrid_label_dict = {'real-debrid': 'RD', 'premiumize.me': 'PM', 'alldebrid': 'AD'}
		self.hostDict = self.make_hostDict()
		self.sourceDictPack = source_utils.packSources()
		self.uncachedTorrents = get_setting('torrent.display.uncached')
		self.removeDuplicates = get_setting('remove.duplicates')
		self.removeDuplicatesTorrents = get_setting('remove.duplicates.torrents')
		self.sleep_time = display_sleep_time()
		self.internalSourcesTotal = self.internalSources4K = self.internalSources1080p = self.internalSources720p = self.internalSourcesSD = 0
		self.total = self.source_4k = self.source_1080 = self.source_720 = self.source_sd = 0
		if not self.progressDialog: self.makeProgressDialog()
		if not self.suppress_notifications: hide_busy_dialog()

	def sourcesTimestamp(self, date_time):
		return int(time.mktime(date_time.timetuple()))
