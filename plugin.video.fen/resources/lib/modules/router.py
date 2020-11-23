# -*- coding: utf-8 -*-
try: from urlparse import parse_qsl
except ImportError: from urllib.parse import parse_qsl
# from modules.utils import logger

def routing(argv):
	params = dict(parse_qsl(argv.replace('?','')))
	mode = params.get('mode', 'navigator.main')
	if 'navigator.' in mode:
		from indexers.navigator import Navigator
		exec('Navigator(params).%s()' % mode.split('.')[1])
	elif 'discover.' in mode:
		if mode in ('discover.remove_from_history', 'discover.remove_all_history'):
			if mode == 'discover.remove_from_history':
				from indexers.discover import remove_from_history
				params['silent'] = False
				remove_from_history(params)
			elif mode == 'discover.remove_all_history':
				from indexers.discover import remove_all_history
				params['silent'] = True
				remove_all_history(params)
		else:
			from indexers.discover import Discover
			exec('Discover(params).%s()' % mode.split('.')[1])
	elif 'furk.' in mode:
		if mode == 'furk.browse_packs':
			from modules.sources import Sources
			Sources().furkTFile(params['file_name'], params['file_id'])
		elif mode == 'furk.add_to_files':
			from indexers.furk import add_to_files
			add_to_files(params['item_id'])
		elif mode == 'furk.remove_from_files':
			from indexers.furk import remove_from_files
			remove_from_files(params['item_id'])
		elif mode == 'furk.remove_from_downloads':
			from indexers.furk import remove_from_downloads
			remove_from_downloads(params['item_id'])
		elif mode == 'furk.remove_from_files':
			from indexers.furk import add_uncached_file
			add_uncached_file(params['id'])
		elif mode == 'furk.myfiles_protect_unprotect':
			from indexers.furk import myfiles_protect_unprotect
			myfiles_protect_unprotect(params['action'], params['name'], params['item_id'])
		elif mode == 'furk.browse_audio_album':
			from indexers.furk import browse_audio_album
			browse_audio_album(params.get('t_file', None), params.get('item_path', None))
		else:
			exec('from indexers.furk import %s as function' % mode.split('.')[1])
			function(params)
	elif 'easynews.' in mode:
		exec('from indexers.easynews import %s as function' % mode.split('.')[1])
		function(params)
	elif 'trakt.' in mode or 'trakt_' in mode:
		if 'trakt.list' in mode:
			exec('from indexers.trakt_lists import %s as function' % mode.split('.')[-1])
			function(params)
		elif 'trakt.' in mode:
			exec('from apis.trakt_api import %s as function' % mode.split('.')[1])
			function(params)
		else:
			if mode == 'trakt_sync_watched_to_fen':
				from ast import literal_eval
				from apis.trakt_api import sync_watched_trakt_to_fen
				sync_watched_trakt_to_fen(literal_eval(params['refresh']))
			elif mode == 'hide_unhide_trakt_items':
				from apis.trakt_api import hide_unhide_trakt_items
				hide_unhide_trakt_items(params['action'], params['media_type'], params['media_id'], params['section'])
	elif 'build' in mode:
		if mode == 'build_movie_list':
			from indexers.movies import Movies
			Movies(params).fetch_list()
		elif mode == 'build_tvshow_list':
			from indexers.tvshows import TVShows
			TVShows(params).fetch_list()
		elif mode == 'build_season_list':
			from indexers.tvshows import build_season_list
			build_season_list(params)
		elif mode == 'build_episode_list':
			from indexers.tvshows import build_episode_list
			build_episode_list(params)
		elif mode == 'build_next_episode':
			from indexers.next_episode import build_next_episode
			build_next_episode()
		elif mode == 'build_in_progress_episode':
			from modules.in_progress import build_in_progress_episode
			build_in_progress_episode()
		elif mode == 'build_add_to_remove_from_list':
			from indexers.dialogs import build_add_to_remove_from_list
			build_add_to_remove_from_list(params.get('meta'), params.get('media_type'), params.get('orig_mode'), params.get('from_search'))
		elif mode == 'build_navigate_to_page':
			from modules.nav_utils import build_navigate_to_page
			build_navigate_to_page(params)
		elif mode == 'build_next_episode_manager':
			from indexers.next_episode import build_next_episode_manager
			build_next_episode_manager(params)
		elif mode == 'build_kodi_library_recently_added':
			from modules.kodi_library import build_kodi_library_recently_added
			build_kodi_library_recently_added(params['db_type'])
		elif mode == 'imdb_build_user_lists':
			from indexers.imdb import imdb_build_user_lists
			imdb_build_user_lists(params.get('db_type'))
		elif mode == 'imdb_build_videos_list':
			from indexers.imdb import imdb_build_videos_list
			imdb_build_videos_list(params.get('imdb_id'))
		elif mode == 'build_popular_people':
			from indexers.people import popular_people
			popular_people(params.get('new_page', 1))
	elif '_play' in mode or 'play_' in mode and not 'autoplay' in mode:
		if mode == 'play_action':
			from modules.nav_utils import play_action
			play_action(params)
		elif mode == 'play_media':
			from modules.sources import Sources
			if 'params' in params:
				import json
				params = json.loads(params['params'])
			Sources().playback_prep(params)
		elif mode == 'play_display_results':
			from modules.sources import Sources
			Sources().display_results(params.get('page_no', None), params.get('previous_nav', None))
		elif mode == 'play_return_from_pagination':
			from modules.sources import Sources
			Sources().return_from_pagination(params['previous_nav'])
		elif mode == 'play_file':
			from modules.sources import Sources
			Sources().play_file(params['title'], params['source'])
		elif mode == 'play_auto':
			from modules.sources import Sources
			Sources().play_auto()
		elif mode == 'play_execute_nextep':
			from modules.sources import Sources
			Sources().play_execute_nextep(params.get('autoplay_nextep', 'True'), params.get('library', 'False'))
		elif mode == 'media_play':
			from modules.player import FenPlayer
			FenPlayer().run(params.get('url', None), params.get('rootname', None))
		elif mode == 'play_trailer':
			from modules.nav_utils import play_trailer
			play_trailer(params.get('url'), params.get('all_trailers', []))
		elif mode == 'play_fetch_random':
			from ast import literal_eval
			from modules.random_play import play_fetch_random
			play_fetch_random(params['db_type'], params['meta'], params.get('default_season', 0), params.get('played_eps', []), literal_eval(params.get('first_run', 'True')))
	elif 'choice' in mode:
		from indexers import dialogs
		if mode == 'scraper_color_choice':
			dialogs.scraper_color_choice(params['setting'])
		elif mode == 'next_episode_color_choice':
			dialogs.next_episode_color_choice(params.get('setting', None))
		elif mode == 'next_episode_options_choice':
			dialogs.next_episode_options_choice(params.get('setting', None))
		elif mode == 'next_episode_context_choice':
			dialogs.next_episode_context_choice()
		elif mode == 'unaired_episode_color_choice':
			dialogs.unaired_episode_color_choice()
		elif mode == 'scraper_dialog_color_choice':
			dialogs.scraper_dialog_color_choice(params['setting'])
		elif mode == 'scraper_quality_color_choice':
			dialogs.scraper_quality_color_choice(params['setting'])
		elif mode == 'similar_recommendations_choice':
			dialogs.similar_recommendations_choice(params)
		elif 'show_all_actors_choice' in mode:
			dialogs.show_all_actors_choice(params['media_rootname'], params['full_cast'])
		elif mode == 'folder_sources_choice':
			dialogs.folder_sources_choice(params['setting'])
		elif mode == 'folder_clear_choice':
			dialogs.folder_clear_choice()
		elif mode == 'internal_scrapers_order_choice':
			dialogs.internal_scrapers_order_choice()
		elif mode == 'imdb_images_choice':
			dialogs.imdb_images_choice(params['imdb_id'], params['rootname'])
		elif mode == 'imdb_videos_choice':
			dialogs.imdb_videos_choice(params['videos'])
		elif mode == 'imdb_reviews_choice':
			dialogs.imdb_reviews_choice(params['imdb_id'], params['rootname'], params['poster'])
		elif mode == 'imdb_parentsguide_choice':
			dialogs.imdb_parentsguide_choice(params['imdb_id'], params['rootname'])
		elif mode == 'imdb_trivia_choice':
			dialogs.imdb_trivia_choice(params['imdb_id'], params['rootname'], params['poster'], params['content'])
		elif mode == 'set_quality_choice':
			dialogs.set_quality(params['quality_setting'])
		elif mode == 'results_sorting_choice':
			dialogs.results_sorting_choice()
		elif mode == 'options_menu_choice':
			dialogs.options_menu(params)
		elif mode == 'extras_menu_choice':
			dialogs.extras_menu(params.get('media_type'), params.get('meta'), params.get('action'), params.get('play_params'), params.get('default_season', 0))
		elif mode == 'media_extra_info_choice':
			dialogs.media_extra_info(params['media_type'], params['meta'], params['extra_info'])
		elif mode == 'plot_choice':
			dialogs.display_plot(params['heading'], params['plot_text'])
		elif mode == 'display_mode_choice':
			from indexers.dialogs import set_display_mode
			set_display_mode()
		elif mode == 'enable_scrapers_choice':
			from indexers.dialogs import enable_scrapers
			enable_scrapers()
	elif 'next_episode_' in mode:
		if mode == 'add_next_episode_unwatched':
			from ast import literal_eval
			from indexers.next_episode import add_next_episode_unwatched
			add_next_episode_unwatched(params.get(action), params.get(media_id), literal_eval(params.get(silent, 'False')))
		elif mode == 'add_to_remove_from_next_episode_excludes':
			from indexers.next_episode import add_to_remove_from_next_episode_excludes
			add_to_remove_from_next_episode_excludes(params)
	elif 'favourites' in mode:
		from modules.favourites import Favourites
		exec('Favourites(params).%s()' % mode)
	elif 'subscriptions' in mode:
		from modules.subscriptions import Subscriptions
		if mode == 'subscriptions_add_remove':
			Subscriptions(params.get('db_type'), params.get('tmdb_id'), params.get('action'), params.get('orig_mode')).add_remove()
		elif mode == 'subscriptions_add_list':
			from modules.subscriptions import subscriptions_add_list
			subscriptions_add_list(params.get('db_type'))
		elif mode == 'subscriptions_update_interval':
			from indexers.dialogs import subscriptions_update_interval
			subscriptions_update_interval(params['update_type'])
		elif mode == 'update_subscriptions':
			from modules.settings import trakt_list_subscriptions
			if trakt_list_subscriptions():
				from modules.subscriptions import subscriptions_update_list
				subscriptions_update_list()
			else:
				exec('Subscriptions().%s()' % mode)
		else:
			exec('Subscriptions().%s()' % mode)
	elif 'watched_unwatched' in mode:
		if mode == 'mark_as_watched_unwatched':
			from modules.indicators_bookmarks import mark_as_watched_unwatched
			mark_as_watched_unwatched()
		elif mode == 'mark_movie_as_watched_unwatched':
			from modules.indicators_bookmarks import mark_movie_as_watched_unwatched
			mark_movie_as_watched_unwatched(params)
		elif mode == 'mark_tv_show_as_watched_unwatched':
			from modules.indicators_bookmarks import mark_tv_show_as_watched_unwatched
			mark_tv_show_as_watched_unwatched(params)
		elif mode == 'mark_season_as_watched_unwatched':
			from modules.indicators_bookmarks import mark_season_as_watched_unwatched
			mark_season_as_watched_unwatched(params)
		elif mode == 'mark_episode_as_watched_unwatched':
			from modules.indicators_bookmarks import mark_episode_as_watched_unwatched
			mark_episode_as_watched_unwatched(params)
		elif mode == 'watched_unwatched_erase_bookmark':
			from modules.indicators_bookmarks import erase_bookmark
			erase_bookmark(params.get('db_type'), params.get('media_id'), params.get('season', ''), params.get('episode', ''), params.get('refresh', 'false'))
	elif 'external_scrapers_' in mode:
		if mode == 'external_scrapers_disable':
			from modules.source_utils import external_scrapers_disable
			external_scrapers_disable()
		elif mode == 'external_scrapers_reset_stats':
			from modules.source_utils import external_scrapers_reset_stats
			external_scrapers_reset_stats()
		elif mode == 'external_scrapers_toggle_all':
			from modules.source_utils import toggle_all
			toggle_all(params.get('folder'), params.get('setting'))
		elif mode == 'external_scrapers_enable_disable_specific_all':
			from modules.source_utils import enable_disable_specific_all
			enable_disable_specific_all(params.get('folder'))
	elif 'myaccounts' in mode:
		action = mode.split('.')[1]
		if action == 'open':
			from modules.nav_utils import open_MyAccounts
			open_MyAccounts(params)
		else:
			from modules.nav_utils import sync_MyAccounts
			sync_MyAccounts()
	elif 'toggle' in mode:
		if mode == 'toggle_setting':
			from modules.nav_utils import toggle_setting
			toggle_setting(params['setting_id'], params['setting_value'], paramsget('refresh', False))
		elif mode == 'toggle_jump_to':
			from modules.utils import toggle_jump_to
			toggle_jump_to()
		elif mode == 'toggle_provider':
			from modules.utils import toggle_provider
			toggle_provider()
		elif mode == 'toggle_language_invoker':
			from modules.nav_utils import toggle_language_invoker
			toggle_language_invoker()
	elif 'history' in mode:
		if mode == 'search_history':
			from modules.history import search_history
			search_history(params)
		elif mode == 'clear_search_history':
			from modules.history import clear_search_history
			clear_search_history()
		elif mode == 'remove_from_history':
			from modules.history import remove_from_history
			remove_from_history(params)
	elif 'real_debrid' in mode:
		if mode == 'real_debrid.rd_torrent_cloud':
			from indexers.real_debrid import rd_torrent_cloud
			rd_torrent_cloud()
		if mode == 'real_debrid.rd_downloads':
			from indexers.real_debrid import rd_downloads
			rd_downloads()
		elif mode == 'real_debrid.browse_rd_cloud':
			from indexers.real_debrid import browse_rd_cloud
			browse_rd_cloud(params['id'])
		elif mode == 'real_debrid.resolve_rd':
			from indexers.real_debrid import resolve_rd
			resolve_rd(params)
		elif mode == 'real_debrid.rd_account_info':
			from indexers.real_debrid import rd_account_info
			rd_account_info()
		elif mode == 'real_debrid.delete':
			from indexers.real_debrid import rd_delete
			rd_delete(params.get('id'), params.get('cache_type'))
		elif mode == 'real_debrid.delete_download_link':
			from indexers.real_debrid import delete_download_link
			delete_download_link(params['download_id'])
	elif 'premiumize' in mode:
		if mode == 'premiumize.pm_torrent_cloud':
			from indexers.premiumize import pm_torrent_cloud
			pm_torrent_cloud(params.get('id', None), params.get('folder_name', None))
		elif mode == 'premiumize.pm_transfers':
			from indexers.premiumize import pm_transfers
			pm_transfers()
		elif mode == 'premiumize.pm_account_info':
			from indexers.premiumize import pm_account_info
			pm_account_info()
		elif mode == 'premiumize.rename':
			from indexers.premiumize import pm_rename
			pm_rename(params.get('file_type'), params.get('id'), params.get('name'))
		elif mode == 'premiumize.delete':
			from indexers.premiumize import pm_delete
			pm_delete(params.get('file_type'), params.get('id'))
	elif 'alldebrid' in mode:
		if mode == 'alldebrid.ad_torrent_cloud':
			from indexers.alldebrid import ad_torrent_cloud
			ad_torrent_cloud(params.get('id', None))
		elif mode == 'alldebrid.ad_transfers':
			from indexers.alldebrid import ad_transfers
			ad_transfers()
		elif mode == 'alldebrid.browse_ad_cloud':
			from indexers.alldebrid import browse_ad_cloud
			browse_ad_cloud(params['folder'])
		elif mode == 'alldebrid.resolve_ad':
			from indexers.alldebrid import resolve_ad
			resolve_ad(params)
		elif mode == 'alldebrid.ad_account_info':
			from indexers.alldebrid import ad_account_info
			ad_account_info()
	elif 'people_search' in mode:
		from indexers.people import People
		actor_id = params.get('actor_id', 'None')
		actor_name = params.get('actor_name', 'None')
		actor_image = params.get('actor_image', 'None')
		page_no = int(params.get('page_no', '1'))
		rolling_count = int(params.get('rolling_count', '0'))
		if 'media_results' in mode:
			media_type = params.get('media_type')
			page_no = int(params.get('new_page', '1'))
			letter = params.get('new_letter', 'None')
			People((actor_id, actor_name, actor_image)).media_results(media_type, page_no, letter)
		elif 'search_results' in mode:
			People((actor_id, actor_name, actor_image)).main()
		elif 'extras_person_data' in mode:
			People((actor_id, actor_name, actor_image)).extras_person_data(params.get('person_name'), params.get('tmdb_api'))
		else:
			action_code = 'People(%s).%s()' % ((actor_id, actor_name, actor_image, page_no, rolling_count), mode.split('.')[1])
			action_object = compile(action_code, 'people_search_string', 'exec')
			exec(action_object)
	elif '_settings' in mode:
		if mode == 'open_settings':
			from modules.nav_utils import open_settings
			open_settings(params.get('query'))
		elif mode == 'backup_settings':
			from modules.nav_utils import backup_settings
			backup_settings()
		elif mode == 'restore_settings':
			from modules.nav_utils import restore_settings
			restore_settings()
		elif mode == 'clean_settings':
			from modules.nav_utils import clean_settings
			clean_settings()
		elif mode == 'external_settings':
			from modules.nav_utils import open_settings
			open_settings(params.get('query', '0.0'), params.get('ext_addon'))
		elif mode == 'clear_settings_window_properties':
			from modules.settings_reader import clear_settings_window_properties
			clear_settings_window_properties()
	elif 'container_' in mode:
		if mode == 'container_update':
			from modules.nav_utils import container_update
			container_update(params)
		elif mode == 'container_refresh':
			from modules.nav_utils import container_refresh
			container_refresh(params)
	elif '_cache' in mode:
		from modules import nav_utils
		if mode == 'refresh_cached_data':
			nav_utils.refresh_cached_data(params.get('db_type', None), params.get('id_type', None), params.get('media_id', None), params.get('from_list', False))
		elif mode == 'clear_cache':
			nav_utils.clear_cache(params.get('cache'))
		elif mode == 'clear_scrapers_cache':
			nav_utils.clear_scrapers_cache()
		elif mode == 'clear_all_cache':
			nav_utils.clear_all_cache()
	elif '_image' in mode:
		if mode == 'tmdb_artwork_image_results':
			from indexers.images import tmdb_artwork_image_results
			tmdb_artwork_image_results(params['db_type'], params['tmdb_id'], params['image_type'])
		elif mode == 'imdb_image_results':
			from indexers.images import imdb_image_results
			imdb_image_results(params['imdb_id'], params['page_no'], params['rolling_count'])
		elif mode == 'browser_image':
			from indexers.images import browser_image
			browser_image(params['folder_path'])
		elif mode == 'show_image':
			from indexers.images import show_image
			show_image(params.get('image_url'))
		elif mode == 'delete_image':
			from indexers.images import delete_image
			delete_image(params.get('image_url'), params.get('thumb_url'))
		elif mode == 'slideshow_image':
			from indexers.images import slideshow_image
			slideshow_image(params.get('all_images'), params.get('current_index'))
	elif 'service_functions' in mode:
		from services import service_functions
		exec('service_functions.%s().run()' % mode.split('.')[1])
	##EXTRA modes##
	elif mode == 'browse_debrid_pack':
		from modules.sources import Sources
		Sources().debridPacks(params['provider'], params['name'], params['magnet_url'], params['info_hash'])
	elif mode == 'get_search_term':
		from modules.nav_utils import get_search_term
		get_search_term(params['db_type'], params.get('query'))
	elif mode == 'link_folders':
		from modules.nav_utils import link_folders
		link_folders(params['service'], params['folder_name'], params['action'])
	elif mode == 'extended_info_open':
		from modules.nav_utils import extended_info_open
		extended_info_open(params.get('db_type'), params.get('tmdb_id'))
	elif mode == 'show_text':
		from modules.nav_utils import show_text
		show_text(params.get('heading'), params.get('text_file'), params.get('usemono'))
	elif mode == 'downloader':
		from modules.downloader_NEW import Downloader
		Downloader(params).run()
	elif mode == 'download_file':
		from modules.nav_utils import show_busy_dialog
		from modules import downloader
		show_busy_dialog()
		db_type = params.get('db_type', None)
		if db_type in ('furk_file', 'realdebrid_direct_file', 'archive', 'audio', 'image'):
			downloader.download(params, params.get('url'))

		elif db_type == 'archive_direct':
			provider = params['provider']
			if provider.lower() == 'premiumize.me':
				from apis.premiumize_api import PremiumizeAPI
				from indexers.premiumize import pm_zip
				downloader.download(params, PremiumizeAPI().add_headers_to_url(pm_zip(params['url'])))
			elif provider.lower() == 'alldebrid':
				downloader.download(params, params['url'])

		elif db_type == 'debrid_archive_results':
			provider = params['provider']
			if provider.lower() == 'premiumize.me':
				from apis.premiumize_api import PremiumizeAPI
				downloader.download(params, PremiumizeAPI().add_headers_to_url(PremiumizeAPI().download_link_magnet_zip(params['magnet_url'], params['info_hash'])))

		elif db_type == 'easynews_file':
			from indexers.easynews import resolve_easynews
			downloader.download(params, resolve_easynews(params))
		elif db_type == 'realdebrid_file':
			from indexers.real_debrid import resolve_rd
			downloader.download(params, resolve_rd(params))
		elif db_type == 'premiumize_file':
			from apis.premiumize_api import PremiumizeAPI
			downloader.download(params, PremiumizeAPI().add_headers_to_url(params.get('url')))
		elif db_type == 'alldebrid_file':
			from indexers.alldebrid import resolve_ad
			downloader.download(params, resolve_ad(params))
		else:
			import json
			from modules import sources
			downloader.download(params, sources.Sources().resolve_sources(json.loads(params.get('source'))[0]))

