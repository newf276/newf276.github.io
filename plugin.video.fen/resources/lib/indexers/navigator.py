import xbmc, xbmcvfs, xbmcplugin, xbmcgui
import os
from sys import argv
import json
import time
try: from urllib import urlencode
except ImportError: from urllib.parse import urlencode
from indexers.default_menus import DefaultMenus
from modules.nav_utils import setView
from modules.utils import to_utf8
from modules.utils import local_string as ls
from modules.settings_reader import get_setting, set_setting
from modules import settings
try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database
# from modules.utils import logger

addon_dir = xbmc.translatePath('special://home/addons/plugin.video.fen/')
profile_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/')
NAVIGATOR_DB = os.path.join(profile_dir, "navigator.db")
window = xbmcgui.Window(10000)


class Navigator:
	def __init__(self, params):
		self.view = 'view.main'
		self.params = params
		self.icon_directory = settings.get_theme()
		self.list_name = self.params.get('action', 'RootList')
		self.fanart = os.path.join(addon_dir, 'fanart.png')
		self.insert_string = ls(32484)
		self.movies_string = ls(32028)
		self.tvshows_string = ls(32029)
		self.__url__ = argv[0]
		self.__handle__ = int(argv[1])

	def main(self):
		if self.list_name == 'RootList': self._changelog_info()
		self.build_main_lists()

	def downloads(self):
		downloads_string, premium_string, images_string = ls(32107), ls(32485), ls(32798)
		name_insert, list_name_insert = self.insert_string % (downloads_string.upper(), '%s'), '%s %s' % ('%s', downloads_string)
		movie_path, episode_path, premium_path, images_path = settings.download_directory('movie'), settings.download_directory('episode'), settings.download_directory('premium'), settings.download_directory('image')
		self._add_dir({'mode': 'navigator.folder_navigator', 'folder_path': movie_path, 'foldername': 'Movie Downloads', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='movies.png')
		self._add_dir({'mode': 'navigator.folder_navigator', 'folder_path': episode_path, 'foldername': 'TV Show Downloads', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='tv.png')
		self._add_dir({'mode': 'navigator.folder_navigator', 'folder_path': premium_path, 'foldername': 'Premium File Downloads', 'list_name': list_name_insert % premium_string}, name_insert % premium_string, iconImage='premium.png')
		self._add_dir({'mode': 'browser_image', 'folder_path': images_path, 'foldername': 'Images File Downloads', 'list_name': list_name_insert % images_string}, name_insert % images_string, iconImage='people.png')
		self._end_directory()

	def discover_main(self):
		discover_string, history_string, help_string = ls(32451), ls(32486), ls(32487)
		movies_history_string, tvshows_history_string = '%s %s' % (self.movies_string, history_string), '%s %s' % (self.tvshows_string, history_string)
		name_insert, list_name_insert = self.insert_string % (discover_string.upper(), '%s'), '%s %s' % (discover_string, '%s')
		self._add_dir({'mode': 'discover.movie', 'db_type': 'movie', 'foldername': 'Discover Movies', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='discover.png')
		self._add_dir({'mode': 'discover.tvshow', 'db_type': 'tvshow', 'foldername': 'Discover TV Shows', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='discover.png')
		self._add_dir({'mode': 'discover.history', 'db_type': 'movie', 'foldername': 'Discover Movie History', 'list_name': list_name_insert % movies_history_string}, name_insert % movies_history_string, iconImage='discover.png')
		self._add_dir({'mode': 'discover.history', 'db_type': 'tvshow', 'foldername': 'Discover TV Show History', 'list_name': list_name_insert % tvshows_history_string}, name_insert % tvshows_history_string, iconImage='discover.png')
		self._add_dir({'mode': 'discover.help', 'foldername': 'Discover Help', 'list_name': list_name_insert % help_string}, name_insert % help_string, iconImage='discover.png', isFolder=False)
		self._end_directory()

	def premium(self):
		from modules.debrid import debrid_enabled
		name_insert = self.insert_string % (ls(32488).upper(), '%s')
		furk_string, easy_string, rd_string, pm_string, ad_string = ls(32069), ls(32070), ls(32054), ls(32061), ls(32063)
		furk_api = get_setting('furk_api_key')
		if not furk_api:
			if not get_setting('furk_login') or not get_setting('furk_password'): enable_fu = False
			else: enable_fu = True
		else: enable_fu = True
		enable_en = False if '' in (get_setting('easynews_user'), get_setting('easynews_password')) else True
		debrids = debrid_enabled()
		if enable_fu: self._add_dir({'mode': 'navigator.furk', 'foldername': 'Furk', 'list_name': furk_string}, name_insert % furk_string, iconImage='furk.png')
		if enable_en: self._add_dir({'mode': 'navigator.easynews', 'foldername': 'Easynews', 'list_name': easy_string}, name_insert % easy_string, iconImage='easynews.png')
		if 'Real-Debrid' in debrids: self._add_dir({'mode': 'navigator.real_debrid', 'foldername': 'Real Debrid', 'list_name': rd_string}, name_insert % rd_string, iconImage='realdebrid.png')
		if 'Premiumize.me' in debrids: self._add_dir({'mode': 'navigator.premiumize', 'foldername': 'Premiumize', 'list_name': pm_string}, name_insert % pm_string, iconImage='premiumize.png')
		if 'AllDebrid' in debrids: self._add_dir({'mode': 'navigator.alldebrid', 'foldername': 'All Debrid', 'list_name': ad_string}, name_insert % ad_string, iconImage='alldebrid.png')
		self._end_directory()

	def furk(self):
		furk_string, active_string, failed_string, video_string, audio_string, files_string, downloads_string = ls(32069), ls(32489), ls(32490), ls(32491), ls(32492), ls(32493), ls(32107)
		search_string, history_string, account_string = ls(32450), ls(32486), ls(32494)
		history_video, history_audio = '%s %s' % (history_string, video_string), '%s %s' % (history_string, audio_string)
		name_insert, list_name_insert = self.insert_string % (furk_string.upper(), '%s %s'), (self.insert_string % (furk_string, '%s %s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'furk.my_furk_files', 'list_type': 'file_get_video', 'foldername': 'Furk Video Files', 'list_name': list_name_insert % (video_string, files_string)}, name_insert % (video_string, files_string), iconImage='lists.png')
		self._add_dir({'mode': 'furk.my_furk_files', 'list_type': 'file_get_audio', 'foldername': 'Furk Audio Files', 'list_name': list_name_insert % (audio_string, files_string)}, name_insert % (audio_string, files_string), iconImage='lists.png')
		self._add_dir({'mode': 'furk.my_furk_files', 'list_type': 'file_get_active', 'foldername': 'Furk Active Downloads', 'list_name': list_name_insert % (active_string, downloads_string)}, name_insert % (active_string, downloads_string), iconImage='lists.png')
		self._add_dir({'mode': 'furk.my_furk_files', 'list_type': 'file_get_failed', 'foldername': 'Furk Failed Downloads', 'list_name': list_name_insert % (failed_string, downloads_string)}, name_insert % (failed_string, downloads_string), iconImage='lists.png')
		self._add_dir({'mode': 'furk.search_furk', 'db_type': 'video', 'foldername': 'Search Furk Video', 'list_name': list_name_insert % (search_string, video_string)}, name_insert % (search_string, video_string), iconImage='search.png')
		self._add_dir({'mode': 'furk.search_furk', 'db_type': 'audio', 'foldername': 'Search Furk Audio', 'list_name': list_name_insert % (search_string, audio_string)}, name_insert % (search_string, audio_string), iconImage='search.png')
		self._add_dir({'mode': 'search_history', 'action': 'furk_video', 'foldername': 'Video Search History', 'list_name': list_name_insert % (search_string, history_video)}, name_insert % (search_string, history_video), iconImage='search.png')
		self._add_dir({'mode': 'search_history', 'action': 'furk_audio', 'foldername': 'Audio Search History', 'list_name': list_name_insert % (search_string, history_audio)}, name_insert % (search_string, history_audio), iconImage='search.png')
		self._add_dir({'mode': 'furk.account_info', 'foldername': 'Account Info', 'list_name': list_name_insert % (account_string, '')}, name_insert % (account_string, ''), iconImage='furk.png', isFolder=False)
		self._end_directory()

	def easynews(self):
		easy_string, search_string, history_string, account_string = ls(32070), ls(32450), ls(32486), ls(32494)
		search_history_string, name_insert, list_name_insert = '%s %s' % (search_string, history_string), self.insert_string % (easy_string.upper(), '%s'), (self.insert_string % (easy_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'easynews.search_easynews', 'foldername': 'Search Easynews', 'list_name': list_name_insert % search_string}, name_insert % search_string, iconImage='search.png')
		self._add_dir({'mode': 'search_history', 'action': 'easynews_video', 'foldername': 'Easynews Search History', 'list_name': list_name_insert % search_history_string}, name_insert % search_history_string, iconImage='search.png')
		self._add_dir({'mode': 'easynews.account_info', 'foldername': 'Account Info', 'list_name': list_name_insert % account_string}, name_insert % account_string, iconImage='easynews.png', isFolder=False)
		self._end_directory()

	def real_debrid(self):
		rd_string, account_string, history_string, cloud_string = ls(32054), ls(32494), ls(32486), ls(32496)
		clearcache_string, name_insert, list_name_insert = ls(32497) % rd_string, self.insert_string % (rd_string.upper(), '%s'), (self.insert_string % (rd_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'real_debrid.rd_torrent_cloud', 'foldername': 'Cloud Storage', 'list_name': list_name_insert % cloud_string}, name_insert % cloud_string, iconImage='realdebrid.png')
		self._add_dir({'mode': 'real_debrid.rd_downloads', 'foldername': 'Real Debrid History', 'list_name': list_name_insert % history_string}, name_insert % history_string, iconImage='realdebrid.png')
		self._add_dir({'mode': 'real_debrid.rd_account_info', 'foldername': 'Account Info', 'list_name': list_name_insert % account_string}, name_insert % account_string, iconImage='realdebrid.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'rd_cloud', 'foldername': 'Clear Cache', 'list_name': list_name_insert % clearcache_string}, name_insert % clearcache_string, iconImage='realdebrid.png', isFolder=False)
		self._end_directory()

	def premiumize(self):
		pm_string, account_string, history_string, cloud_string = ls(32061), ls(32494), ls(32486), ls(32496)
		clearcache_string, name_insert, list_name_insert = ls(32497) % pm_string, self.insert_string % (pm_string.upper(), '%s'), (self.insert_string % (pm_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'premiumize.pm_torrent_cloud', 'foldername': 'Cloud Storage', 'list_name': list_name_insert % cloud_string}, name_insert % cloud_string, iconImage='premiumize.png')
		self._add_dir({'mode': 'premiumize.pm_transfers', 'foldername': 'Premiumize History', 'list_name': list_name_insert % history_string}, name_insert % history_string, iconImage='premiumize.png')
		self._add_dir({'mode': 'premiumize.pm_account_info', 'foldername': 'Account Info', 'list_name': list_name_insert % account_string}, name_insert % account_string, iconImage='premiumize.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'pm_cloud', 'foldername': 'Clear Cache', 'list_name': list_name_insert % clearcache_string}, name_insert % clearcache_string, iconImage='premiumize.png', isFolder=False)
		self._end_directory()

	def alldebrid(self):
		ad_string, account_string, history_string, cloud_string = ls(32063), ls(32494), ls(32486), ls(32496)
		clearcache_string, name_insert, list_name_insert = ls(32497) % ad_string, self.insert_string % (ad_string.upper(), '%s'), (self.insert_string % (ad_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'alldebrid.ad_torrent_cloud', 'foldername': 'Cloud Storage', 'list_name': list_name_insert % cloud_string}, name_insert % cloud_string, iconImage='alldebrid.png')
		self._add_dir({'mode': 'alldebrid.ad_transfers', 'foldername': 'All Debrid History', 'list_name': list_name_insert % history_string}, name_insert % history_string, iconImage='alldebrid.png')
		self._add_dir({'mode': 'alldebrid.ad_account_info', 'foldername': 'Account Info', 'list_name': list_name_insert % account_string}, name_insert % account_string, iconImage='alldebrid.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'ad_cloud', 'foldername': 'Clear Cache', 'list_name': list_name_insert % clearcache_string}, name_insert % clearcache_string, iconImage='alldebrid.png', isFolder=False)
		self._end_directory()

	def favourites(self):
		fav_string = ls(32453)
		name_insert, list_name_insert = self.insert_string % (fav_string.upper(), '%s'), (self.insert_string % ('%s', fav_string)).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'build_movie_list', 'action': 'favourites_movies', 'foldername': 'Movie Favourites', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='movies.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'favourites_tvshows', 'foldername': 'TV Show Favourites', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='tv.png')
		self._end_directory()

	def subscriptions(self):
		subs_string = ls(32194)
		name_insert, list_name_insert = self.insert_string % (subs_string.upper(), '%s'), (self.insert_string % ('%s', subs_string)).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'build_movie_list', 'action': 'subscriptions_movies', 'foldername': 'Fen Subscriptions', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='movies.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'subscriptions_tvshows', 'foldername': 'Fen Subscriptions', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='tv.png')
		self._end_directory()

	def kodi_library(self):
		klibrary_string, recentadded_string = ls(32100), ls(32498)
		recent_movies, recent_tvshows = '%s %s' % (recentadded_string, self.movies_string), '%s %s' % (recentadded_string, self.tvshows_string)
		name_insert, list_name_insert = self.insert_string % (klibrary_string.upper(), '%s'), (self.insert_string % (klibrary_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'build_movie_list', 'action': 'kodi_library_movies', 'foldername': 'Movies Kodi Library', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='movies.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'kodi_library_tvshows', 'foldername': 'TV Shows Kodi Library', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='tv.png')
		self._add_dir({'mode': 'build_kodi_library_recently_added', 'db_type': 'movies', 'foldername': 'Recently Added Movies Kodi Library', 'list_name': list_name_insert % recent_movies}, name_insert % recent_movies, iconImage='recently_added_movies.png')
		self._add_dir({'mode': 'build_kodi_library_recently_added', 'db_type': 'episodes', 'foldername': 'Recently Added Movies Kodi Library', 'list_name': list_name_insert % recent_tvshows}, name_insert % recent_tvshows, iconImage='recently_added_episodes.png')
		self._end_directory()

	def my_content(self):
		trakt_string, imdb_string, collection_string, watchlist_string, lists_string, widgets_string = ls(32037), ls(32064), ls(32499), ls(32500), ls(32501), ls(32085)
		t_name_insert, t_list_name_insert = self.insert_string % (trakt_string.upper(), '%s'), (self.insert_string % (trakt_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		i_name_insert, i_list_name_insert = self.insert_string % (imdb_string.upper(), '%s'), (self.insert_string % (imdb_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		trakt_status = get_setting('trakt_user') not in ('', None)
		imdb_status = get_setting('imdb_user') not in ('', None)
		if trakt_status or imdb_status:
			if trakt_status:
				self._add_dir({'mode': 'navigator.trakt_collections', 'foldername': 'My Trakt Collections', 'list_name': t_list_name_insert % collection_string}, t_name_insert % collection_string, iconImage='trakt.png')
				self._add_dir({'mode': 'navigator.trakt_watchlists', 'foldername': 'My Trakt Watchlists', 'list_name': t_list_name_insert % watchlist_string}, t_name_insert % watchlist_string, iconImage='trakt.png')
				self._add_dir({'mode': 'navigator.trakt_lists', 'foldername': 'My Trakt Lists', 'list_name': t_list_name_insert % lists_string}, t_name_insert % lists_string, iconImage='trakt.png')
				self._add_dir({'mode': 'navigator.trakt_widgets', 'foldername': 'Trakt Widgets', 'list_name': t_list_name_insert % widgets_string}, t_name_insert % widgets_string, iconImage='trakt.png')
			if imdb_status:
				self._add_dir({'mode': 'navigator.imdb_watchlists', 'foldername': 'My IMDb Watchlists', 'list_name': i_list_name_insert % watchlist_string}, i_name_insert % watchlist_string, iconImage='imdb.png')
				self._add_dir({'mode': 'navigator.imdb_lists', 'foldername': 'My IMDb Lists', 'list_name': i_list_name_insert % lists_string}, i_name_insert % lists_string, iconImage='imdb.png')
			self._end_directory()
		else:
			from modules.nav_utils import notification
			notification(ls(33022))

	def trakt_collections(self):
		trakt_string, collection_string = ls(32037), ls(32499)
		trakt_collection_string = '%s %s' % (trakt_string, collection_string)
		name_insert, list_name_insert = self.insert_string % (trakt_collection_string.upper(), '%s'), (self.insert_string % (trakt_collection_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'build_movie_list', 'action': 'trakt_collection', 'foldername': 'Trakt Movie Collection', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='trakt.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'trakt_collection', 'foldername': 'Trakt TV Show Collection', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='trakt.png')
		self._end_directory()

	def trakt_watchlists(self):
		trakt_string, watchlist_string = ls(32037), ls(32500)
		trakt_watchlist_string = '%s %s' % (trakt_string, watchlist_string)
		name_insert, list_name_insert = self.insert_string % (trakt_watchlist_string.upper(), '%s'), (self.insert_string % (trakt_watchlist_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'build_movie_list', 'action': 'trakt_watchlist', 'foldername': 'Trakt Movie Watchlist', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='trakt.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'trakt_watchlist', 'foldername': 'Trakt TV Show Watchlist', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='trakt.png')
		self._end_directory()

	def trakt_lists(self):
		trakt_string, user_string, lists_string, my_lists_string, liked_lists_string, recommended_string, calendar_string = ls(32037), ls(32065), ls(32501), ls(32454), ls(32502), ls(32503), ls(32081)
		trending_user_lists, popular_user_lists = '%s %s %s' % (ls(32458), user_string, lists_string), '%s %s %s' % (ls(32459), user_string, lists_string)
		search_lists, name_insert, list_name_insert = '%s %s' % (ls(32477), lists_string), self.insert_string % (trakt_string.upper(), '%s'), (self.insert_string % (trakt_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'trakt.list.get_trakt_lists', 'list_type': 'my_lists', 'build_list': 'true', 'foldername': 'Trakt My Lists', 'list_name': list_name_insert % my_lists_string}, name_insert % my_lists_string, iconImage='trakt.png')
		self._add_dir({'mode': 'trakt.list.get_trakt_lists', 'list_type': 'liked_lists', 'build_list': 'true', 'foldername': 'Trakt Liked Lists', 'list_name': list_name_insert % liked_lists_string}, name_insert % liked_lists_string, iconImage='trakt.png')
		self._add_dir({'mode': 'navigator.trakt_recommendations', 'foldername': 'Trakt Recommended Lists', 'list_name': list_name_insert % recommended_string}, name_insert % recommended_string, iconImage='trakt.png')
		self._add_dir({'mode': 'trakt.lists.get_trakt_my_calendar', 'foldername': 'Trakt Calendar', 'list_name': list_name_insert % calendar_string}, name_insert % calendar_string, iconImage='trakt.png')
		self._add_dir({'mode': 'trakt.list.get_trakt_trending_popular_lists', 'list_type': 'trending', 'foldername': 'Trakt Trending User Lists', 'list_name': list_name_insert % trending_user_lists}, name_insert % trending_user_lists, iconImage='trakt.png')
		self._add_dir({'mode': 'trakt.list.get_trakt_trending_popular_lists', 'list_type': 'popular', 'foldername': 'Trakt Most Popular User Lists', 'list_name': list_name_insert % popular_user_lists}, name_insert % popular_user_lists, iconImage='trakt.png')
		self._add_dir({'mode': 'trakt.list.search_trakt_lists', 'foldername': 'Search Trakt Lists', 'list_name': list_name_insert % search_lists}, name_insert % search_lists, iconImage='trakt.png')
		self._end_directory()

	def trakt_recommendations(self):
		recommended_string = ls(32503)
		name_insert, list_name_insert = self.insert_string % (recommended_string.upper(), '%s'), (self.insert_string % (recommended_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'build_movie_list', 'action': 'trakt_recommendations', 'foldername': 'Recommended Movies', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='trakt.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'trakt_recommendations', 'foldername': 'Recommended TV Shows', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='trakt.png')
		self._end_directory()

	def trakt_widgets(self):
		# use 'new_page' to pass the type of list to be processed when using 'trakt_collection_widgets'...
		collection_string = ls(32499)
		movies_recently_added_string, movies_random_string = '%s %s' % (ls(32498), self.movies_string), '%s %s' % (ls(32504), self.movies_string)
		tvshows_recently_added_string, tvshows_random_string, recently_aired_string = '%s %s' % (ls(32498), self.tvshows_string), '%s %s' % (ls(32504), self.tvshows_string), '%s %s' % (ls(32505), ls(32506))
		name_insert, list_name_insert = self.insert_string % (collection_string.upper(), '%s'), (self.insert_string % (collection_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'build_movie_list', 'action': 'trakt_collection_widgets', 'new_page': 'recent', 'foldername': 'Trakt Collection Recently Added Movies', 'list_name': list_name_insert % movies_recently_added_string}, name_insert % movies_recently_added_string, iconImage='trakt.png')
		self._add_dir({'mode': 'build_movie_list', 'action': 'trakt_collection_widgets', 'new_page': 'random', 'foldername': 'Trakt Collection Random Movies', 'list_name': list_name_insert % movies_random_string}, name_insert % movies_random_string, iconImage='trakt.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'trakt_collection_widgets', 'new_page': 'recent', 'foldername': 'Trakt Collection Recently Added TV Shows', 'list_name': list_name_insert % tvshows_recently_added_string}, name_insert % tvshows_recently_added_string, iconImage='trakt.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'trakt_collection_widgets', 'new_page': 'random', 'foldername': 'Trakt Collection Random TV Shows', 'list_name': list_name_insert % tvshows_random_string}, name_insert % tvshows_random_string, iconImage='trakt.png')
		self._add_dir({'mode': 'trakt.list.get_trakt_my_calendar', 'recently_aired': 'true', 'foldername': 'Trakt Collection Recently Aired Episodes', 'list_name': list_name_insert % recently_aired_string}, name_insert % recently_aired_string, iconImage='trakt.png')
		self._end_directory()

	def imdb_watchlists(self):
		imdb_string, watchlist_string = ls(32064), ls(32500)
		imdb_watchlist_string = '%s %s' % (imdb_string, watchlist_string)
		name_insert, list_name_insert = self.insert_string % (imdb_watchlist_string.upper(), '%s'), (self.insert_string % (imdb_watchlist_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'build_movie_list', 'action': 'imdb_watchlist', 'foldername': 'IMDb Watchlist Movies', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='imdb.png')
		self._add_dir({'mode': 'build_tvshow_list', 'action': 'imdb_watchlist', 'foldername': 'IMDb Watchlist TV Show', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='imdb.png')
		self._end_directory()

	def imdb_lists(self):
		imdb_string, lists_string = ls(32064), ls(32501)
		imdb_lists_string = '%s %s' % (imdb_string, lists_string)
		name_insert, list_name_insert = self.insert_string % (imdb_lists_string.upper(), '%s'), (self.insert_string % (imdb_lists_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'imdb_build_user_lists', 'db_type': 'movies', 'foldername': 'My IMDb Movie Lists', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='imdb.png')
		self._add_dir({'mode': 'imdb_build_user_lists', 'db_type': 'tvshows', 'foldername': 'My IMDb TV Shows Lists', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='imdb.png')
		self._end_directory()

	def search(self):
		search_string, people_string, history_string = ls(32450), ls(32507), ls(32486)
		movie_history_string, tvshows_history_string, people_history_string = '%s %s' % (self.movies_string, history_string), '%s %s' % (self.tvshows_string, history_string), '%s %s' % (people_string, history_string)
		name_insert, list_name_insert = self.insert_string % (search_string.upper(), '%s'), (self.insert_string % (search_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'get_search_term', 'db_type': 'movie', 'default_search_item': 'true', 'foldername': 'Movie Search', 'list_name': list_name_insert % self.movies_string}, name_insert % self.movies_string, iconImage='search_movie.png', isFolder=False)
		self._add_dir({'mode': 'get_search_term', 'db_type': 'tv_show', 'default_search_item': 'true', 'foldername': 'TV Show Search', 'list_name': list_name_insert % self.tvshows_string}, name_insert % self.tvshows_string, iconImage='search_tv.png', isFolder=False)
		self._add_dir({'mode': 'people_search.search', 'foldername': 'People Search', 'list_name': list_name_insert % people_string}, name_insert % people_string, iconImage='genre_comedy.png', isFolder=True)
		self._add_dir({'mode': 'search_history', 'action': 'movie', 'foldername': 'History Movie Search', 'list_name': list_name_insert % movie_history_string}, name_insert % movie_history_string, iconImage='search.png')
		self._add_dir({'mode': 'search_history', 'action': 'tvshow', 'foldername': 'History TV Show Search', 'list_name': list_name_insert % tvshows_history_string}, name_insert % tvshows_history_string, iconImage='search.png')
		self._add_dir({'mode': 'search_history', 'action': 'people', 'foldername': 'History People Search', 'list_name': list_name_insert % people_history_string}, name_insert % people_history_string, iconImage='search.png')
		self._end_directory()

	def tools(self):
		from modules.nav_utils import get_kodi_version
		tools_string, manager_string, changelog_string, ext_string, short_string, source_string, next_update_string = ls(32456), ls(32513), ls(32508), ls(32118), ls(32514), ls(32515), ls(32519)
		update_subs_string, log_viewer_string, tips_string, views_string, backup_string, clean_string, traktsync_string, lang_inv_string = ls(32520), ls(32509), ls(32518), ls(32510), ls(32511), ls(32512), ls(32516), ls(33017)
		changelog_log_viewer_string, scrapers_manager_string = '%s & %s' % (changelog_string, log_viewer_string), '%s %s' % (ext_string, manager_string)
		shortcut_manager_string, source_manager_string = '%s %s' % (short_string, manager_string), '%s %s' % (source_string, manager_string)
		name_insert, list_name_insert = self.insert_string % (tools_string.upper(), '%s'), (self.insert_string % (tools_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		display_time = '' if settings.subscription_update() == False else '[COLOR=grey]| %s: %s[/COLOR]' % (next_update_string, str(get_setting('service_time')))
		self._add_dir({'mode': 'navigator.changelogs', 'foldername': 'Changelogs & Log Viewer', 'list_name': list_name_insert % changelog_log_viewer_string}, name_insert % changelog_log_viewer_string, iconImage='settings2.png')
		self._add_dir({'mode': 'navigator.tips', 'foldername': 'Tips for Fen Use', 'list_name': list_name_insert % tips_string}, name_insert % tips_string, iconImage='settings2.png')
		self._add_dir({'mode': 'navigator.set_view_modes', 'foldername': 'Set Views', 'list_name': list_name_insert % views_string}, name_insert % views_string, iconImage='settings2.png')
		self._add_dir({'mode': 'navigator.backup_restore', 'foldername': 'Backup/Restore Fen User Data', 'list_name': list_name_insert % backup_string}, name_insert % backup_string, iconImage='settings2.png')
		self._add_dir({'mode': 'navigator.clear_info', 'foldername': 'Clear Databases and Clean Settings Files', 'list_name': list_name_insert % clean_string}, name_insert % clean_string, iconImage='settings2.png')
		self._add_dir({'mode': 'navigator.external_scrapers', 'foldername': 'External Scrapers Manager', 'list_name': list_name_insert % scrapers_manager_string}, name_insert % scrapers_manager_string, iconImage='settings2.png')
		self._add_dir({'mode': 'navigator.shortcut_folders', 'foldername': 'Shortcut Folders Manager', 'list_name': list_name_insert % shortcut_manager_string}, name_insert % shortcut_manager_string, iconImage='settings2.png')
		self._add_dir({'mode': 'navigator.sources_folders', 'foldername': 'Sources Folders Manager', 'list_name': list_name_insert % source_manager_string}, name_insert % source_manager_string, iconImage='settings2.png')
		self._add_dir({'mode': 'update_subscriptions', 'foldername': 'Update Subscriptions', 'list_name': list_name_insert % backup_string}, '%s %s' % (name_insert % update_subs_string, display_time), iconImage='settings2.png', isFolder=False)
		if settings.watched_indicators() == 1: self._add_dir({'mode': 'trakt_sync_watched_to_fen', 'refresh': True, 'foldername': 'ReSync Fen Watched to Trakt Watched', 'list_name': list_name_insert % traktsync_string}, name_insert % traktsync_string, iconImage='settings2.png', isFolder=False)
		if get_kodi_version() >= 18: self._add_dir({'mode': 'toggle_language_invoker', 'foldername': 'Set Language Invoker', 'list_name': list_name_insert % lang_inv_string}, name_insert % lang_inv_string, iconImage='settings2.png', isFolder=False)
		self._end_directory()

	def settings(self):
		settings_string, general_string, accounts_string, notifi_string, nextep_string, trakt_string, intscrapers_string, extscrapers_string = ls(32247), ls(32001), ls(32050), ls(32211), ls(32071), ls(32037), ls(32096), ls(32118)
		results_string, playback_string, parentcontrol_string, subs_string, downs_string, external_string = ls(32139), ls(32174), ls(32999), ls(32194), ls(32107), ls(32521)
		fenom_scr_string, meta_string, myaccounts_str = '%s (%s)' % (ls(32522), external_string), '%s (%s)' % (ls(32523), external_string), '%s (%s)' % (ls(33025), external_string)
		name_insert, list_name_insert = self.insert_string % (settings_string.upper(), '%s'), (self.insert_string % (settings_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'open_settings', 'query': '0.0', 'foldername': 'General', 'list_name': list_name_insert % general_string}, name_insert % general_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '1.0', 'foldername': 'Accounts', 'list_name': list_name_insert % accounts_string}, name_insert % accounts_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '2.0', 'foldername': 'Notifications', 'list_name': list_name_insert % notifi_string}, name_insert % notifi_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '3.0', 'foldername': 'Next Episodes', 'list_name': list_name_insert % nextep_string}, name_insert % nextep_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '4.0', 'foldername': 'Trakt', 'list_name': list_name_insert % trakt_string}, name_insert % trakt_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '5.0', 'foldername': 'Internal Scrapers', 'list_name': list_name_insert % intscrapers_string}, name_insert % intscrapers_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '6.0', 'foldername': 'External Scrapers', 'list_name': list_name_insert % extscrapers_string}, name_insert % extscrapers_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '7.0', 'foldername': 'Results', 'list_name': list_name_insert % results_string}, name_insert % results_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '8.0', 'foldername': 'Playback', 'list_name': list_name_insert % playback_string}, name_insert % playback_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '9.0', 'foldername': 'Parental Controls', 'list_name': list_name_insert % parentcontrol_string}, name_insert % parentcontrol_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '10.0', 'foldername': 'Subscriptions', 'list_name': list_name_insert % subs_string}, name_insert % subs_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'open_settings', 'query': '11.0', 'foldername': 'Downloads', 'list_name': list_name_insert % downs_string}, name_insert % downs_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'external_settings', 'ext_addon': 'script.module.tikimeta', 'foldername': 'Tiki Meta Settings', 'list_name': list_name_insert % meta_string}, name_insert % meta_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'external_settings', 'ext_addon': 'script.module.fenomscrapers', 'foldername': 'Fenomscrapers 2 Settings', 'list_name': list_name_insert % fenom_scr_string}, name_insert % fenom_scr_string, iconImage='settings.png', isFolder=False)
		self._add_dir({'mode': 'external_settings', 'ext_addon': 'script.module.myaccounts', 'foldername': 'My Accounts Settings', 'list_name': list_name_insert % myaccounts_str}, name_insert % myaccounts_str, iconImage='settings.png', isFolder=False)
		self._end_directory()

	def backup_restore(self):
		back_restore_string, back_string, restore_string = ls(32046), ls(32048), ls(32049)
		name_insert, list_name_insert = self.insert_string % (back_restore_string.upper(), '%s'), (self.insert_string % (back_restore_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		self._add_dir({'mode': 'backup_settings', 'foldername': 'Backup Fen User Data', 'list_name': list_name_insert % back_string}, name_insert % back_string, iconImage='backup_export.png', isFolder=False)
		self._add_dir({'mode': 'restore_settings', 'foldername': 'Restore Fen User Data', 'list_name': list_name_insert % restore_string}, name_insert % restore_string, iconImage='backup_import.png', isFolder=False)
		self._end_directory()

	def clear_info(self):
		cache_string, clear_cache_base_string, clean_string, all_string, settings_string, fav_string, subs_string = ls(32524), ls(32497), ls(32526), ls(32525), ls(32247), ls(32453), ls(32194)
		clean_set_cache_str, clean_set_cache_str_list_name = '[B]%s:[/B] %s %s %s' % (clean_string.upper(), clean_string, ls(32247), ls(32524)), '%s %s %s' % (clean_string, ls(32247), ls(32524))
		clean_all_string, clean_all_string_list_name, search_string = '[B]%s:[/B] %s %s %s' % (clean_string.upper(), clean_string, all_string, settings_string), '%s %s %s' % (clean_string, all_string, settings_string), '%s %s' % (ls(32450), ls(32486))
		clear_all_string, clear_meta_string, clear_list_string, clear_trakt_string = clear_cache_base_string % all_string, clear_cache_base_string % ls(32527), clear_cache_base_string % ls(32501), clear_cache_base_string % ls(32037)
		clear_imdb_string, clear_intscrapers_string, clear_extscrapers_string = clear_cache_base_string % ls(32064), clear_cache_base_string % ls(32096), clear_cache_base_string % ls(32118)
		clear_rd_string, clear_pm_string, clear_ad_string = clear_cache_base_string % ls(32054), clear_cache_base_string % ls(32061), clear_cache_base_string % ls(32063)
		clear_fav_string, clear_search_string = clear_cache_base_string % fav_string, clear_cache_base_string % search_string
		name_insert, list_name_insert = self.insert_string % (cache_string.upper(), '%s'), (self.insert_string % (cache_string, '%s')).replace('[B]', '').replace(': [/B]', ' ')
		clear_all_amble = '[B][I][COLOR=grey] (%s %s, %s & %s)[/COLOR][/I][/B]' % (ls(32189), fav_string, subs_string, search_string)
		clear_all = '[B]%s:[/B] %s' % (clear_all_string.upper(), clear_all_amble)
		self._add_dir({'mode': 'clean_settings', 'foldername': 'Clean Settings Files', 'list_name': clean_all_string_list_name}, clean_all_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_settings_window_properties', 'foldername': 'clear_settings_window_properties', 'list_name': clean_set_cache_str_list_name}, clean_set_cache_str, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_all_cache', 'foldername': 'Clear All Cache', 'list_name': clear_all_string}, clear_all, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_favourites', 'foldername': 'Clear Fen Favourites', 'list_name': list_name_insert % clear_fav_string}, name_insert % clear_fav_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_search_history', 'foldername': 'Clear Search History', 'list_name': list_name_insert % clear_search_string}, name_insert % clear_search_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'meta', 'foldername': 'Clear Meta Cache', 'list_name': list_name_insert % clear_meta_string}, name_insert % clear_meta_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'list', 'foldername': 'Clear List Cache', 'list_name': list_name_insert % clear_list_string}, name_insert % clear_list_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'trakt', 'foldername': 'Clear Trakt Cache', 'list_name': list_name_insert % clear_trakt_string}, name_insert % clear_trakt_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'imdb', 'foldername': 'Clear IMDb Cache', 'list_name': list_name_insert % clear_imdb_string}, name_insert % clear_imdb_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'internal_scrapers', 'foldername': 'Clear Internal Scrapers Cache', 'list_name': list_name_insert % clear_intscrapers_string}, name_insert % clear_intscrapers_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'external_scrapers', 'foldername': 'Clear External Scrapers Cache', 'list_name': list_name_insert % clear_extscrapers_string}, name_insert % clear_extscrapers_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'rd_cloud', 'foldername': 'Clear Real Debrid Cache', 'list_name': list_name_insert % clear_rd_string}, name_insert % clear_rd_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'pm_cloud', 'foldername': 'Clear Premiumize Cache', 'list_name': list_name_insert % clear_pm_string}, name_insert % clear_pm_string, iconImage='settings2.png', isFolder=False)
		self._add_dir({'mode': 'clear_cache', 'cache': 'ad_cloud', 'foldername': 'Clear Cache', 'list_name': list_name_insert % clear_ad_string}, name_insert % clear_ad_string, iconImage='settings2.png', isFolder=False)
		self._end_directory()

	def external_scrapers(self):
		icon = settings.ext_addon('script.module.fenomscrapers').getAddonInfo('icon')
		fail_color = 'crimson'
		all_color = 'mediumvioletred'
		hosters_color = get_setting('hoster.identify')
		torrent_color = get_setting('torrent.identify')
		enable_string, disable_string, specific_string, all_string, failing_string, ext_scrapers_string, reset_string, stats_string, scrapers_string, hoster_string, torrent_string = ls(32055), ls(32024), ls(32536), ls(32525), ls(32529), ls(32118), ls(32531), ls(32532), ls(32533), ls(33031), ls(32535)
		failing_scrapers_string, all_scrapers_string, hosters_string = '%s %s' % (failing_string, scrapers_string), '%s %s' % (all_string, scrapers_string), '%s %s' % (hoster_string, scrapers_string)
		torrent_scrapers_string, fail1_string, fail2_string = '%s %s' % (torrent_string, scrapers_string), '%s %s %s' % (disable_string, failing_string, ext_scrapers_string), '%s %s %s %s' % (reset_string, failing_string, ext_scrapers_string, stats_string)
		enable_string_base, disable_string_base, enable_disable_string_base = '%s %s %s %s' % (enable_string, all_string, '%s', scrapers_string), '%s %s %s %s' % (disable_string, all_string, '%s', scrapers_string), '%s/%s %s %s %s' % (enable_string, disable_string, specific_string, '%s', scrapers_string)
		failure_base, all_scrapers_base = '[COLOR %s][B]%s : [/B][/COLOR] %s' % (fail_color, failing_scrapers_string.upper(), '%s'), '[COLOR %s][B]%s : [/B][/COLOR] %s' % (all_color, all_scrapers_string.upper(), '%s')
		debrid_scrapers_base, torrent_scrapers_base = '[COLOR %s][B]%s : [/B][/COLOR] %s' % (hosters_color, hosters_string.upper(), '%s'), '[COLOR %s][B]%s : [/B][/COLOR] %s' % (torrent_color, torrent_scrapers_string.upper(), '%s')
		self._add_dir({'mode': 'external_scrapers_disable', 'foldername': 'Disable Failing External Scrapers', 'list_name': fail1_string}, failure_base % fail1_string, iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_reset_stats', 'foldername': 'Reset Failing External Scraper Stats', 'list_name': fail2_string}, failure_base % fail2_string, iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_toggle_all', 'folder': 'all', 'setting': 'true', 'foldername': 'Enable All Scrapers', 'list_name': enable_string_base % ''}, all_scrapers_base % (enable_string_base % ''), iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_toggle_all', 'folder': 'all', 'setting': 'false', 'foldername': 'Disable All Scrapers', 'list_name': disable_string_base % ''}, all_scrapers_base % (disable_string_base % ''), iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_enable_disable_specific_all', 'folder': 'all', 'foldername': 'Enable/Disable Specific Scrapers', 'list_name': enable_disable_string_base % ''}, all_scrapers_base % (enable_disable_string_base % ''), iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_toggle_all', 'folder': 'hosters', 'setting': 'true', 'foldername': 'Enable All Debrid Scrapers', 'list_name': enable_string_base % hoster_string}, debrid_scrapers_base % (enable_string_base % hoster_string), iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_toggle_all', 'folder': 'hosters', 'setting': 'false', 'foldername': 'Disable All Debrid Scrapers', 'list_name': disable_string_base % hoster_string}, debrid_scrapers_base % (disable_string_base % hoster_string), iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_enable_disable_specific_all', 'folder': 'hosters', 'foldername': 'Enable/Disable Specific Debrid Scrapers', 'list_name': enable_disable_string_base % hoster_string}, debrid_scrapers_base % (enable_disable_string_base % hoster_string), iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_toggle_all', 'folder': 'torrents', 'setting': 'true', 'foldername': 'Enable All Torrent Scrapers', 'list_name': enable_string_base % torrent_string}, torrent_scrapers_base % (enable_string_base % torrent_string), iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_toggle_all', 'folder': 'torrents', 'setting': 'false', 'foldername': 'Disable All Torrent Scrapers', 'list_name': disable_string_base % torrent_string}, torrent_scrapers_base % (disable_string_base % torrent_string), iconImage=icon, isFolder=False)
		self._add_dir({'mode': 'external_scrapers_enable_disable_specific_all', 'folder': 'torrents', 'foldername': 'Enable/Disable Specific Torrent Scrapers', 'list_name': enable_disable_string_base % torrent_string}, torrent_scrapers_base % (enable_disable_string_base % torrent_string), iconImage=icon, isFolder=False)
		self._end_directory()

	def set_view_modes(self):
		set_views_string, lists_string, root_string, movies_string, tvshows_string, season_string, episode_string, premium_files_string, images_string = ls(32510), ls(32501), ls(32457), ls(32028), ls(32029), ls(32537), ls(32506), ls(32485), ls(32798)
		ep_lists_string, trakt_lists_string, search_results_string = '%s %s' % (episode_string, lists_string), '%s %s' % (ls(32037), lists_string), '%s %s' % (ls(32450), ls(32139))
		name_insert = self.insert_string % (set_views_string.upper(), '%s')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.main', 'view_type': 'addons', 'exclude_external': 'true'},name_insert % root_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.movies', 'view_type': 'movies', 'exclude_external': 'true'},name_insert % movies_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.tvshows', 'view_type': 'tvshows', 'exclude_external': 'true'},name_insert % tvshows_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.seasons', 'view_type': 'seasons', 'exclude_external': 'true'},name_insert % season_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.episodes', 'view_type': 'episodes', 'exclude_external': 'true'},name_insert % episode_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.episode_lists', 'view_type': 'episodes', 'exclude_external': 'true'},name_insert % ep_lists_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.trakt_list', 'view_type': 'movies', 'exclude_external': 'true'},name_insert % trakt_lists_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.premium', 'view_type': 'files', 'exclude_external': 'true'},name_insert % premium_files_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.search_results', 'view_type': 'files', 'exclude_external': 'true'},name_insert % search_results_string, iconImage='settings.png')
		self._add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.images', 'view_type': 'images', 'exclude_external': 'true'},name_insert % images_string, iconImage='settings.png')
		self._end_directory()

	def changelogs(self):
		fen_string, changelog_string, tikimeta_string, fenomscrapers_string, myaccounts_string, log_viewer_string, kodi_string = ls(32036), ls(32508), ls(32523), ls(32522), ls(33025), ls(32509), ls(32538)
		fen_version, fen_icon = settings.addon().getAddonInfo('version'), settings.addon().getAddonInfo('icon')
		scrapers_version, scrapers_icon = settings.ext_addon('script.module.fenomscrapers').getAddonInfo('version'), settings.ext_addon('script.module.fenomscrapers').getAddonInfo('icon')
		meta_version, meta_icon = settings.ext_addon('script.module.tikimeta').getAddonInfo('version'), settings.ext_addon('script.module.tikimeta').getAddonInfo('icon')
		myaccounts_version, myaccounts_icon = settings.ext_addon('script.module.myaccounts').getAddonInfo('version'), settings.ext_addon('script.module.myaccounts').getAddonInfo('icon')
		main_text_file, main_heading = xbmc.translatePath(os.path.join(addon_dir, "resources", "text", "changelog.txt")), '[B]%s : [/B] %s  [I](v.%s)[/I]' % (changelog_string.upper(), fen_string, fen_version)
		meta_text_file, meta_heading = xbmc.translatePath(os.path.join(xbmc.translatePath(settings.ext_addon('script.module.tikimeta').getAddonInfo('path')), "changelog.txt")), '[B]%s : [/B] %s  [I](v.%s)[/I]' % (changelog_string.upper(), tikimeta_string, meta_version)
		scrapers_text_file, scrapers_heading = xbmc.translatePath(os.path.join(xbmc.translatePath(settings.ext_addon('script.module.fenomscrapers').getAddonInfo('path')), "changelog.txt")), '[B]%s : [/B] %s  [I](v.%s)[/I]' % (changelog_string.upper(), fenomscrapers_string, scrapers_version)
		myaccounts_text_file, myaccounts_heading = xbmc.translatePath(os.path.join(xbmc.translatePath(settings.ext_addon('script.module.myaccounts').getAddonInfo('path')), "changelog.txt")), '[B]%s : [/B] %s  [I](v.%s)[/I]' % (changelog_string.upper(), myaccounts_string, myaccounts_version)
		kodi_log_location, log_heading = os.path.join(xbmc.translatePath('special://logpath/'), 'kodi.log'), '[B]%s : [/B]%s %s' % (log_viewer_string.upper(), kodi_string, log_viewer_string)
		self._add_dir({'mode': 'show_text', 'text_file': main_text_file, 'heading': main_heading, 'foldername': main_heading, 'exclude_external': 'true'}, main_heading, iconImage=fen_icon, isFolder=False)
		self._add_dir({'mode': 'show_text', 'text_file': meta_text_file, 'heading': meta_heading, 'foldername': meta_heading, 'exclude_external': 'true'}, meta_heading, iconImage=meta_icon, isFolder=False)
		self._add_dir({'mode': 'show_text', 'text_file': scrapers_text_file, 'heading': scrapers_heading, 'foldername': scrapers_heading, 'exclude_external': 'true'}, scrapers_heading, iconImage=scrapers_icon, isFolder=False)
		self._add_dir({'mode': 'show_text', 'text_file': myaccounts_text_file, 'heading': myaccounts_heading, 'foldername': myaccounts_heading, 'exclude_external': 'true'}, myaccounts_heading, iconImage=myaccounts_icon, isFolder=False)
		self._add_dir({'mode': 'show_text', 'text_file': kodi_log_location, 'heading': log_heading, 'usemono': 'True', 'foldername': 'Kodi Log Viewer', 'exclude_external': 'true'}, log_heading, iconImage='lists.png', isFolder=False)
		self._end_directory()

	def certifications(self):
		if self.params.get('menu_type') == 'movie': from modules.nav_utils import movie_certifications as certifications
		else: from modules.nav_utils import tvshow_certifications as certifications
		mode = 'build_movie_list' if self.params.get('menu_type') == 'movie' else 'build_tvshow_list'
		action = 'tmdb_movies_certifications' if self.params.get('menu_type') == 'movie' else 'trakt_tv_certifications'
		list_name_insert = self.make_list_name(self.params.get('menu_type'))
		for cert in certifications():
			list_name = '%s %s %s' % (list_name_insert, cert.upper(), ls(32473))
			self._add_dir({'mode': mode, 'action': action, 'certification': cert, 'foldername': cert.upper(), 'list_name': list_name}, cert.upper(), iconImage='certifications.png')
		self._end_directory()

	def languages(self):
		from modules.nav_utils import languages
		mode = 'build_movie_list' if self.params.get('menu_type') == 'movie' else 'build_tvshow_list'
		action = 'tmdb_movies_languages' if self.params.get('menu_type') == 'movie' else 'tmdb_tv_languages'
		list_name_insert = self.make_list_name(self.params.get('menu_type'))
		for lang in languages():
			list_name = '%s %s %s' % (list_name_insert, lang[0], ls(32471))
			self._add_dir({'mode': mode, 'action': action, 'language': lang[1], 'foldername': lang, 'list_name': list_name}, lang[0], iconImage='languages.png')
		self._end_directory()

	def years(self):
		from modules.nav_utils import years
		mode = 'build_movie_list' if self.params.get('menu_type') == 'movie' else 'build_tvshow_list'
		action = 'tmdb_movies_year' if self.params.get('menu_type') == 'movie' else 'tmdb_tv_year'
		list_name_insert = self.make_list_name(self.params.get('menu_type'))
		for i in years():
			list_name = '%s %s %s' % (list_name_insert, str(i), ls(32460))
			self._add_dir({'mode': mode, 'action': action, 'year': str(i), 'foldername': '%s - %s' % (str(i), self.params.get('menu_type')), 'list_name': list_name}, str(i), iconImage='calender.png')
		self._end_directory()

	def genres(self):
		mode = 'build_movie_list' if self.params.get('menu_type') == 'movie' else 'build_tvshow_list'
		action = 'tmdb_movies_genres' if self.params.get('menu_type') == 'movie' else 'tmdb_tv_genres'
		list_name_insert = self.make_list_name(self.params.get('menu_type'))
		if self.params.get('menu_type') == 'movie':  from modules.nav_utils import movie_genres as genre_list
		else: from modules.nav_utils import tvshow_genres as genre_list
		self._add_dir({'mode': mode, 'action': action, 'genre_list': json.dumps(genre_list()), 'exclude_external': 'true', 'foldername': 'Multiselect'}, ls(32789), iconImage='genres.png')
		for genre, value in sorted(genre_list().items()):
			list_name = '%s %s %s' % (list_name_insert, genre, ls(32470))
			self._add_dir({'mode': mode, 'action': action, 'genre_id': value[0], 'foldername': genre, 'list_name': list_name}, genre, iconImage=value[1])
		self._end_directory()

	def networks(self):
		from modules.nav_utils import networks
		list_name_insert = self.make_list_name(self.params.get('menu_type'))
		for item in sorted(networks(), key=lambda k: k['name']):
			list_name = '%s %s %s' % (list_name_insert, item['name'], ls(32480))
			self._add_dir({'mode': 'build_tvshow_list', 'action': 'tmdb_tv_networks', 'network_id': item['id'], 'foldername': item['name'], 'list_name': list_name}, item['name'], iconImage=item['logo'])
		self._end_directory()

	def trakt_mosts(self):
		final_mode = 'build_movie_list' if self.params.get('menu_type') == 'movie' else 'build_tvshow_list'
		action = 'trakt_movies_mosts' if self.params.get('menu_type') == 'movie' else 'trakt_tv_mosts'
		list_name_insert = self.make_list_name(self.params.get('menu_type'))
		trakt_mosts = {ls(32539): ['played', 'most__played.png'],
					   ls(32540): ['collected', 'most__collected.png'],
					   ls(32475): ['watched', 'most__watched.png']}
		mosts_string = ls(32469)
		name_insert = self.insert_string % (mosts_string.upper(), '%s')
		for most, value in trakt_mosts.items():
			list_name = '%s %s %s' % (list_name_insert, mosts_string, most)
			self._add_dir({'mode': 'navigator.trakt_mosts_duration', 'action': action, 'period_str': most, 'period': value[0], 'menu_type': self.params.get('menu_type'), 'final_mode': final_mode, 'iconImage': value[1], 'foldername': 'Most %s' % most, 'list_name': list_name}, name_insert % most, iconImage=value[1])
		self._end_directory()

	def trakt_mosts_duration(self):
		list_name_insert = self.make_list_name(self.params.get('menu_type'))
		mosts_string, most_str = ls(32469), ls(32970)
		this_week_string, this_month_string, this_year_string, all_time_string = '%s %s' % (ls(32544), ls(32541)), '%s %s' % (ls(32544), ls(32542)), '%s %s' % (ls(32544), ls(32543)), '%s %s' % (ls(32129), ls(32545))
		durations = [(this_week_string, 'weekly'), (this_month_string, 'monthly'), (this_year_string, 'yearly'), (all_time_string, 'all')]
		period_str = self.params['period_str']
		for duration, urlitem in durations:
			list_name = '%s %s %s %s' % (list_name_insert, mosts_string, period_str.capitalize(), duration)
			self._add_dir({'mode': self.params['final_mode'], 'action': self.params['action'], 'period': self.params['period'], 'duration': urlitem, 'foldername': duration, 'list_name': list_name}, most_str % (period_str.upper(), duration), iconImage=self.params['iconImage'])
		self._end_directory()

	def folder_navigator(self):
		from modules.utils import clean_file_name, normalize
		from caches import fen_cache
		def _process():
			for tup in items:
				item = tup[0]
				isFolder = tup[1]
				if sources_folders and isFolder:
					cm = []
					normalized_folder_name = normalize(item)
					link_folders_add = {'mode': 'link_folders', 'service': 'FOLDER', 'folder_name': normalized_folder_name, 'action': 'add'}
					link_folders_remove = {'mode': 'link_folders', 'service': 'FOLDER', 'folder_name': normalized_folder_name, 'action': 'remove'}
					string = 'FEN_FOLDER_%s' % normalized_folder_name
					current_link = _cache.get(string)
					if current_link: ending = '[COLOR=limegreen][B][I]\n%s[/I][/B][/COLOR]' % (linkedto_str % current_link)
					else: ending = ''
				else: ending = ''
				display = '%s%s' % (item, ending)
				url = os.path.join(folder_path, item)
				try: listitem = xbmcgui.ListItem(display, offscreen=True)
				except: listitem = xbmcgui.ListItem(display)
				listitem.setArt({'fanart': self.fanart})
				if sources_folders and isFolder:
					cm.append((link_str,'RunPlugin(%s)' % self._build_url(link_folders_add)))
					if ending != '': cm.append((clear_str,'RunPlugin(%s)' % self._build_url(link_folders_remove)))
					listitem.addContextMenuItems(cm)
				yield (url, listitem, isFolder)
		link_str, clear_str, linkedto_str = ls(32745), ls(32746), ls(32744)
		_cache = fen_cache.FenCache()
		folder_path = self.params['folder_path']
		sources_folders = self.params.get('sources_folders', None)
		if sources_folders: from modules.utils import normalize
		dirs, files = xbmcvfs.listdir(folder_path)
		items = [(i, True) for i in dirs] + [(i, False) for i in files]
		item_list = list(_process())
		xbmcplugin.addDirectoryItems(self.__handle__, item_list)
		xbmcplugin.addSortMethod(self.__handle__, xbmcplugin.SORT_METHOD_FILE)
		self._end_directory()
	
	def sources_folders(self):
		for source in ('folder1', 'folder2', 'folder3', 'folder4', 'folder5'):
			for db_type in ('movie', 'tvshow'):
				folder_path = settings.source_folders_directory(db_type, source)
				if not folder_path: continue
				name = '[B]%s (%s): %s[/B]\n     [I]%s[/I]' % (source.upper(), self.make_list_name(db_type).upper(), get_setting('%s.display_name' % source).upper(), folder_path)
				self._add_dir({'mode': 'navigator.folder_navigator','sources_folders': 'True', 'folder_path': folder_path, 'foldername': name, 'list_name': name}, name, iconImage='most__collected.png')
		self._end_directory()

	def tips(self):
		tips_location = xbmc.translatePath(os.path.join(addon_dir, "resources", "text", "tips"))
		files = sorted(xbmcvfs.listdir(tips_location)[1])
		icon = os.path.join(self.icon_directory, 'faq8.png')
		help_str, new_str, spotlight_str = ls(32487).upper(), ls(32857).upper(), ls(32858).upper()
		flags = ['%s!!!' % help_str, '%s!' % new_str, '%s!' % spotlight_str]
		tips_list = []
		name_insert = self.insert_string % (ls(32546).upper(), '%s')
		for tip in files:
			try:
				add_sort_top = False
				tip_name = name_insert % tip.replace('.txt', '')[4:]
				for i in flags:
					if i in tip_name:
						tip_name_replace = (flags[0], '[COLOR crimson][B]%s!!![/B][/COLOR]' % help_str) if i == flags[0]\
									  else (flags[1], '[COLOR chartreuse][B]%s![/B][/COLOR]' % new_str) if i == flags[1]\
									  else (flags[2], '[COLOR orange][B]%s![/B][/COLOR]' % spotlight_str)
						tip_name = tip_name.replace(tip_name_replace[0], tip_name_replace[1])
						sort_order = 0 if i == flags[0] else 1 if i == flags[1] else 2
						break
				else:
					sort_order = 3
				listitem = xbmcgui.ListItem(tip_name)
				listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': self.fanart, 'banner': icon})
				params = {'mode': 'show_text', 'heading': 'Fen', 'text_file': xbmc.translatePath(os.path.join(tips_location, tip))}
				url = self._build_url(params)
				tips_list.append({'sort_order': sort_order, 'listitem': (url, listitem, False)})
			except: pass
		item_list = sorted(tips_list, key=lambda x: x['sort_order'])
		xbmcplugin.addDirectoryItems(self.__handle__, [i['listitem'] for i in item_list])
		self._end_directory()

	def because_you_watched(self):
		from modules.indicators_bookmarks import get_watched_info_movie, get_watched_info_tv
		def _convert_fen_watched_episodes_info():
			final_list = []
			used_names = []
			_watched, _trakt = get_watched_info_tv()
			if not _trakt:
				for item in _watched:
					name = item[3]
					if not name in used_names:
						if item[3] == name:
							tv_show = [i for i in _watched if i[3] == name]
							season = max(tv_show)[1]
							episode = max(tv_show)[2]
							final_item = (tv_show[0][0], 'foo', [(season, episode),], tv_show[0][3], tv_show[0][4])
							final_list.append(final_item)
							used_names.append(name)
				_watched = final_list
			return _watched, _trakt
		db_type = self.params['menu_type']
		func = get_watched_info_movie if db_type == 'movie' else _convert_fen_watched_episodes_info
		key_index = 2 if db_type == 'movie' else 4
		name_index = 1 if db_type == 'movie' else 3
		tmdb_index = 0
		mode = 'build_movie_list' if db_type == 'movie' else 'build_tvshow_list'
		action = 'tmdb_movies_recommendations' if db_type == 'movie' else 'tmdb_tv_recommendations'
		recently_watched = func()[0]
		recently_watched = sorted(recently_watched, key=lambda k: k[key_index], reverse=True)
		because_string = ls(32474)
		because_insert = '[I]%s[/I]  [B]%s[/B]' % (because_string, '%s')
		for item in recently_watched:
			if db_type == 'movie':
				name = because_insert % item[name_index]
			else:
				season, episode = item[2][-1]
				name = because_insert % '%s - %sx%s' % (item[name_index], season, episode)
			tmdb_id = item[tmdb_index]
			self._add_dir({'mode': mode, 'action': action, 'sim_recom_name': name, 'sim_recom_tmdb': tmdb_id, 'sim_recom_imdb': None, 'foldername': name, 'exclude_external': 'true'}, name, iconImage='because_you_watched.png')
		self._end_directory()

	def view_chooser(self):
		set_view_string = ls(32547)
		self._add_dir({'mode': 'navigator.set_views', 'view_setting_id': self.params.get('view_setting_id'), 'title': self.params.get('title'), 'view_type': self.params.get('view_type'), 'exclude_external': 'true'}, set_view_string, iconImage='settings.png', isFolder=False)
		xbmcplugin.setContent(self.__handle__, self.params.get('view_type'))
		xbmcplugin.endOfDirectory(self.__handle__)
		setView(self.params.get('view_setting_id'), self.params.get('view_type'))

	def set_views(self):
		from modules.nav_utils import notification
		VIEWS_DB = os.path.join(profile_dir, "views.db")
		settings.check_database(VIEWS_DB)
		view_type = self.params.get('view_setting_id')
		view_id = str(xbmcgui.Window(xbmcgui.getCurrentWindowId()).getFocusId())
		dbcon = database.connect(VIEWS_DB)
		dbcon.execute("DELETE FROM views WHERE view_type = '%s'" % (str(view_type)))
		dbcon.execute("INSERT INTO views VALUES (?, ?)", (str(view_type), str(view_id)))
		dbcon.commit()
		notification(xbmc.getInfoLabel('Container.Viewmode').upper(), time=2000)

	def make_list_name(self, menu_type):
		return menu_type.replace('tvshow', self.tvshows_string).replace('movie', self.movies_string)
	
	def shortcut_folders(self):
		def _make_icon(chosen_icon):
			return os.path.join(self.icon_directory, chosen_icon)
		def _make_new_item():
			icon = _make_icon('new.png')
			display_name = '[I]%s...[/I]' % ls(32702)
			url_params = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'add_shortcut_folder'}
			url = self._build_url(url_params)
			listitem = xbmcgui.ListItem(display_name)
			listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': self.fanart, 'banner': icon})
			xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=listitem, isFolder=False)
		dbcon = database.connect(NAVIGATOR_DB)
		dbcur = dbcon.cursor()
		dbcur.execute("SELECT list_name, list_contents FROM navigator WHERE list_type = ?", ('shortcut_folder',))
		folders = dbcur.fetchall()
		try: folders = sorted([(str(i[0]), i[1]) for i in folders], key=lambda s: s[0].lower())
		except: folders = []
		_make_new_item()
		short_str = ls(32514)
		delete_str = ls(32703)
		all_str = ls(32704)
		icon = os.path.join(self.icon_directory, 'furk.png')
		for i in folders:
			try:
				cm = []
				name = i[0]
				display_name = '[B]%s : [/B] %s ' % (short_str.upper(), i[0])
				contents = json.loads(i[1])
				url_params = {"iconImage": "furk.png", 
							"mode": "navigator.build_shortcut_folder_lists",
							"action": name,
							"name": name, 
							"foldername": name,
							"shortcut_folder": 'True',
							"external_list_item": 'True',
							"shortcut_folder": 'True',
							"contents": contents}
				remove_params = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'delete_shortcut_folder', 'list_name': name}
				remove_all_params = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'remove_all_shortcut_folders'}
				url = self._build_url(url_params)
				listitem = xbmcgui.ListItem(display_name)
				listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': self.fanart, 'banner': icon})
				cm.append((delete_str,'RunPlugin(%s)'% self._build_url(remove_params)))
				cm.append((all_str,'RunPlugin(%s)'% self._build_url(remove_all_params)))
				listitem.addContextMenuItems(cm)
				xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=listitem, isFolder=True)
			except: pass
		self._end_directory()

	def adjust_main_lists(self, params=None):
		from modules.nav_utils import notification
		def db_execute():
			dbcon = database.connect(NAVIGATOR_DB)
			dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (list_name, 'edited'))
			dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, 'edited', json.dumps(li)))
			dbcon.commit()
			window.setProperty('fen_%s_edited' % list_name, json.dumps(li))
		def menu_select(heading, position_list=False):
			pos_str, top_pos_str, top_str = ls(32707), ls(32708), ls(32709)
			for item in choice_items:
				line = pos_str % (menu_name, ls(item['name'])) if position_list else ''
				icon = item.get('iconImage') if item.get('network_id', '') != '' else os.path.join(self.icon_directory, item.get('iconImage'))
				listitem = xbmcgui.ListItem(ls(item['name']), line)
				listitem.setArt({'icon': icon})
				choice_list.append(listitem)
			if position_list:
				listitemTop = xbmcgui.ListItem(top_str, top_pos_str % menu_name)
				listitemTop.setArt({'icon': os.path.join(self.icon_directory, 'top.png')})
				choice_list.insert(0, listitemTop)
			return dialog.select(heading, choice_list, useDetails=True)
		def select_from_main_menus(current_list=[], item_list=[]):
			include_list = DefaultMenus().DefaultMenuItems()
			menus = DefaultMenus().RootList()
			menus.insert(0, {'name': ls(32457), 'iconImage': 'fen.png', 'foldername': 'Root', 'mode': 'navigator.main', 'action': 'RootList'})
			include_list = [i for i in include_list if i != current_list]
			menus = [i for i in menus if i.get('action', None) in include_list and not i.get('name') == item_list]
			return menus
		def get_external_name():
			dialog = xbmcgui.Dialog()
			name_append_list = [('RootList', ''), ('MovieList', '%s ' % ls(32028)), ('TVShowList', '%s ' % ls(32029))]
			orig_name = params.get('list_name', None)
			try: name = '%s%s' % ([i[1] for i in name_append_list if i[0] == orig_name][0], ls(menu_item.get('name')))
			except: name = orig_name
			name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=name)
			return name
		def db_execute_shortcut_folder(action='add'):
			dbcon = database.connect(NAVIGATOR_DB)
			dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (menu_name, 'shortcut_folder'))
			if action == 'add': dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (menu_name, 'shortcut_folder', json.dumps(li)))
			dbcon.commit()
			window.setProperty('fen_%s_shortcut_folder' % menu_name, json.dumps(li))
		def db_execute_add_to_shortcut_folder():
			dbcon = database.connect(NAVIGATOR_DB)
			dbcur.execute("SELECT list_contents FROM navigator WHERE list_name = ?", (shortcut_folder_name,))
			dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (menu_name, 'shortcut_folder'))
			if action == 'add': dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (menu_name, 'shortcut_folder', json.dumps(li)))
			dbcon.commit()
			window.setProperty('fen_%s_shortcut_folder' % list_name, json.dumps(li))
		def check_shortcut_folders():
			dbcon = database.connect(NAVIGATOR_DB)
			dbcur = dbcon.cursor()
			dbcur.execute("SELECT list_name, list_contents FROM navigator WHERE list_type = ?", ('shortcut_folder',))
			folders = dbcur.fetchall()
			try: folders = sorted([(str(i[0]), i[1]) for i in folders], key=lambda s: s[0].lower())
			except: folders = []
			return folders
		def select_shortcut_folders(make_new=False):
			folders = check_shortcut_folders()
			selection = 0
			folder_choice_list = []
			if len(folders) > 0:
				folder_names = ['[B]%s[/B]' % i[0] for i in folders]
				for item in folder_names:
					icon = os.path.join(self.icon_directory, 'furk.png')
					listitem = xbmcgui.ListItem(item, 'Existing Shortcut Folder')
					listitem.setArt({'icon': icon})
					folder_choice_list.append(listitem)
				if make_new:
					make_new_item = xbmcgui.ListItem(ls(32715), ls(32702))
					make_new_item.setArt({'icon': os.path.join(self.icon_directory, 'new.png')})
					folder_choice_list.insert(0, make_new_item)
				selection = dialog.select('Fen', folder_choice_list, useDetails=True)
			return folders, selection
		window.clearProperty('fen_%s_default')
		window.clearProperty('fen_%s_edited')
		dialog = xbmcgui.Dialog()
		if not params: params = self.params
		menu_name = params.get('menu_name', '')
		list_name = params.get('list_name', '')
		li = None
		method = params.get('method')
		choice_list = []
		if not method in ('display_edit_menu', 'add_external', 'add_trakt_external', 'add_imdb_external', 'add_sim_recom_external', 'restore'):
			try:
				current_position = int(params.get('position', '0'))
				default_list, edited_list = self._db_lists(list_name)
				def_file = default_list if not edited_list else edited_list
				li, def_li = def_file, default_list
				choice_items = [i for i in def_li if i not in li]
			except: pass
		try:
			if method == 'display_edit_menu':
				from ast import literal_eval
				from modules.utils import selection_dialog
				shortcut_folders_active = check_shortcut_folders()
				default_menu = params.get('default_menu')
				edited_list = None if params.get('edited_list') == 'None' else params.get('edited_list')
				list_name = params.get('list_name') if 'list_name' in params else self.list_name
				menu_name = params.get('menu_name')
				position = params.get('position')
				external_list_item = literal_eval(params.get('external_list_item', 'False'))
				list_is_full = literal_eval(params.get('list_is_full', 'False'))
				list_slug = params.get('list_slug', '')
				menu_item = json.loads(params.get('menu_item'))
				shortcut_folder = literal_eval(menu_item.get('shortcut_folder', 'False'))
				menu_item['list_name'] = list_name
				list_heading = ls(32457) if list_name == 'RootList' else ls(32028) if list_name == 'MovieList' else ls(32029)
				listing = []
				if len(default_menu) != 1:
					listing += [(ls(32716) % menu_name, 'move')]
					listing += [(ls(32717) % menu_name, 'remove')]
				if not shortcut_folder:
					listing += [(ls(32718) % menu_name, 'add_external')]
					if shortcut_folders_active: listing += [(ls(32719) % menu_name, 'shortcut_folder_add')]
				if list_name in ('RootList', 'MovieList', 'TVShowList'): listing += [(ls(32720) % list_heading, 'add_trakt')]
				if not list_is_full: listing += [(ls(32721) % list_heading, 'add_original')]
				listing += [(ls(32722) % list_heading, 'restore')]
				listing += [(ls(32723) % list_heading, 'check_update')]
				if not list_slug and not external_list_item: listing += [(ls(32724) % menu_name, 'reload')]
				if list_name in ('RootList', 'MovieList', 'TVShowList'): listing += [(ls(32725), 'shortcut_folder_new')]
				choice = selection_dialog([i[0] for i in listing], [i[1] for i in listing])
				if choice in (None, 'save_and_exit'): return
				elif choice == 'move': params = {'method': 'move', 'list_name': list_name, 'menu_name': menu_name, 'position': position}
				elif choice == 'remove': params = {'method': 'remove', 'list_name': list_name, 'menu_name': menu_name, 'position': position}
				elif choice == 'add_original': params = {'method': 'add_original', 'list_name': list_name, 'position': position}
				elif choice == 'restore': params = {'method': 'restore', 'list_name': list_name, 'position': position}
				elif choice == 'add_external': params = {'method': 'add_external', 'list_name': list_name, 'menu_item': json.dumps(menu_item)}
				elif choice == 'shortcut_folder_add': params = {'method': 'shortcut_folder_add', 'list_name': list_name, 'menu_item': json.dumps(menu_item)}
				elif choice == 'add_trakt': params = {'method': 'add_trakt', 'list_name': list_name, 'position': position}
				elif choice == 'reload': params = {'method': 'reload_menu_item', 'list_name': list_name, 'menu_name': menu_name, 'position': position}
				elif choice == 'shortcut_folder_new': params = {'method': 'shortcut_folder_new', 'list_name': list_name, 'menu_name': menu_name, 'position': position}
				elif choice == 'check_update': params = {'method': 'check_update_list', 'list_name': list_name, 'menu_name': menu_name, 'position': position}
				return self.adjust_main_lists(params)
			elif method == 'move':
				choice_items = [i for i in li if ls(i['name']) != menu_name]
				new_position = menu_select('Fen', position_list=True)
				if new_position < 0 or new_position == current_position: return
				li.insert(new_position, li.pop(current_position))
				db_execute()
			elif method == 'remove':
				li = [i for i in li if ls(i['name']) != menu_name]
				db_execute()
			elif method == 'add_original':
				selection = menu_select("Fen")
				if selection < 0: return
				selection = choice_items[selection]
				choice_list = []
				choice_items = li
				item_position = menu_select('Fen', position_list=True)
				if item_position < 0: return
				li.insert((item_position), selection)
				db_execute()
			elif method == 'shortcut_folder_add':
				menu_item = json.loads(params['menu_item'])
				if not menu_item: return
				current_shortcut_folders, folder_selection = select_shortcut_folders()
				if not current_shortcut_folders: return notification(ls(32702))
				if folder_selection < 0: return
				name = get_external_name()
				if not name: return
				menu_item['name'] = name
				folder_selection = current_shortcut_folders[folder_selection]
				shortcut_folder_name = folder_selection[0]
				shortcut_folder_contents = json.loads(folder_selection[1])
				choice_items = shortcut_folder_contents
				if len(choice_items) > 0: item_position = menu_select('Fen', position_list=True)
				else: item_position = 0
				if item_position < 0: return
				menu_item['external_list_item'] = 'True'
				shortcut_folder_contents.insert((item_position), menu_item)
				menu_name = shortcut_folder_name
				li = shortcut_folder_contents
				db_execute_shortcut_folder()
			elif method == 'add_external':
				menu_item = json.loads(params['menu_item'])
				if not menu_item: return
				name = get_external_name()
				if not name: return
				menu_item['name'] = name
				choice_items = select_from_main_menus(params.get('list_name'), name)
				selection = menu_select(ls(32726) % params.get('list_name'))
				if selection < 0: return
				add_to_menu_choice = choice_items[selection]
				list_name = add_to_menu_choice['action']
				default_list, edited_list = self._db_lists(list_name)
				def_file = default_list if not edited_list else edited_list
				li = def_file
				if menu_item in li: return
				choice_list = []
				choice_items = li
				item_position = menu_select('', position_list=True)
				if item_position < 0: return
				menu_item['external_list_item'] = 'True'
				li.insert((item_position), menu_item)
				db_execute()
			elif method == 'add_trakt':
				from indexers.trakt_lists import get_trakt_list_selection
				trakt_selection = json.loads(params['trakt_selection']) if 'trakt_selection' in params else get_trakt_list_selection(list_choice='nav_edit')
				if not trakt_selection: return
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=trakt_selection['name'])
				if not name: return
				choice_list = []
				choice_items = li
				item_position = menu_select('Fen', position_list=True)
				if item_position < 0: return
				li.insert(item_position, {"iconImage": "traktmylists.png", "mode": "trakt.lists.build_trakt_list", "name": name, "foldername": name, "user": trakt_selection['user'], "slug": trakt_selection['slug'], 'external_list_item': 'True'})
				db_execute()
			elif method == 'add_trakt_external':
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=params['name'])
				if not name: return
				if not li:
					choice_items = select_from_main_menus()
					selection = menu_select(ls(32726) % name)
					if selection < 0: return
					add_to_menu_choice = choice_items[selection]
					list_name = add_to_menu_choice['action']
					default_list, edited_list = self._db_lists(list_name)
					li = default_list if not edited_list else edited_list
				if name in [i['name'] for i in li]: return
				choice_list = []
				choice_items = li
				item_position = 0 if len(li) == 0 else menu_select('Fen', position_list=True)
				if item_position < 0: return
				li.insert(item_position, {"iconImage": "traktmylists.png", "mode": "trakt.lists.build_trakt_list", "name": name, "foldername": name, "user": params['user'], "slug": params['slug'], 'external_list_item': 'True'})
				db_execute()
			elif method == 'add_imdb_external':
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=params['name'])
				if not name: return
				if not li:
					choice_items = select_from_main_menus()
					selection = menu_select(ls(32726) % name)
					if selection < 0: return
					add_to_menu_choice = choice_items[selection]
					list_name = add_to_menu_choice['action']
					default_list, edited_list = self._db_lists(list_name)
					li = default_list if not edited_list else edited_list
				if name in [i['name'] for i in li]: return
				choice_list = []
				choice_items = li
				item_position = 0 if len(li) == 0 else menu_select('Fen', position_list=True)
				if item_position < 0: return
				imdb_params = json.loads(params['imdb_params'])
				imdb_params.update({'iconImage': 'imdb.png', 'name': name, 'foldername': name, 'external_list_item': 'True'})
				li.insert(item_position, imdb_params)
				db_execute()
			elif method == 'add_sim_recom_external':
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=params['sim_recom_name'])
				if not name: return
				if not li:
					choice_items = select_from_main_menus()
					selection = menu_select(ls(32726) % name)
					if selection < 0: return
					add_to_menu_choice = choice_items[selection]
					list_name = add_to_menu_choice['action']
					default_list, edited_list = self._db_lists(list_name)
					li = default_list if not edited_list else edited_list
				if name in [i['name'] for i in li]: return
				choice_list = []
				choice_items = li
				item_position = 0 if len(li) == 0 else menu_select('Fen', position_list=True)
				if item_position < 0: return
				li.insert(item_position, {"iconImage": "discover.png", "mode": params['end_mode'], 'action': params['end_action'], "name": name, "sim_recom_name": name, "foldername": name, "sim_recom_tmdb": params['sim_recom_tmdb'], "sim_recom_imdb": params['sim_recom_imdb'], 'external_list_item': 'True'})
				db_execute()
			elif method == 'browse':
				selection = menu_select('Fen')
				if selection < 0: return
				mode = choice_items[selection]['mode'] if 'mode' in choice_items[selection] else ''
				action = choice_items[selection]['action'] if 'action' in choice_items[selection] else ''
				url_mode = choice_items[selection]['url_mode'] if 'url_mode' in choice_items[selection] else ''
				menu_type = choice_items[selection]['menu_type'] if 'menu_type' in choice_items[selection] else ''
				query = choice_items[selection]['query'] if 'query' in choice_items[selection] else ''
				db_type = choice_items[selection]['db_type'] if 'db_type' in choice_items[selection] else ''
				xbmc.executebuiltin("Container.Update(%s)" % self._build_url({'mode': mode, 'action': action, 'url_mode': url_mode, 'menu_type': menu_type, 'query': query, 'db_type': db_type}))
			elif method == 'reload_menu_item':
				default = eval('DefaultMenus().%s()' % list_name)
				default_item = [i for i in default if ls(i['name']) == menu_name][0]
				li = [default_item if x['name'] == menu_name else x for x in def_file]
				list_type = 'edited' if self._db_lists(list_name)[1] else 'default'
				dbcon = database.connect(NAVIGATOR_DB)
				dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (list_name, list_type))
				dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, list_type, json.dumps(li)))
				dbcon.commit()
				window.setProperty('fen_%s_%s' % (list_name, list_type), json.dumps(li))
			elif method == 'shortcut_folder_new':
				make_new_folder = True
				current_shortcut_folders, folder_selection = select_shortcut_folders(make_new=True)
				if folder_selection < 0: return
				if folder_selection > 0:
					make_new_folder = False
					folder_selection = current_shortcut_folders[folder_selection-1] # -1 because we added the 'Make New' listitem
					name = folder_selection[0]
					contents = folder_selection[1]
				if make_new_folder:
					name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM)
					if not name: return
					contents = []
				if name in [ls(i['name']) for i in li]: return notification(ls(32490))
				menu_item = {"iconImage": "furk.png", 
							"mode": "navigator.build_shortcut_folder_lists",
							"action": name,
							"name": name, 
							"foldername": name,
							"shortcut_folder": 'True',
							"external_list_item": 'True',
							"contents": contents}
				choice_list = []
				choice_items = li
				menu_name = name
				item_position = 0 if len(li) == 0 else menu_select('Fen', position_list=True)
				if item_position < 0: return
				li.insert(item_position, menu_item)
				db_execute()
				if make_new_folder:
					li = []
					db_execute_shortcut_folder()
			elif method == 'check_update_list':
				dbcon = database.connect(NAVIGATOR_DB)
				dbcur = dbcon.cursor()
				new_contents = eval('DefaultMenus().%s()' % list_name)
				if default_list != new_contents:
					new_entry = [i for i in new_contents if i not in default_list][0]
					if not dialog.yesno('Fen', ls(32727) % ls(new_entry.get('name')), ls(32728)): return
					choice_items = def_file
					item_position = menu_select('Fen', position_list=True)
					if item_position < 0: return
					if edited_list:
						edited_list.insert(item_position, new_entry)
						dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (list_name, 'edited'))
						dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, 'edited', json.dumps(edited_list)))
						window.setProperty('fen_%s_edited' % list_name, json.dumps(edited_list))
					default_list.insert(item_position, new_entry)
					dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (list_name, 'default'))
					dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, 'default', json.dumps(default_list)))
					window.setProperty('fen_%s_default' % list_name, json.dumps(default_list))
					dbcon.commit()
					dbcon.close()
				else:
					return dialog.ok('Fen', ls(32983))
			elif method == 'restore':
				confirm = dialog.yesno('Fen', ls(32580))
				if not confirm: return
				dbcon = database.connect(NAVIGATOR_DB)
				for item in ['edited', 'default']: dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (list_name, item))
				dbcon.commit()
				dbcon.execute("VACUUM")
				dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, 'default', json.dumps(eval('DefaultMenus().%s()' % list_name))))
				dbcon.commit()
				for item in ('edited', 'default'): window.clearProperty('fen_%s_%s' % (list_name, item))
			if not method in ('browse',):
					notification(ls(32576), time=1500)
			if not method in ('browse', 'add_sim_recom_external'):
				xbmc.sleep(200)
				xbmc.executebuiltin('Container.Refresh')
		except: return notification(ls(32574))

	def build_main_lists(self):
		def _process():
			for item_position, item in enumerate(self.default_menu):
				try:
					is_folder = False if 'default_search_item' in item else True
					cm = []
					name = item.get('name', '')
					name = ls(name)
					icon = item.get('iconImage') if item.get('network_id', '') != '' else os.path.join(self.icon_directory, item.get('iconImage'))
					url = self._build_url(item)
					cm.append((edit_str,'RunPlugin(%s)' % self._build_url(
						{'mode': 'navigator.adjust_main_lists', 'method': 'display_edit_menu', 'default_menu': self.default_menu, 'menu_item': json.dumps(item),
						'edited_list': self.edited_list, 'list_name': self.list_name, 'menu_name': name,
						'position': item_position, 'list_is_full': list_is_full, 'list_slug': item.get('slug', ''),
						'external_list_item': item.get('external_list_item', 'False')})))
					if not list_is_full:
						cm.append((browse_str,'RunPlugin(%s)' % \
						self._build_url({'mode': 'navigator.adjust_main_lists', 'method': 'browse', 'list_name': self.list_name, 'position': item_position})))
					try: listitem = xbmcgui.ListItem(name, offscreen=True)
					except: listitem = xbmcgui.ListItem(name)
					listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': self.fanart, 'banner': icon})
					listitem.addContextMenuItems(cm)
					yield (url, listitem, is_folder)
				except: pass
		self.default_list, self.edited_list = self._db_lists()
		self.default_menu = self.default_list if not self.edited_list else self.edited_list
		current_items_from_default = [i for i in self.default_menu if not i.get('external_list_item', 'False') == 'True']
		list_is_full = True if len(current_items_from_default) >= len(self.default_list) else False
		cache_to_disc = False if self.list_name == 'RootList' else True
		edit_str, browse_str = ls(32705), ls(32706)
		item_list = list(_process())
		xbmcplugin.addDirectoryItems(self.__handle__, item_list)
		self._end_directory(cache_to_disc=cache_to_disc)

	def adjust_shortcut_folder_lists(self, params=None):
		from modules.nav_utils import notification
		def db_execute_shortcut_folder(action='add'):
			dbcon = database.connect(NAVIGATOR_DB)
			dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (menu_name, 'shortcut_folder'))
			if action == 'add': dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (menu_name, 'shortcut_folder', json.dumps(li)))
			dbcon.commit()
			window.setProperty('fen_%s_shortcut_folder' % menu_name, json.dumps(li))
		def menu_select(heading, position_list=False):
			pos_str, top_pos_str, top_str = ls(32707), ls(32708), ls(32709)
			for item in choice_items:
				line = pos_str % (name, ls(item['name'])) if position_list else ''
				icon = item.get('iconImage') if item.get('network_id', '') != '' else os.path.join(self.icon_directory, item.get('iconImage'))
				listitem = xbmcgui.ListItem(ls(item['name']), line)
				listitem.setArt({'icon': icon})
				choice_list.append(listitem)
			if position_list:
				listitemTop = xbmcgui.ListItem(top_str, top_pos_str % name)
				listitemTop.setArt({'icon': os.path.join(self.icon_directory, 'top.png')})
				choice_list.insert(0, listitemTop)
			return dialog.select(heading, choice_list, useDetails=True)
		def select_shortcut_folders(select=True):
			dbcon = database.connect(NAVIGATOR_DB)
			dbcur = dbcon.cursor()
			dbcur.execute("SELECT list_name, list_contents FROM navigator WHERE list_type = ?", ('shortcut_folder',))
			folders = dbcur.fetchall()
			try: folders = sorted([(str(i[0]), i[1]) for i in folders], key=lambda s: s[0].lower())
			except: folders = []
			if not select: return folders
			selection = 0
			folder_choice_list = []
			exist_str = ls(32710)
			if len(folders) > 0:
				folder_names = ['[B]%s[/B]' % i[0] for i in folders]
				for item in folder_names:
					icon = os.path.join(self.icon_directory, 'furk.png')
					listitem = xbmcgui.ListItem(item, exist_str)
					listitem.setArt({'icon': icon})
					folder_choice_list.append(listitem)
			return folders, selection
		dialog = xbmcgui.Dialog()
		if not params: params = self.params
		menu_name = params.get('menu_name')
		list_name = params.get('list_name')
		li = None
		method = params.get('method')
		choice_list = []
		current_position = int(params.get('position', '0'))
		try:
			if method == 'display_edit_menu':
				from ast import literal_eval
				from modules.utils import selection_dialog
				position = params.get('position')
				menu_item = json.loads(params.get('menu_item'))
				contents = json.loads(params.get('contents'))
				external_list_item = literal_eval(params.get('external_list_item', 'False'))
				list_slug = params.get('list_slug', '')
				list_heading = ls(32457) if list_name == 'RootList' else self.movies_string if list_name == 'MovieList' else self.tvshows_string
				string = ls(32711) % list_name
				listing = []
				if len(contents) != 1: listing += [(ls(32712), 'move')]
				listing += [(ls(32713), 'remove')]
				listing += [(ls(32714), 'add_trakt')]
				listing += [("%s %s" % (ls(32671), ls(32129)), 'clear_all')]
				choice = selection_dialog([i[0] for i in listing], [i[1] for i in listing], string)
				if choice in (None, 'save_and_exit'): return
				elif choice == 'move': params = {'method': 'move', 'list_name': list_name, 'menu_name': menu_name, 'position': position, 'menu_item': json.dumps(menu_item), 'contents': json.dumps(contents)}
				elif choice == 'remove': params = {'method': 'remove', 'list_name': list_name, 'menu_name': menu_name, 'position': position, 'menu_item': json.dumps(menu_item), 'contents': json.dumps(contents)}
				elif choice == 'add_trakt': params = {'method': 'add_trakt', 'list_name': list_name, 'position': position, 'menu_item': json.dumps(menu_item), 'contents': json.dumps(contents)}
				elif choice == 'clear_all': params = {'method': 'clear_all', 'list_name': list_name, 'menu_name': menu_name, 'position': position, 'menu_item': json.dumps(menu_item), 'contents': json.dumps(contents)}
				return self.adjust_shortcut_folder_lists(params)
			elif method == 'move':
				menu_name = params.get('list_name')
				name = params.get('menu_name')
				li = json.loads(params.get('contents'))
				choice_items = [i for i in li if i['name'] != name]
				new_position = menu_select('Fen', position_list=True)
				if new_position < 0 or new_position == current_position: return
				li.insert(new_position, li.pop(current_position))
				db_execute_shortcut_folder()
			elif method == 'remove':
				menu_name = params.get('list_name')
				name = params.get('menu_name')
				li = json.loads(params.get('contents'))
				li = [x for x in li if x['name'] != name]
				db_execute_shortcut_folder()
			elif method == 'add_external':
				menu_item = json.loads(params['menu_item'])
				if not menu_item: return
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=params['name'])
				if not name: return
				menu_item['name'] = name
				current_shortcut_folders, folder_selection = select_shortcut_folders()
				if folder_selection < 0: return
				folder_selection = current_shortcut_folders[folder_selection]
				shortcut_folder_name = folder_selection[0]
				shortcut_folder_contents = json.loads(folder_selection[1])
				choice_items = shortcut_folder_contents
				if len(choice_items) > 0: item_position = menu_select('Fen', position_list=True)
				else: item_position = 0
				if item_position < 0: return
				menu_name = shortcut_folder_name
				li = shortcut_folder_contents
				li.insert(item_position, menu_item)
				db_execute_shortcut_folder()
			elif method == 'add_trakt':
				from indexers.trakt_lists import get_trakt_list_selection
				trakt_selection = json.loads(params['trakt_selection']) if 'trakt_selection' in params else get_trakt_list_selection(list_choice='nav_edit')
				if not trakt_selection: return
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=trakt_selection['name'])
				if not name: return
				menu_name = params.get('list_name')
				li = json.loads(params.get('contents'))
				choice_items = li
				item_position = menu_select('Fen', position_list=True)
				if item_position < 0: return
				li.insert(item_position, {"iconImage": "traktmylists.png", "mode": "trakt.lists.build_trakt_list", "name": name, "foldername": name, "user": trakt_selection['user'], "slug": trakt_selection['slug'], 'external_list_item': 'True'})
				db_execute_shortcut_folder()
			elif method == 'add_trakt_external':
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=params['name'])
				if not name: return
				current_shortcut_folders, folder_selection = select_shortcut_folders()
				if folder_selection < 0: return
				folder_selection = current_shortcut_folders[folder_selection]
				shortcut_folder_name = folder_selection[0]
				shortcut_folder_contents = json.loads(folder_selection[1])
				choice_items = shortcut_folder_contents
				if len(choice_items) > 0: item_position = menu_select('Fen', position_list=True)
				else: item_position = 0
				if item_position < 0: return
				menu_name = shortcut_folder_name
				li = shortcut_folder_contents
				li.insert(item_position, {"iconImage": "traktmylists.png", "mode": "trakt.lists.build_trakt_list", "name": name, "foldername": name, "user": params['user'], "slug": params['slug'], 'external_list_item': 'True'})
				db_execute_shortcut_folder()
			elif method == 'add_imdb_external':
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=params['name'])
				if not name: return
				current_shortcut_folders, folder_selection = select_shortcut_folders()
				if folder_selection < 0: return
				folder_selection = current_shortcut_folders[folder_selection]
				shortcut_folder_name = folder_selection[0]
				shortcut_folder_contents = json.loads(folder_selection[1])
				choice_items = shortcut_folder_contents
				if len(choice_items) > 0: item_position = menu_select('Fen', position_list=True)
				else: item_position = 0
				if item_position < 0: return
				menu_name = shortcut_folder_name
				li = shortcut_folder_contents
				imdb_params = json.loads(params['imdb_params'])
				imdb_params.update({'iconImage': 'imdb.png', 'name': name, 'foldername': name, 'external_list_item': 'True'})
				li.insert(item_position, imdb_params)
				db_execute_shortcut_folder()
			elif method == 'clear_all':
				confirm = dialog.yesno('Fen', ls(32580))
				if not confirm: return
				menu_name = params.get('list_name')
				li = []
				db_execute_shortcut_folder()
			elif method == 'add_shortcut_folder':
				name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM)
				if not name: return
				dbcon = database.connect(NAVIGATOR_DB)
				dbcur = dbcon.cursor()
				dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (name, 'shortcut_folder', json.dumps([])))
				dbcon.commit()
			elif method == 'delete_shortcut_folder':
				list_name = params['list_name']
				if not dialog.yesno("Fen", ls(32580)): return
				dbcon = database.connect(NAVIGATOR_DB)
				dbcur = dbcon.cursor()
				dbcur.execute("DELETE FROM navigator WHERE list_name = ?", (list_name,))
				dbcon.commit()
				dialog.ok('Fen', ls(32729))
			elif method == 'remove_all_shortcut_folders':
				if not dialog.yesno("Fen", ls(32580)): return
				dbcon = database.connect(NAVIGATOR_DB)
				dbcur = dbcon.cursor()
				dbcon.execute("DELETE FROM navigator WHERE list_type=?", ('shortcut_folder',))
				dbcon.commit()
				dialog.ok('Fen', ls(32729))
			notification(ls(32576), time=1500)
			xbmc.sleep(200)
			if not method in ('add_external', 'add_trakt_external'):
				xbmc.sleep(200)
				xbmc.executebuiltin('Container.Refresh')
		except Exception:
			from modules.nav_utils import notification
			return notification(ls(32574), time=1500)
	
	def build_shortcut_folder_lists(self):
		def _build_default():
			icon = os.path.join(self.icon_directory, 'furk.png')
			url_params = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'add_trakt', 'contents': [], 'menu_item': '',
						'list_name': list_name, 'menu_name': '',
						'position': '', 'list_slug': '',
						'external_list_item': 'False'}
			url = self._build_url(url_params)
			listitem = xbmcgui.ListItem("[B][I]%s...[/I][/B]" % ls(32714))
			listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': self.fanart, 'banner': icon})
			xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=listitem, isFolder=False)
		def _process():
			for item_position, item in enumerate(contents):
				try:
					cm = []
					name = item.get('name', '')
					icon = item.get('iconImage') if item.get('network_id', '') != '' else os.path.join(self.icon_directory, item.get('iconImage'))
					url = self._build_url(item)
					cm.append((ls(32705),'RunPlugin(%s)' % self._build_url(
						{'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'display_edit_menu', 'contents': json.dumps(contents), 'menu_item': json.dumps(item),
						'list_name': list_name, 'menu_name': name,
						'position': item_position, 'list_slug': item.get('slug', ''),
						'external_list_item': item.get('external_list_item', 'False')})))
					try: listitem = xbmcgui.ListItem(name, offscreen=True)
					except: listitem = xbmcgui.ListItem(name)
					listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': self.fanart, 'banner': icon})
					listitem.addContextMenuItems(cm)
					yield (url, listitem, True)
				except: pass
		contents = self._db_lists_shortcut_folder()
		list_name = self.params['name']
		if not contents:
			_build_default()
			return self._end_directory()
		item_list = list(_process())
		xbmcplugin.addDirectoryItems(self.__handle__, item_list)
		self._end_directory()

	def _build_url(self, query):
		return self.__url__ + '?' + urlencode(to_utf8(query))

	def _changelog_info(self):
		disable_changelog = window.getProperty('fen_disable_changelog_popup')
		if disable_changelog == 'true': return
		if disable_changelog in ('', None):
			disable_changelog = get_setting('disable_changelog_popup')
			window.setProperty('fen_disable_changelog_popup', disable_changelog)
			if disable_changelog == 'true': return
		addon_version = settings.addon().getAddonInfo('version')
		setting_version = window.getProperty('fen_version_number')
		if setting_version in ('', None):
			setting_version = get_setting('version_number')
			window.setProperty('fen_version_number', setting_version)
		if addon_version == setting_version:
			return
		set_setting('version_number', addon_version)
		window.setProperty('fen_version_number', addon_version)
		from modules.nav_utils import show_text
		changelog_file, changelog_heading = xbmc.translatePath(os.path.join(addon_dir, "resources", "text", "changelog.txt")), '[B]Fen Changelog[/B]  [I](v.%s)[/I]' % addon_version
		show_text(changelog_heading, changelog_file)

	def _db_lists(self, list_name=None):
		list_name = self.list_name if not list_name else list_name
		try:
			default_contents = json.loads(window.getProperty('fen_%s_default' % list_name))
			try: edited_contents = json.loads(window.getProperty('fen_%s_edited' % list_name))
			except: edited_contents = None
			return default_contents, edited_contents
		except: pass
		try:
			dbcon = database.connect(NAVIGATOR_DB)
			dbcur = dbcon.cursor()
			dbcur.execute("SELECT list_contents FROM navigator WHERE list_name = ? AND list_type = ?", (str(list_name), 'default'))
			default_contents = json.loads(dbcur.fetchone()[0])
			dbcur.execute("SELECT list_contents FROM navigator WHERE list_name = ? AND list_type = ?", (str(list_name), 'edited'))
			try: edited_contents = json.loads(dbcur.fetchone()[0])
			except: edited_contents = None
			window.setProperty('fen_%s_default' % list_name, json.dumps(default_contents))
			window.setProperty('fen_%s_edited' % list_name, json.dumps(edited_contents))
			return default_contents, edited_contents
		except:
			self._build_database()
			return self._db_lists()
	
	def _db_lists_shortcut_folder(self, list_name=None):
		list_name = self.list_name if not list_name else list_name
		try:
			contents = json.loads(window.getProperty('fen_%s_shortcut_folder' % list_name))
			return contents
		except: pass
		try:
			dbcon = database.connect(NAVIGATOR_DB)
			dbcur = dbcon.cursor()
			dbcur.execute("SELECT list_contents FROM navigator WHERE list_name = ? AND list_type = ?", (str(list_name), 'shortcut_folder'))
			contents = json.loads(dbcur.fetchone()[0])
			window.setProperty('fen_%s_shortcut_folder' % list_name, json.dumps(contents))
			return contents
		except:
			return []

	def _rebuild_single_database(self, dbcon, list_name):
		dbcon.execute("DELETE FROM navigator WHERE list_type=? and list_name=?", ('default', list_name))
		dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, 'default', json.dumps(eval('DefaultMenus().%s()' % list_name))))
		dbcon.commit()

	def _build_database(self):
		settings.initialize_databases()
		default_menus = DefaultMenus().DefaultMenuItems()
		dbcon = database.connect(NAVIGATOR_DB)
		for content in default_menus:
			dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (content, 'default', json.dumps(eval('DefaultMenus().%s()' % content))))
		dbcon.commit()

	def _add_dir(self, url_params, list_name, iconImage='DefaultFolder.png', isFolder=True):
		cm = []
		icon = iconImage if 'network_id' in url_params else os.path.join(self.icon_directory, iconImage)
		url_params['iconImage'] = icon
		url = self._build_url(url_params)
		try: listitem = xbmcgui.ListItem(list_name, offscreen=True)
		except: listitem = xbmcgui.ListItem(list_name)
		listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': self.fanart, 'banner': icon})
		if 'SpecialSort' in url_params:
			listitem.setProperty("SpecialSort", url_params['SpecialSort'])
		if not 'exclude_external' in url_params:
			list_name = url_params['list_name'] if 'list_name' in url_params else self.list_name
			menu_params = {'mode': 'navigator.adjust_main_lists', 'method': 'add_external',
						'list_name': list_name, 'menu_item': json.dumps(url_params)}
			folder_params = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'add_external',
						'name': list_name, 'menu_item': json.dumps(url_params)}
			cm.append((ls(32730),'RunPlugin(%s)'% self._build_url(menu_params)))
			cm.append((ls(32731),'RunPlugin(%s)' % self._build_url(folder_params)))
			listitem.addContextMenuItems(cm)
		xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=listitem, isFolder=isFolder)

	def _end_directory(self, cache_to_disc=True):
		xbmcplugin.setContent(self.__handle__, 'addons')
		xbmcplugin.endOfDirectory(self.__handle__, cacheToDisc=cache_to_disc)
		setView(self.view, 'addons')


