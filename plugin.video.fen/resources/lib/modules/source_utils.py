# -*- coding: utf-8 -*-
import xbmc, xbmcvfs, xbmcgui
import os
import re
try: from urlparse import urlparse
except ImportError: from urllib.parse import urlparse
try: from urllib import unquote
except ImportError: from urllib.parse import unquote
try: from sqlite3 import dbapi2 as database
except Exception: from pysqlite2 import dbapi2 as database
from modules.utils import confirm_dialog, replace_html_codes
from modules.utils import local_string as ls
from modules.settings_reader import get_setting
from modules.settings import ext_addon
from caches.fen_cache import cache_object
from fenomscrapers import pack_sources
# from modules.utils import logger

data_path = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/')
os_data_path = xbmc.translatePath('special://profile/addon_data/script.module.fenomscrapers/')
os_addon_dir = xbmc.translatePath('special://home/addons/script.module.fenomscrapers/')
database_path = os.path.join(data_path, "ext_providers3.db")
scraper_module_base_folder = os.path.join(os_addon_dir, 'lib', 'fenomscrapers')

window = xbmcgui.Window(10000)

__external__ = ext_addon('script.module.fenomscrapers')

RES_4K = [' 4k ', ' hd4k ', ' 4khd ', ' uhd ', ' ultrahd ', ' ultra hd ', ' 2160 ', ' 2160p ', ' hd2160 ', ' 2160hd ']
RES_1080 = [' 1080 ', ' 1080p ', ' 1080i ', ' hd1080 ', ' 1080hd ', ' m1080p ', ' fullhd ', ' full hd ', ' 1o8o ', ' 1o8op ']
RES_720 = [' 720 ', ' 720p ', ' 720i ', ' hd720 ', ' 720hd ', ' hd ', ' 72o ', ' 72op ']
RES_SD = [' 576 ', ' 576p ', ' 576i ', ' sd576 ', ' 576sd ', ' 480 ', ' 480p ', ' 480i ', ' sd480 ', ' 480sd ', ' 360 ', ' 360p ', ' 360i ', ' sd360 ', ' 360sd ', ' 240 ', ' 240p ', ' 240i ', ' sd240 ', ' 240sd ']
CAM = [' camrip ', ' hdcam ', ' hd cam ', ' cam rip ', ' dvdcam ', ' cam ']
SCR = [' scr ', ' screener ', ' dvdscr ', ' dvd scr ', ' r5 ', ' r6 ']
TELE = [' tsrip ', ' hdts ', ' hdtc ', ' dvdts ', ' telesync ', ' ts ', ' tc ']

def sources():
	sourceDict = []
	try:
		sourceFolderLocation = os.path.join(scraper_module_base_folder, 'sources_fenomscrapers')
		sourceSubFolders = ['hosters', 'torrents']
		path = 'fenomscrapers.sources_fenomscrapers.%s.%s'
		enabled_scrapers = enabledScrapersXML()
		for item in sourceSubFolders:
			files = xbmcvfs.listdir(os.path.join(sourceFolderLocation, item))[1]
			for m in files:
				try:
					if not os.path.splitext(urlparse(m).path)[-1] == '.py':
						continue
					module_name = m.split('.')[0]
					if module_name == '__init__':
						continue
					if str(module_name) in enabled_scrapers:
						module_path = path % (item, module_name)
						sourceDict.append((module_name, module_path))
				except: pass
	except: pass
	return sourceDict

def importSingleSource(source):
	sourceDict = []
	try:
		sourceFolderLocation = os.path.join(scraper_module_base_folder, 'sources_fenomscrapers')
		sourceSubFolders = ['hosters', 'torrents']
		path = 'fenomscrapers.sources_fenomscrapers.%s.%s'
		for item in sourceSubFolders:
			files = xbmcvfs.listdir(os.path.join(sourceFolderLocation, item))[1]
			for m in files:
				if not os.path.splitext(urlparse(m).path)[-1] == '.py':
					continue
				module_name = m.split('.')[0]
				if module_name == source:
					module_path = path % (item, module_name)
					return module_path
	except: return None

def packSources():
	def _get_pack_info(dummy_arg):
		return pack_sources()
	try:
		version = __external__.getAddonInfo('version')
		string = 'fen_fs_pack_providers_%s' % version
		return cache_object(_get_pack_info, string, 'dummy_arg', False, 168)
	except: return []

def enabledScrapersXML():
	import xml.etree.ElementTree as ET
	from modules.nav_utils import get_kodi_version
	kodi_version = get_kodi_version()
	enabled_scrapers = []
	settings_location = xbmc.translatePath('special://profile/addon_data/script.module.fenomscrapers/settings.xml')
	if not xbmcvfs.exists(settings_location): makeEXTSettingsFile()
	root = ET.parse(settings_location).getroot()
	for item in root:
		try:
			setting_id = item.get('id')
			if setting_id.startswith('provider'):
				if kodi_version >= 18: setting_value = item.text
				else: setting_value = item.get('value')
				if setting_value == 'true':
					enabled_scrapers.append(setting_id.split('.')[1])
		except: pass
	return enabled_scrapers

def makeEXTSettingsFile():
	from xbmcaddon import Addon
	Addon('script.module.fenomscrapers').setSetting('module.provider', 'Fenomscrapers')
	xbmc.sleep(100)

def normalize(title):
	try:
		try: return title.decode('ascii').encode("utf-8")
		except: pass
		
		try: import unicodedata
		except ImportError: return
		title = u'%s' % obj
		title = ''.join(c for c in unicodedata.normalize('NFD', title) if unicodedata.category(c) != 'Mn')

		return str(title)
	except:
		return title

def deleteProviderCache(silent=False):
	try:
		if not xbmcvfs.exists(database_path): return 'failure'
		if not silent:
			if not confirm_dialog(): return 'cancelled'
		dbcon = database.connect(database_path)
		dbcur = dbcon.cursor()
		for i in ('rel_url', 'rel_src'): dbcur.execute("DELETE FROM %s" % i)
		dbcon.commit()
		dbcur.execute("VACUUM")
		dbcon.close()
		return 'success'
	except: return 'failure'

def cleanProviderDatabase():
	import time
	import datetime
	dbcon = database.connect(database_path)
	dbcur = dbcon.cursor()
	dbcur.execute("DELETE from rel_src WHERE CAST(added AS INT) <= ?", (int(time.mktime(datetime.datetime.now().timetuple())),))
	dbcon.commit()
	dbcur.execute("VACUUM")
	dbcon.close()
	return

def checkDatabase():
	if not xbmcvfs.exists(data_path): xbmcvfs.mkdirs(data_path)
	dbcon = database.connect(database_path)
	dbcon.execute("""CREATE TABLE IF NOT EXISTS rel_url
					  (source text, imdb_id text, season text, episode text,
					  rel_url text, unique (source, imdb_id, season, episode)) 
				   """)
	dbcon.execute("""CREATE TABLE IF NOT EXISTS rel_src
					  (source text, imdb_id text, season text, episode text,
					  hosts text, added text, unique (source, imdb_id, season, episode)) 
				   """)
	dbcon.execute("""CREATE TABLE IF NOT EXISTS scr_perf
					  (source text, success integer, failure integer, unique (source)) 
				   """)
	dbcon.close()

def external_scrapers_fail_stats():
	checkDatabase()
	dbcon = database.connect(database_path)
	dbcur = dbcon.cursor()
	dbcur.execute("SELECT * FROM scr_perf")
	results = dbcur.fetchall()
	results = sorted([(str(i[0]), i[1], i[2]) for i in results], key=lambda k: k[2] - k[1], reverse=True)
	return results

def external_scrapers_disable():
	from modules.utils import multiselect_dialog
	dialog = xbmcgui.Dialog()
	scrapers = external_scrapers_fail_stats()
	try: scrapers = [i for i in scrapers if __external__.getSetting('provider.%s' % i[0]) == 'true']
	except: scrapers = []
	if not scrapers: return dialog.ok('Fen', ls(32581))
	scrapers_dialog = ['[B]%s[/B] | %s: %s | [COLOR=green]%s: %d[/COLOR] | [COLOR=red]%s: %d[/COLOR]' % (i[0].upper(), ls(32677).upper(), (i[1] + i[2]), ls(32576).upper(),i[1], ls(32490).upper(), i[2]) for i in scrapers]
	scraper_choice = multiselect_dialog(ls(32024), scrapers_dialog, scrapers)
	if not scraper_choice: return
	if confirm_dialog(): clear_database = True
	else: clear_database = False
	checkDatabase()
	dbcon = database.connect(database_path)
	dbcur = dbcon.cursor()
	for i in scraper_choice:
		if clear_database: dbcur.execute("DELETE FROM scr_perf WHERE source = ?", (i[0],))
		__external__.setSetting('provider.%s' % i[0], 'false')
	if clear_database:
		dbcon.commit()
	return dialog.ok('FEN', ls(32576))

def external_scrapers_reset_stats(silent=False):
	try:
		checkDatabase()
		if not silent:
			if not confirm_dialog(): return
		dbcon = database.connect(database_path)
		dbcur = dbcon.cursor()
		dbcur.execute("DELETE FROM scr_perf")
		dbcon.commit()
		dbcur.execute("VACUUM")
		dbcon.close()
		if silent: return
		return xbmcgui.Dialog().ok('FEN', ls(32576))
	except:
		if silent: return
		return xbmcgui.Dialog().ok('FEN', ls(32574))

def _ext_scrapers_notice(status):
	from modules.nav_utils import notification
	notification(status, 2500)

def toggle_all(folder, setting, silent=False):
	try:
		sourcelist = scraperNames(folder)
		for i in sourcelist:
			source_setting = 'provider.' + i
			__external__.setSetting(source_setting, setting)
		if silent: return
		return _ext_scrapers_notice(ls(32576))
	except:
		if silent: return
		return _ext_scrapers_notice(ls(32574))

def enable_disable_specific_all(folder):
	try:
		from modules.utils import multiselect_dialog
		enabled, disabled = scrapersStatus(folder)
		all_sources = sorted(enabled + disabled)
		preselect = [all_sources.index(i) for i in enabled]
		chosen = multiselect_dialog('Fen', [i.upper() for i in all_sources], all_sources, preselect)
		if not chosen: return
		for i in all_sources:
			if i in chosen: __external__.setSetting('provider.' + i, 'true')
			else: __external__.setSetting('provider.' + i, 'false')
		return _ext_scrapers_notice(ls(32576))
	except: return _ext_scrapers_notice(ls(32574))

def scrapersStatus(folder='all'):
	providers = scraperNames(folder)
	enabled = [i for i in providers if __external__.getSetting('provider.' + i) == 'true']
	disabled = [i for i in providers if i not in enabled]
	return enabled, disabled

def scraperNames(folder):
	providerList = []
	sourceFolderLocation = os.path.join(scraper_module_base_folder, 'sources_fenomscrapers')
	sourceSubFolders = ['hosters', 'torrents']
	if folder != 'all':
		sourceSubFolders = [i for i in sourceSubFolders if i == folder]
	for item in sourceSubFolders:
		files = xbmcvfs.listdir(os.path.join(sourceFolderLocation, item))[1]
		for m in files:
			if not os.path.splitext(urlparse(m).path)[-1] == '.py':
				continue
			module_name = m.split('.')[0]
			if module_name == '__init__':
				continue
			providerList.append(module_name)
	return providerList

def pack_enable_check(meta, season, episode):
	extra_info = meta['extra_info']
	status = extra_info['status'].lower()
	if status in ('ended', 'canceled'): return True, True
	from tikimeta import season_episodes_meta, retrieve_user_info
	from modules.utils import adjust_premiered_date
	from modules.settings import adjusted_datetime
	adjust_hours = int(get_setting('datetime.offset'))
	current_adjusted_date = adjusted_datetime(dt=True)
	meta_user_info = retrieve_user_info()
	episodes_data = season_episodes_meta(meta['tmdb_id'], meta['tvdb_id'], season, meta['tvdb_summary']['airedSeasons'], meta['season_data'], meta_user_info, False)
	unaired_episodes = [adjust_premiered_date(i['premiered'], adjust_hours)[0] for i in episodes_data]
	if None in unaired_episodes or any(i > current_adjusted_date for i in unaired_episodes): return False, False
	else: return True, False
	return False, False

def getFileNameMatch(title, url, name=None):
	from modules.utils import clean_file_name
	if name: return clean_file_name(name)
	try: from urllib import unquote
	except ImportError: from urllib.parse import unquote
	from modules.utils import clean_title, normalize
	title_match = None
	try:
		title = clean_title(normalize(title))
		name_url = unquote(url)
		try: file_name = clean_title(name_url.split('/')[-1])
		except: return title_match
		test = name_url.split('/')
		for item in test:
			test_url = str(clean_title(normalize(item)))
			if title in test_url:
				title_match = clean_file_name(str(item)).replace('html', ' ').replace('+', ' ')
				break
	except:
		pass
	return title_match

def supported_video_extensions():
	supported_video_extensions = xbmc.getSupportedMedia('video').split('|')
	return [i for i in supported_video_extensions if i != '' and i != '.zip']

def seas_ep_query_list(season, episode):
	return ['s%02de%02d' % (int(season), int(episode)),
			'%dx%02d' % (int(season), int(episode)),
			'%02dx%02d' % (int(season), int(episode)),
			'season%02depisode%02d' % (int(season), int(episode)),
			'season%depisode%02d' % (int(season), int(episode)),
			'season%depisode%d' % (int(season), int(episode))]

def seas_ep_filter(season, episode, release_title, split=False):
	try: from urllib import unquote
	except: from urllib.parse import unquote
	release_title = re.sub('[^A-Za-z0-9-]+', '.', unquote(release_title).replace('\'', '')).lower()
	string1 = '(s<<S>>e<<E>>)|' \
			  '(s<<S>>\.e<<E>>)|' \
			  '(s<<S>>ep<<E>>)|' \
			  '(s<<S>>\.ep<<E>>)'
	string2 = '(season\.<<S>>\.episode\.<<E>>)|' \
			  '(season<<S>>\.episode<<E>>)|' \
			  '(season<<S>>episode<<E>>)|' \
			  '(<<S>>x<<E>>\.)|' \
			  '(s<<S>>e\(<<E>>\))|' \
			  '(s<<S>>\.e\(<<E>>\))|' \
			  '(<<S>>\.<<E>>\.)'
	string3 = '(<<S>><<E>>\.)'
	string4 = '(s<<S>>e<<E1>>e<<E2>>)|' \
			  '(s<<S>>e<<E1>>-e<<E2>>)|' \
			  '(s<<S>>e<<E1>>\.e<<E2>>)|' \
			  '(s<<S>>e<<E1>>-<<E2>>)-|' \
			  '(s<<S>>e<<E1>>\.<<E2>>)\.|' \
			  '(s<<S>>e<<E1>><<E2>>)'
	string_list = []
	string_list.append(string1.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
	string_list.append(string1.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
	string_list.append(string2.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
	string_list.append(string2.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
	string_list.append(string2.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode)))	
	string_list.append(string2.replace('<<S>>', str(season)).replace('<<E>>', str(episode)))
	string_list.append(string3.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
	string_list.append(string3.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
	string_list.append(string4.replace('<<S>>', str(season).zfill(2)).replace('<<E1>>', str(episode-1).zfill(2)).replace('<<E2>>', str(episode).zfill(2)))
	string_list.append(string4.replace('<<S>>', str(season).zfill(2)).replace('<<E1>>', str(episode).zfill(2)).replace('<<E2>>', str(episode+1).zfill(2)))
	final_string = '|'.join(string_list)
	reg_pattern = re.compile(final_string)
	if split:
		return release_title.split(re.search(reg_pattern, release_title).group(), 1)[1]
	else:
		return bool(re.search(reg_pattern, release_title))

def episode_extras_filter():
	return ['sample', 'extra', 'extras', 'deleted', 'unused', 'footage', 'inside', 'blooper', 'bloopers', 'making.of', 'feature', 'featurette']

def get_release_quality(release_name, release_link=None):
	quality = 'default'
	try:
		try: release_name = release_name.encode('utf-8')
		except: pass
		try:
			fmt = replace_html_codes(release_name)
			fmt = unquote(fmt)
			fmt = fmt.lower()
			fmt = re.sub('[^a-z0-9]+', ' ', fmt)
		except:
			fmt = str(release_name)
		if any(i in fmt for i in CAM): quality = 'CAM'
		elif any(i in fmt for i in SCR): quality = 'SCR'
		elif any(i in fmt for i in TELE): quality = 'TELE'
		elif any(i in fmt for i in RES_4K): quality = '4K'
		elif any(i in fmt for i in RES_1080): quality = '1080p'
		elif any(i in fmt for i in RES_720): quality = '720p'
		elif any(i in fmt for i in RES_SD): quality = 'SD'
	except: pass
	if quality == 'default':
		if release_link:
			try:
				try: release_link = release_link.encode('utf-8')
				except: pass
				fmt = release_link.lower()
				fmt = re.sub('[^a-z0-9]+', ' ', fmt)
				if any(i in fmt for i in CAM): quality = 'CAM'
				elif any(i in fmt for i in SCR): quality = 'SCR'
				elif any(i in fmt for i in TELE): quality = 'TELE'
				elif any(i in fmt for i in RES_4K): quality = '4K'
				elif any(i in fmt for i in RES_1080): quality = '1080p'
				elif any(i in fmt for i in RES_720): quality = '720p'
				elif any(i in fmt for i in RES_SD): quality = 'SD'
			except: pass
		else: pass
	if quality == 'default': quality = 'SD'
	return quality

def get_file_info(url):
	try: url = url.encode('utf-8')
	except: pass
	try:
		url = replace_html_codes(url)
		url = unquote(url)
		url = url.lower()
		url = re.sub('[^a-z0-9]+', ' ', url)
	except:
		url = str(url)
	info = ''
	if any(i in url for i in [' h 265 ', ' h256 ', ' x265 ', ' hevc ']):
		info += '[B]HEVC[/B] |'
	if ' hi10p ' in url:
		info += ' HI10P |'
	if ' 10bit ' in url:
		info += ' 10BIT |'
	if ' 3d ' in url:
		info += ' 3D |'
	if any(i in url for i in [' bluray ', ' blu ray ']):
		info += ' BLURAY |'
	if any(i in url for i in [' bd r ', ' bdr ', ' bd rip ', ' bdrip ', ' br rip ', ' brrip ']):
		info += ' BD-RIP |'
	if any(i in url for i in [' remux ', ' bdremux ', ' bd remux ']):
		info += ' REMUX |'
	if any(i in url for i in [' dvdrip ', ' dvd rip ']):
		info += ' DVD-RIP |'
	if any(i in url for i in [' dvd ', ' dvdr ', ' dvd r ']):
		info += ' DVD |'
	if any(i in url for i in [' webdl ', ' web dl ', ' web ', ' web rip ', ' webrip ']):
		info += ' WEB |'
	if ' hdtv ' in url:
		info += ' HDTV |'
	if ' sdtv ' in url:
		info += ' SDTV |'
	if any(i in url for i in [' hdrip ', ' hd rip ']):
		info += ' HDRIP |'
	if any(i in url for i in [' uhdrip ', ' uhd rip ']):
		info += ' UHDRIP |'
	if any(i in url for i in [' hdr ', ' hdr10 ', ' dolby vision ', ' hlg ']):
		info += ' HDR |'
	if ' imax ' in url:
		info += ' IMAX |'
	if any(i in url for i in [' ac3 ', ' ac 3 ']):
		info += ' AC3 |'
	if ' aac ' in url:
		info += ' AAC |'
	if ' aac5 1 ' in url:
		info += ' AAC | 5.1 |'
	if any(i in url for i in [' dd ', ' dolby ', ' dolbydigital ', ' dolby digital ']):
		info += ' DD |'
	if any(i in url for i in [' truehd ', ' true hd ']):
		info += ' TRUEHD |'
	if ' atmos ' in url:
		info += ' ATMOS |'
	if any(i in url for i in [' ddplus ', ' dd plus ', ' ddp ', ' eac3 ', ' eac 3 ']):
		info += ' DD+ |'
	if ' dts ' in url:
		info += ' DTS |'
	if any(i in url for i in [' hdma ', ' hd ma ']):
		info += ' HD.MA |'
	if any(i in url for i in [' hdhra ', ' hd hra ']):
		info += ' HD.HRA |'
	if any(i in url for i in [' dtsx ', ' dts x ']):
		info += ' DTS:X |'
	if any(i in url for i in [' dd5 1 ', ' dd5 1ch ']):
		info += ' DD | 5.1 |'
	if any(i in url for i in [' ddp5 1 ', ' ddp5 1ch ']):
		info += ' DD+ | 5.1 |'
	if ' opus ' in url:
		info += ' OPUS |'
	if any(i in url for i in [' 5 1 ', ' 5 1ch ', ' 6ch ']):
		info += ' 5.1 |'
	if any(i in url for i in [' 7 1 ', ' 7 1ch ', ' 8ch ']):
		info += ' 7.1 |'
	if ' korsub ' in url:
		info += ' HC-SUBS |'
	if any(i in url for i in [' subs ', ' subbed ', ' sub ']):
		info += ' SUBS |'
	if any(i in url for i in [' dub ', ' dubbed ', ' dublado ']):
		info += ' DUB |'
	info = info.rstrip('|')
	return info




