# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
try: from urlparse import parse_qsl
except ImportError: from urllib.parse import parse_qsl
try: from sqlite3 import dbapi2 as database
except ImportError: from pysqlite2 import dbapi2 as database
from sys import argv
import json
from datetime import date
import _strptime  # fix bug in python import
from threading import Thread
from modules.nav_utils import build_url, setView, remove_unwanted_info_keys, notification
from modules.utils import jsondate_to_datetime
from apis.trakt_api import get_trakt_tvshow_id, trakt_get_next_episodes
from indexers.tvshows import build_episode
from modules.utils import local_string as ls
from modules.settings_reader import get_setting
from tikimeta import tvshow_meta, all_episodes_meta, retrieve_user_info, check_meta_database
from modules import settings
# from modules.utils import logger

WATCHED_DB = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/watched_status.db')

window = xbmcgui.Window(10000)

def build_next_episode():
	from modules.indicators_bookmarks import get_watched_info_tv
	def _process_eps(item):
		try:
			meta = tvshow_meta('tmdb_id', item['tmdb_id'], meta_user_info)
			include_unaired = nextep_settings['include_unaired']
			current_season = item['season']
			current_episode = item['episode']
			unwatched = item.get('unwatched', False)
			season_data = meta['season_data']
			curr_season_data = [i for i in season_data if i['season_number'] == current_season][0]
			season = current_season if current_episode < curr_season_data['episode_count'] else current_season + 1
			episode = current_episode + 1 if current_episode < curr_season_data['episode_count'] else 1
			if watched_indicators in (1, 2):
				resformat = "%Y-%m-%dT%H:%M:%S.%fZ"
				curr_last_played = item.get('last_played', '2000-01-01T00:00:00.000Z')
			else:
				resformat = "%Y-%m-%d %H:%M:%S"
				curr_last_played = item.get('last_played', '2000-01-01 00:00:00')
			datetime_object = jsondate_to_datetime(curr_last_played, resformat)
			episode_item = {"season": season, "episode": episode, "meta": meta, "curr_last_played_parsed": datetime_object, "action": "next_episode",
							"unwatched": unwatched, "nextep_display_settings": nextep_display_settings, 'include_unaired': include_unaired,
							"adjust_hours": adjust_hours, "current_adjusted_date": current_adjusted_date, 'watched_indicators': watched_indicators}
			result.append(build_episode(episode_item, watched_info, use_trakt, meta_user_info, meta_user_info_json, is_widget))
		except: pass
	check_meta_database()
	try:
		__handle__ = int(argv[1])
		threads = []
		ep_list = []
		result = []
		nextep_settings = settings.nextep_content_settings()
		nextep_display_settings = settings.nextep_display_settings()
		watched_info, use_trakt = get_watched_info_tv()
		adjust_hours = int(get_setting('datetime.offset'))
		current_adjusted_date = settings.adjusted_datetime(dt=True)
		is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
		meta_user_info = retrieve_user_info()
		meta_user_info_json = json.dumps(meta_user_info)
		watched_indicators = settings.watched_indicators()
		cache_to_disk = nextep_settings['cache_to_disk']
		if nextep_settings['include_unwatched']:
			for i in get_unwatched_next_episodes(): ep_list.append(i)
		if watched_indicators in (1, 2):
			ep_list += trakt_get_next_episodes()
		else:
			seen = set()
			settings.check_database(WATCHED_DB)
			dbcon = database.connect(WATCHED_DB)
			dbcur = dbcon.cursor()
			dbcur.execute('''SELECT media_id, season, episode, last_played FROM watched_status WHERE db_type=?''', ('episode',))
			rows = dbcur.fetchall()
			rows = sorted(rows, key = lambda x: (x[0], x[1], x[2]), reverse=True)
			[ep_list.append({"tmdb_id": a, "season": int(b), "episode": int(c), "last_played": d}) for a, b, c, d in rows if not (a in seen or seen.add(a))]
			ep_list = [x for x in ep_list if not x['tmdb_id'] in check_for_next_episode_excludes()]
		ep_list = [i for i in ep_list if not i['tmdb_id'] is None]
		for item in ep_list: threads.append(Thread(target=_process_eps, args=(item,)))
		[i.start() for i in threads]
		[i.join() for i in threads]
		r = [i for i in result if i is not None]
		r = sort_next_eps(r, nextep_settings)
		item_list = [i['listitem'] for i in r]
		for i in item_list: xbmcplugin.addDirectoryItem(__handle__, i[0], i[1], i[2])
		xbmcplugin.setContent(__handle__, 'episodes')
		xbmcplugin.endOfDirectory(__handle__, cacheToDisc=cache_to_disk)
		setView('view.episode_lists', 'episodes')
	except:
		notification(ls(32574), time=3500)
		pass

def sort_next_eps(result, nextep_settings):
	from modules.utils import title_key
	ignore_articles = settings.ignore_articles()
	def func(function):
		if nextep_settings['sort_key'] == 'name': return title_key(function, ignore_articles)
		else: return function
	return sorted(result, key=lambda i: func(i[nextep_settings['sort_key']]), reverse=nextep_settings['sort_direction'])

def get_unwatched_next_episodes():
	try:
		if settings.watched_indicators() in (1, 2):
			from apis.trakt_api import trakt_fetch_collection_watchlist, get_trakt_tvshow_id
			data = trakt_fetch_collection_watchlist('watchlist', 'tvshow')
			return [{"tmdb_id": get_trakt_tvshow_id(i['media_ids']), "season": 1, "episode": 0, "unwatched": True} for i in data]
		else:
			settings.check_database(WATCHED_DB)
			dbcon = database.connect(WATCHED_DB)
			dbcur = dbcon.cursor()
			dbcur.execute('''SELECT media_id FROM unwatched_next_episode''')
			unwatched = dbcur.fetchall()
			return [{"tmdb_id": i[0], "season": 1, "episode": 0, "unwatched": True} for i in unwatched]
	except: return []

def add_next_episode_unwatched(action, media_id, silent=False):
	from modules.indicators_bookmarks import mark_as_watched_unwatched
	settings.check_database(WATCHED_DB)
	if action == 'add': command = "INSERT OR IGNORE INTO unwatched_next_episode VALUES (?)"
	else: command = "DELETE FROM unwatched_next_episode WHERE media_id=?"
	dbcon = database.connect(WATCHED_DB)
	dbcon.execute(command, (media_id,))
	dbcon.commit()
	dbcon.close()
	if not silent: notification(ls(32576), time=3500)

def add_to_remove_from_next_episode_excludes(params):
	settings.check_database(WATCHED_DB)
	action = params.get('action')
	media_id = str(params.get('media_id'))
	title = str(params.get('title'))
	dbcon = database.connect(WATCHED_DB)
	if action == 'add':
		dbcon.execute("INSERT INTO exclude_from_next_episode VALUES (?, ?)", (media_id, title))
	elif action == 'remove':
		dbcon.execute("DELETE FROM exclude_from_next_episode WHERE media_id=?", (media_id,))
	dbcon.commit()
	dbcon.close()
	notification(ls(32576), time=5000)
	xbmc.sleep(500)
	xbmc.executebuiltin("Container.Refresh")

def check_for_next_episode_excludes():
	settings.check_database(WATCHED_DB)
	dbcon = database.connect(WATCHED_DB)
	dbcur = dbcon.cursor()
	dbcur.execute('''SELECT media_id FROM exclude_from_next_episode''')
	row = dbcur.fetchall()
	dbcon.close()
	return [str(i[0]) for i in row]

def build_next_episode_manager(params):
	from modules.nav_utils import add_dir
	from modules.indicators_bookmarks import get_watched_status_tvshow, get_watched_info_tv
	def _process(tmdb_id, action):
		try:
			meta = tvshow_meta('tmdb_id', tmdb_id, meta_user_info)
			title = meta['title']
			if action == 'manage_unwatched':
				action, display = 'remove', '[COLOR=%s][%s][/COLOR] %s' % (NEXT_EP_UNWATCHED, ls(32803).upper(), title)
				url_params = {'mode': 'add_next_episode_unwatched', 'action': 'remove', 'tmdb_id': tmdb_id, 'title': title}
			elif action == 'trakt_and_fen':
				action, display = 'unhide' if tmdb_id in exclude_list else 'hide', '[COLOR=red][%s][/COLOR] %s' % (ls(32805).upper(), title) if tmdb_id in exclude_list else '[COLOR=green][%s][/COLOR] %s' % (ls(32804).upper(), title)
				url_params = {"mode": "hide_unhide_trakt_items", "action": action, "media_type": "shows", "media_id": meta['imdb_id'], "section": "progress_watched"}
			else:
				action, display = 'remove' if tmdb_id in exclude_list else 'add', '[COLOR=red][%s][/COLOR] %s' % (ls(32805).upper(), title) if tmdb_id in exclude_list else '[COLOR=green][%s][/COLOR] %s' % (ls(32804).upper(), title)
				url_params = {'mode': 'add_to_remove_from_next_episode_excludes', 'action': action, 'title': title, 'media_id': tmdb_id}
			sorted_list.append({'tmdb_id': tmdb_id, 'display': display, 'url_params': url_params, 'meta': json.dumps(meta)})
		except: pass
	check_meta_database()
	__handle__ = int(argv[1])
	NEXT_EP_UNWATCHED = get_setting('nextep.unwatched_colour')
	if not NEXT_EP_UNWATCHED or NEXT_EP_UNWATCHED == '': NEXT_EP_UNWATCHED = 'red'
	threads = []
	sorted_list = []
	action = params['action']
	if action == 'manage_unwatched':
		tmdb_list = [i['tmdb_id'] for i in get_unwatched_next_episodes()]
		heading = ls(32808)
	elif settings.watched_indicators() in (1, 2):
		tmdb_list, exclude_list = trakt_get_next_episodes(include_hidden=True)
		heading = ls(32806)
		action = 'trakt_and_fen'
	else:
		settings.check_database(WATCHED_DB)
		dbcon = database.connect(WATCHED_DB)
		dbcur = dbcon.cursor()
		dbcur.execute('''SELECT media_id FROM watched_status WHERE db_type=? GROUP BY media_id''', ('episode',))
		rows = dbcur.fetchall()
		tmdb_list = [row[0] for row in rows]
		exclude_list = check_for_next_episode_excludes()
		heading = ls(32807)
	add_dir({'mode': 'nill'}, '[I][COLOR=grey2]%s[/COLOR][/I]' % heading.upper(), iconImage='settings.png')
	if not tmdb_list:
		return notification(ls(32490), time=5000)
	meta_user_info = retrieve_user_info()
	for tmdb_id in tmdb_list: threads.append(Thread(target=_process, args=(tmdb_id, action)))
	[i.start() for i in threads]
	[i.join() for i in threads]
	sorted_items = sorted(sorted_list, key=lambda k: k['display'])
	watched_info, use_trakt = get_watched_info_tv()
	browse_str = ls(32652)
	for i in sorted_items:
		try:
			cm = []
			meta = json.loads(i['meta'])
			playcount, overlay, total_watched, total_unwatched = get_watched_status_tvshow(watched_info, use_trakt, meta['tmdb_id'], meta.get('total_episodes'))
			meta.update({'playcount': playcount, 'overlay': overlay,
						 'total_watched': str(total_watched), 'total_unwatched': str(total_unwatched)})
			url = build_url(i['url_params'])
			browse_url = build_url({'mode': 'build_season_list', 'meta': i['meta']})
			cm.append((browse_str,'Container.Update(%s)' % browse_url))
			listitem = xbmcgui.ListItem(i['display'])
			listitem.setProperty('watchedepisodes', str(total_watched))
			listitem.setProperty('unwatchedepisodes', str(total_unwatched))
			listitem.setProperty('totalepisodes', str(meta['total_episodes']))
			listitem.setProperty('totalseasons', str(meta['total_seasons']))
			listitem.addContextMenuItems(cm)
			listitem.setArt({'poster': meta['poster'],
							'fanart': meta['fanart'],
							'banner': meta['banner'],
							'clearart': meta['clearart'],
							'clearlogo': meta['clearlogo'],
							'landscape': meta['landscape']})
			listitem.setCast(meta['cast'])
			listitem.setInfo('video', remove_unwanted_info_keys(meta))
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
		except: pass
	xbmcplugin.setContent(__handle__, 'tvshows')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.main', 'tvshows')

def nextep_playback_info(tmdb_id, current_season, current_episode, from_library=None):
	def build_next_episode_play():
		ep_data = [i['episodes_data'] for i in seasons_data if i['season_number'] == season][0]
		ep_data = [i for i in ep_data if i['airedEpisodeNumber'] == episode][0]
		airdate = ep_data['firstAired']
		d = airdate.split('-')
		episode_date = date(int(d[0]), int(d[1]), int(d[2]))
		if current_adjusted_date < episode_date: return {'pass': True}
		query = meta['title'] + ' S%.2dE%.2d' % (int(season), int(episode))
		display_name = '%s - %dx%.2d' % (meta['title'], int(season), int(episode))
		meta.update({'vid_type': 'episode', 'rootname': display_name, "season": season, 'ep_name': ep_data['episodeName'],
					"episode": episode, 'premiered': airdate, 'plot': ep_data['overview']})
		meta_json = json.dumps(meta)
		url_params = {'mode': 'play_media', 'background': 'true', 'vid_type': 'episode', 'tmdb_id': meta['tmdb_id'],
					'query': query, 'tvshowtitle': meta['rootname'], 'season': season,
					'episode': episode, 'meta': meta_json, 'ep_name': ep_data['episodeName']}
		if from_library: url_params.update({'library': 'True', 'plot': ep_data['overview']})
		return build_url(url_params)
	check_meta_database()
	meta_user_info = retrieve_user_info()
	meta = tvshow_meta('tmdb_id', tmdb_id, meta_user_info)
	nextep_info = {'pass': True}
	autoplay_next_check_threshold = settings.autoplay_next_check_threshold()
	try: current_number = int(window.getProperty('fen_total_autoplays'))
	except: current_number = 1
	if current_number == autoplay_next_check_threshold:
		current_number = 1
		window.setProperty('fen_total_autoplays', str(current_number))
		continue_playing = xbmcgui.Dialog().yesno('Fen', ls(32802) % meta['title'], autoclose=10000)
		if not continue_playing == 1:
			notification(ls(32736), 6000)
			return nextep_info
	else:
		current_number += 1
		window.setProperty('fen_total_autoplays', str(current_number))
	# try:
	current_adjusted_date = settings.adjusted_datetime()
	seasons_data = all_episodes_meta(tmdb_id, meta['tvdb_id'], meta['tvdb_summary']['airedSeasons'], meta['season_data'], meta_user_info)
	curr_season_data = [i for i in seasons_data if i['season_number'] == current_season][0]
	season = current_season if current_episode < curr_season_data['episode_count'] else current_season + 1
	episode = current_episode + 1 if current_episode < curr_season_data['episode_count'] else 1
	nextep_info = {'season': season, 'episode': episode, 'url': build_next_episode_play()}
	# except: pass
	return nextep_info

def nextep_execute(nextep_info):
	xbmc.executebuiltin("RunPlugin(%s)" % nextep_info['url'])

