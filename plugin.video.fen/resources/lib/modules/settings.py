import xbmc
from modules.settings_reader import get_setting
# from modules.utils import logger

def addon():
	from xbmcaddon import Addon
	return Addon(id='plugin.video.fen')

def ext_addon(addon_id):
	from xbmcaddon import Addon
	return Addon(id=addon_id)

def addon_installed(addon_id):
	if xbmc.getCondVisibility('System.HasAddon(%s)' % addon_id): return True
	else: return False

def get_theme():
	theme = 'light' if get_setting('fen.theme') in ('0', '-', '') else 'heavy'
	return xbmc.translatePath('special://home/addons/script.tiki.artwork/resources/media/%s' % theme)

def tmdb_api_check():
	return get_setting('tmdb_api', '1b0d3c6ac6a6c0fa87b55a1069d6c9c8')

def check_database(database):
	import xbmcvfs
	if not xbmcvfs.exists(database): initialize_databases()

def display_mode():
	return int(get_setting('display_mode', '0'))

def store_resolved_torrent_to_cloud(debrid_service):
	return get_setting('store_torrent.%s' % debrid_service.lower()) == 'true'

def debrid_enabled(debrid_service):
	enabled = get_setting('%s.enabled' % debrid_service) == 'true'
	if not enabled: return False
	authed = get_setting('%s.token' % debrid_service)
	if authed not in (None, ''): return True
	return False

def display_sleep_time():
	return 0.1

def show_specials():
	return get_setting('show_specials') == 'true'

def auto_start_fen():
	return get_setting('auto_start_fen') == 'true'

def setview_delay():
	try: return float(int(get_setting('setview_delay')))/1000
	except: return 800/1000

def adjusted_datetime(string=False, dt=False):
	from datetime import datetime, timedelta
	d = datetime.utcnow() + timedelta(hours=int(get_setting('datetime.offset')))
	if dt: return d
	d = datetime.date(d)
	if string:
		try: d = d.strftime('%Y-%m-%d')
		except ValueError: d = d.strftime('%Y-%m-%d')
	else: return d

def date_to_timestamp(date_str, format="%Y-%m-%d"):
	import time
	if date_str:
		try:
			tt = time.strptime(date_str, format)
			return int(time.mktime(tt))
		except:
			return 0  # 1970
	return None

def add_release_date():
	return get_setting('subscriptions.add_release_date') == "true"
	
def movies_directory():
	return xbmc.translatePath(get_setting('movies_directory'))
	
def tv_show_directory():
	return xbmc.translatePath(get_setting('tv_shows_directory'))

def download_directory(db_type):
	setting = 'movie_download_directory' if db_type == 'movie' \
		else 'tvshow_download_directory' if db_type == 'episode' \
		else 'image_download_directory' if db_type == 'image' \
		else 'premium_download_directory'
	if get_setting(setting) != '': return xbmc.translatePath(get_setting(setting))
	else: return False

def source_folders_directory(db_type, source):
	setting = '%s.movies_directory' % source if db_type == 'movie' else '%s.tv_shows_directory' % source
	if get_setting(setting) not in ('', 'None', None): return xbmc.translatePath( get_setting(setting))
	else: return False

def paginate():
	return get_setting('paginate.lists') == "true"

def page_limit():
	try: page_limit = int(get_setting('page_limit'))
	except: page_limit = 20
	return page_limit

def ignore_articles():
	return get_setting('ignore_articles') == "true"

def default_open_action(db_type):
	action = int(get_setting('default_open_action'))
	if action == 0: return False
	db_type_setting = int(get_setting('default_open_db_type'))
	if db_type_setting == 2: return action
	db_type_dict = {'movie': 0, 'tvshow': 1}
	if db_type_setting == db_type_dict[db_type]: return action
	return False

def default_all_episodes():
	return int(get_setting('default_all_episodes'))

def quality_filter(setting):
	return get_setting(setting).split(', ')

def include_prerelease_results():
	return get_setting('include_prerelease_results') == "true"

def include_sources_in_filter(source_setting):
	return get_setting('%s_in_filter' % source_setting) == "true"

def include_uncached_results():
	return get_setting('include_uncached_results') == "true"

def auto_play():
	return get_setting('auto_play') == "true"

def minimal_notifications():
	return get_setting('autoplay_minimal_notifications') == "true"

def autoplay_next_episode():
	if auto_play() and get_setting('autoplay_next_episode') == "true": return True
	else: return False

def advancescrape_next_episode():
	if not auto_play() and get_setting('advancescrape_next_episode') == "true": return True
	else: return False

def advancescrape_show_results():
	return get_setting('advancescrape_show_results') == "true"

def autoplay_next_check_threshold():
	return int(get_setting('autoplay_next_check_threshold'))

def filter_hevc():
	try: setting = int(get_setting('filter_hevc'))
	except: setting = 0
	return setting

def sync_kodi_library_watchstatus():
	return get_setting('sync_kodi_library_watchstatus') == "true"

def refresh_trakt_on_startup():
	return get_setting('refresh_trakt_on_startup') == "true"
	
def trakt_cache_duration():
	duration = (1, 24, 168)
	return duration[int(get_setting('trakt_cache_duration'))]

def trakt_calendar_days():
	import datetime
	try: previous_days = int(get_setting('trakt.calendar_previous_days'))
	except: previous_days = 3
	try: future_days = int(get_setting('trakt.calendar_future_days'))
	except: future_days = 7
	current_date = adjusted_datetime()
	start = (current_date - datetime.timedelta(days=previous_days)).strftime('%Y-%m-%d')
	finish = previous_days + future_days
	return (start, finish)

def calendar_focus_today():
	return get_setting('calendar_focus_today') == 'true'

def watched_indicators():
	if get_setting('trakt_user') == '': return 0
	watched_indicators = get_setting('watched_indicators')
	if watched_indicators == '0': return 0
	if watched_indicators == '1' and get_setting('sync_fen_watchstatus') == 'true': return 1
	return 2

def sync_fen_watchstatus():
	if get_setting('sync_fen_watchstatus') == 'false': return False
	if get_setting('trakt_user') == '': return False
	if watched_indicators() in (0, 2): return False
	return True

def check_prescrape_sources(scraper):
	if scraper in ('furk', 'easynews', 'rd-cloud', 'pm-cloud', 'ad-cloud'): return get_setting('check.%s' % scraper) == "true"
	if get_setting('check.%s' % scraper) == "true" and get_setting('auto_play') != "true": return True
	else: return False

def subscription_update():
	return get_setting('subscription_update') == "true"

def subscription_service_time():
	return get_setting('service_time')

def trakt_list_subscriptions():
	return get_setting('trakt.subscriptions_active') == "true"

def show_subscriptions():
	trakt = get_setting('trakt.subscriptions_active') == "true"
	if not trakt: return True
	keep_non_trakt = get_setting('subscriptions.keep_nonlist') == "true"
	if keep_non_trakt: return True
	return False

def skip_duplicates():
	return get_setting('skip_duplicates') == "true"

def update_library_after_service():
	return get_setting('update_library_after_service') == "true"

def clean_library_after_service():
	return get_setting('clean_library_after_service') == "true"

def subscriptions_add_unknown_airdate():
	return get_setting('subscriptions.add_unknown_airdate') == "true"

def internal_scraper_order():
	setting = get_setting('results.internal_scrapers_order')
	if setting in ('', None):
		setting = 'FILES, FURK, EASYNEWS, CLOUD'
	return setting.split(', ')

def internal_scrapers_order_display():
	setting = get_setting('results.internal_scrapers_order_display')
	if setting in ('', None):
		setting = '$ADDON[plugin.video.fen 32493], $ADDON[plugin.video.fen 32069], $ADDON[plugin.video.fen 32070], $ADDON[plugin.video.fen 32586]'
	return setting.split(', ')

def results_sort_order():
	results_sort_order = get_setting('results.sort_order')
	if results_sort_order == '0': return ['quality_rank', 'internal_rank', 'host_rank', 'name_rank', 'external_size', 'size'] #Quality, Provider, Size
	if results_sort_order == '1': return ['quality_rank', 'internal_rank', 'host_rank', 'external_size', 'size', 'name_rank'] #Quality, Size, Provider
	if results_sort_order == '2': return ['internal_rank', 'host_rank', 'name_rank', 'quality_rank', 'external_size', 'size'] #Provider, Quality, Size
	if results_sort_order == '3': return ['internal_rank', 'host_rank', 'name_rank', 'external_size', 'size', 'quality_rank', ] #Provider, Size, Quality
	if results_sort_order == '4': return ['external_size', 'size', 'quality_rank', 'internal_rank', 'host_rank', 'name_rank'] #Size, Quality, Provider
	if results_sort_order == '5': return ['external_size', 'size', 'internal_rank', 'host_rank', 'name_rank', 'quality_rank', ] #Size, Provider, Quality
	return ['quality_rank', 'internal_rank', 'host_rank', 'name_rank', 'external_size', 'size'] #Quality, Provider, Size

def sorted_first(scraper_setting):
	return get_setting('results.%s' % scraper_setting) == "true"

def provider_color(provider):
	return get_setting('provider.%s_colour' % provider)

def active_scrapers(group_folders=False):
	folders = ['folder1', 'folder2', 'folder3', 'folder4', 'folder5']
	settings = ['provider.external', 'provider.furk', 'provider.easynews', 'provider.rd-cloud', 'provider.pm-cloud', 'provider.ad-cloud',
				'provider.local', 'provider.downloads']
	active = [i.split('.')[1] for i in settings if get_setting(i) == 'true']
	if get_setting('provider.folders') == 'true':
		if group_folders: active.append('folders')
		else: active += folders
	return active

def multiline_results():
	return get_setting('results.multiline_label') == "true"

def show_extra_info():
	return get_setting('results.show_extra_info') == 'true'

def show_filenames():
	return get_setting('results.show_filenames') == 'true'

def subscription_timer():
	if get_setting('subsciptions.update_type') == '1': return 24
	return int(get_setting('subscription_timer'))

def auto_resume():
	auto_resume = get_setting('auto_resume')
	if auto_resume == '1': return True
	if auto_resume == '2' and auto_play(): return True
	else: return False

def set_resume():
	return float(get_setting('resume.threshold'))

def set_watched():
	return float(get_setting('watched.threshold'))

def nextep_threshold():
	return float(get_setting('nextep.threshold'))

def nav_jump_use_alphabet():
	if get_setting('cache_browsed_page') == 'true': return False
	if get_setting('nav_jump') == '0': return False
	else: return True

def all_trailers():
	return get_setting('all_trailers') == "true"

def use_season_title():
	return get_setting('use_season_title') == "true"

def unaired_episode_colour():
	unaired_episode_colour = get_setting('unaired_episode_colour')
	if not unaired_episode_colour or unaired_episode_colour == '': unaired_episode_colour = 'red'
	return unaired_episode_colour

def nextep_airdate_format():
	date_format = get_setting('nextep.airdate_format')
	if date_format == '0': return '%d-%m-%Y'
	elif date_format == '1': return '%Y-%m-%d'
	elif date_format == '2': return '%m-%d-%Y'
	else: return '%Y-%m-%d'

def nextep_display_settings():
	include_airdate = get_setting('nextep.include_airdate') == 'true'
	airdate_colour = get_setting('nextep.airdate_colour', 'magenta')
	unaired_colour = get_setting('nextep.unaired_colour', 'red')
	unwatched_colour = get_setting('nextep.unwatched_colour', 'darkgoldenrod')
	return {'include_airdate': include_airdate, 'airdate_colour': airdate_colour,
			'unaired_colour': unaired_colour, 'unwatched_colour': unwatched_colour}

def nextep_content_settings():
	sort_type = int(get_setting('nextep.sort_type'))
	sort_order = int(get_setting('nextep.sort_order'))
	sort_direction = True if sort_order == 0 else False
	sort_key = 'curr_last_played_parsed' if sort_type == 0 else 'first_aired' if sort_type == 1 else 'name'
	cache_to_disk = get_setting('nextep.cache_to_disk') == 'true'
	include_unaired = get_setting('nextep.include_unaired') == 'true'
	include_unwatched = get_setting('nextep.include_unwatched') == 'true'
	return {'cache_to_disk': cache_to_disk, 'sort_key': sort_key, 'sort_direction': sort_direction, 'sort_type': sort_type, 'sort_order':sort_order,
			'include_unaired': include_unaired, 'include_unwatched': include_unwatched}

def scraping_settings():
	extra_info = show_extra_info()
	enable_filenames = show_filenames()
	multiline_highlight = get_setting('secondline.identify', '')
	if multiline_highlight.lower() == 'no color': multiline_highlight = ''
	highlight_type = get_setting('highlight.type', '0')
	highlight_4K = get_setting('scraper_4k_highlight', 'magenta')
	highlight_1080p = get_setting('scraper_1080p_highlight', 'lawngreen')
	highlight_720p = get_setting('scraper_720p_highlight', 'gold')
	highlight_SD = get_setting('scraper_SD_highlight', 'lightsaltegray')
	hoster_highlight = get_setting('hoster.identify', 'blue')
	if hoster_highlight.lower() == 'no color': hoster_highlight = ''
	torrent_highlight = get_setting('torrent.identify', 'magenta')
	if torrent_highlight.lower() == 'no color': torrent_highlight = ''
	return {'extra_info': extra_info, 'show_filenames': enable_filenames,
			'multiline_highlight': multiline_highlight, 'highlight_type': highlight_type,
			'highlight_4K': highlight_4K, 'highlight_1080p': highlight_1080p, 'highlight_720p': highlight_720p,
			'highlight_SD': highlight_SD, 'hoster_highlight': hoster_highlight, 'torrent_highlight': torrent_highlight}

def create_directory(dir_path, dir_name=None):
	import os
	if dir_name:
		dir_path = os.path.join(dir_path, dir_name)
	dir_path = dir_path.strip()
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)
	return dir_path

def list_actions_global():
	global list_actions
	list_actions = []

def initialize_databases():
	import xbmcvfs
	import os
	try: from sqlite3 import dbapi2 as database
	except ImportError: from pysqlite2 import dbapi2 as database
	from settings_reader import make_settings_dict
	DATA_PATH = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/')
	if not xbmcvfs.exists(DATA_PATH): xbmcvfs.mkdirs(DATA_PATH)
	NAVIGATOR_DB = os.path.join(DATA_PATH, "navigator.db")
	WATCHED_DB = os.path.join(DATA_PATH, "watched_status.db")
	FAVOURITES_DB = os.path.join(DATA_PATH, "favourites.db")
	VIEWS_DB = os.path.join(DATA_PATH, "views.db")
	TRAKT_DB = os.path.join(DATA_PATH, "fen_trakt2.db")
	FEN_DB = os.path.join(DATA_PATH, "fen_cache2.db")
	make_settings_dict()
	#Always check NAVIGATOR.
	dbcon = database.connect(NAVIGATOR_DB)
	dbcon.execute("""CREATE TABLE IF NOT EXISTS navigator
					  (list_name text, list_type text, list_contents text) 
				   """)
	if not xbmcvfs.exists(WATCHED_DB):
		dbcon = database.connect(WATCHED_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS progress
						  (db_type text, media_id text, season integer, episode integer,
						  resume_point text, curr_time text,
						  unique(db_type, media_id, season, episode)) 
					   """)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS watched_status
						  (db_type text, media_id text, season integer,
						  episode integer, last_played text, title text,
						  unique(db_type, media_id, season, episode)) 
					   """)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS exclude_from_next_episode
						  (media_id text, title text) 
					   """)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS unwatched_next_episode
						  (media_id text) 
					   """)
		dbcon.close()
	if not xbmcvfs.exists(FAVOURITES_DB):
		dbcon = database.connect(FAVOURITES_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS favourites
						  (db_type text, tmdb_id text, title text, unique (db_type, tmdb_id)) 
					   """)
		dbcon.close()
	if not xbmcvfs.exists(VIEWS_DB):
		dbcon = database.connect(VIEWS_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS views
						  (view_type text, view_id text, unique (view_type)) 
					   """)
		dbcon.close()
	if not xbmcvfs.exists(TRAKT_DB):
		dbcon = database.connect(TRAKT_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS fentrakt(
					id TEXT UNIQUE, data TEXT, expires INTEGER)
							""")
		dbcon.close()
	if not xbmcvfs.exists(FEN_DB):
		dbcon = database.connect(FEN_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS fencache(
					id TEXT UNIQUE, data TEXT, expires INTEGER)
							""")
		dbcon.close()
	return True
