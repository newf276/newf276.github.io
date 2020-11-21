# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import json
import re
try: from urlparse import parse_qsl
except ImportError: from urllib.parse import parse_qsl
try: from sqlite3 import dbapi2 as database
except ImportError: from pysqlite2 import dbapi2 as database
from modules.indicators_bookmarks import get_resumetime, get_progress_percent, get_watched_info_tv, get_watched_status, get_watched_status_season
from apis.trakt_api import trakt_get_next_episodes
from apis.imdb_api import imdb_parentsguide
from modules.nav_utils import build_url
from modules.utils import local_string as ls
from modules.settings_reader import get_setting
from modules import settings
import tikimeta 
# from modules.utils import logger

def _get_meta():
	meta = None
	try: meta = json.loads(xbmc.getInfoLabel('ListItem.Property(fen_listitem_meta)'))
	except ValueError:
		try:
			listitem = xbmc.getInfoLabel('ListItem.FileNameAndPath')
			params = dict(parse_qsl(listitem[listitem.find('?'):][1:]))
			meta = json.loads(params['meta'])
		except: pass
	return meta

def nextep_notification(priority):
	meta = _get_meta()
	if not meta: return settings.list_actions.append(None)
	if settings.watched_indicators() in (1, 2):
		ep_list = trakt_get_next_episodes(include_hidden=True, hidden_full_info=True)
	else:
		watched_db = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/watched_status.db')
		seen = set()
		settings.check_database(watched_db)
		dbcon = database.connect(watched_db)
		dbcur = dbcon.cursor()
		dbcur.execute('''SELECT media_id, season, episode, last_played FROM watched_status WHERE db_type=?''', ('episode',))
		rows = dbcur.fetchall()
		rows = sorted(rows, key = lambda x: (x[0], x[1], x[2]), reverse=True)
		ep_list = [{"tmdb_id": int(a), "season": int(b), "episode": int(c), "last_played": d} for a, b, c, d in rows if not (a in seen or seen.add(a))]
	try: info = [i for i in ep_list if i['tmdb_id'] == meta['tmdb_id']][0]
	except: return settings.list_actions.append((ls(33041), 'S01E01', meta['poster'], priority))
	current_season = info['season']
	current_episode = info['episode']
	season_data = meta['season_data']
	curr_season_data = [i for i in season_data if i['season_number'] == current_season][0]
	season = current_season if current_episode < curr_season_data['episode_count'] else current_season + 1
	episode = current_episode + 1 if current_episode < curr_season_data['episode_count'] else 1
	try: info = [i for i in season_data if i['season_number'] == season][0]
	except: return settings.list_actions.append(None)
	if info['episode_count'] >= episode:
		next_episode = 'S%.2dE%.2d' % (season, episode)
	return settings.list_actions.append((ls(33041), next_episode, meta['poster'], priority))

def watched_status_notification(db_type, priority):
	meta = _get_meta()
	if not meta: return settings.list_actions.append(None)
	if db_type == 'tvshow':
		total_episodes, total_watched = meta['total_episodes'], meta['total_watched']
		icon = meta['poster']
	else:
		season_number = xbmc.getInfoLabel('Listitem.Season')
		meta_user_info = tikimeta.retrieve_user_info()
		season_data = tikimeta.all_episodes_meta(meta['tmdb_id'], meta['tvdb_id'], meta['tvdb_summary']['airedSeasons'], meta['season_data'], meta_user_info)
		try: season_data = [i for i in season_data if int(i['season_number']) == int(season_number)][0]
		except: return settings.list_actions.append(None)
		aired_episodes = season_data['episode_count']
		watched_info, use_trakt = get_watched_info_tv()
		playcount, overlay, watched, unwatched = get_watched_status_season(watched_info, use_trakt, meta['tmdb_id'], int(season_number), aired_episodes)
		total_watched, total_episodes = watched, aired_episodes
		icon = season_data['poster_path'] if season_data['poster_path'] is not None else meta['poster']
	watched_status = ls(33046) % (total_watched, total_episodes)
	return settings.list_actions.append((ls(33048), watched_status, icon, priority))

def progress_notification(db_type, priority):
	meta = _get_meta()
	if not meta: return settings.list_actions.append(None)
	icon = meta['poster']
	if db_type in ['movie', 'episode']:
		season = meta.get('season', '')
		episode = meta.get('episode', '')
		resumetime = get_resumetime(db_type, meta['tmdb_id'], season, episode)
		duration = meta['duration']
		if db_type == 'episode' and resumetime in (0, '0'):
			watched_info, use_trakt = get_watched_info_tv()
			playcount, overlay = get_watched_status(watched_info, use_trakt, 'episode', meta['tmdb_id'], season, episode)
			if playcount == 1: resumetime = duration
	elif db_type == 'season':
		season_number = xbmc.getInfoLabel('Listitem.Season')
		meta_user_info = tikimeta.retrieve_user_info()
		season_data = tikimeta.all_episodes_meta(meta['tmdb_id'], meta['tvdb_id'], meta['tvdb_summary']['airedSeasons'], meta['season_data'], meta_user_info)
		try: season_data = [i for i in season_data if int(i['season_number']) == int(season_number)][0]
		except: return settings.list_actions.append(None)
		aired_episodes = season_data['episode_count']
		watched_info, use_trakt = get_watched_info_tv()
		playcount, overlay, watched, unwatched = get_watched_status_season(watched_info, use_trakt, meta['tmdb_id'], int(season_number), aired_episodes)
		resumetime, duration = watched, aired_episodes
		icon = season_data['poster_path'] if season_data['poster_path'] is not None else meta['poster']
	else:
		resumetime = int(meta['total_watched'])
		duration = int(meta['total_episodes'])
	percent_watched = get_progress_percent(resumetime, duration)
	progress_status = '%s%% %s' % (percent_watched, ls(32475))
	return settings.list_actions.append((ls(33049), progress_status, icon, priority))

def last_aired_notification(priority):
	meta = _get_meta()
	if not meta: return settings.list_actions.append(None)
	last_aired = meta['extra_info'].get('last_episode_to_air', ls(33052))
	if last_aired != 'N/A':
		episode = re.search(r'] (.*?) - ', last_aired).group(1)
		date = re.search(r'\[(.*?)\]', last_aired).group(1)
		last_aired = '%s (%s)' % (episode, date)
	return settings.list_actions.append((ls(32634), last_aired, meta['poster'], priority))

def next_aired_notification(priority):
	meta = _get_meta()
	if not meta: return settings.list_actions.append(None)
	next_aired = meta['extra_info'].get('next_episode_to_air', ls(33052))
	if next_aired != 'N/A':
		episode = re.search(r'] (.*?) - ', next_aired).group(1)
		date = re.search(r'\[(.*?)\]', next_aired).group(1)
		next_aired = '%s (%s)' % (episode, date)
	return settings.list_actions.append((ls(32635), next_aired, meta['poster'], priority))

def duration_finish_notification(db_type, priority):
	meta = _get_meta()
	if not meta: return settings.list_actions.append(None)
	duration = int(float(int(meta['duration']))/60)
	finished = xbmc.getInfoLabel('ListItem.EndTime')
	duration_finished = ls(33058) % (duration, finished)
	return settings.list_actions.append((ls(33059), duration_finished, meta['poster'], priority))

def production_status_notification(priority):
	meta = _get_meta()
	if not meta: return settings.list_actions.append(None)
	status = meta['extra_info'].get('status', ls(33052))
	return settings.list_actions.append((ls(33060), status, meta['poster'], priority))

def budget_revenue_notification(priority):
	meta = _get_meta()
	if not meta: return settings.list_actions.append(None)
	budget = meta['extra_info'].get('budget', ls(33052))
	if str(budget) == '$0': budget = ls(33052)
	revenue = meta['extra_info'].get('revenue', ls(33052))
	if str(revenue) == '$0': revenue = ls(33052)
	if budget == revenue == ls(33052): status = ls(33052)
	else: status = '%s / %s' % (budget, revenue)
	return settings.list_actions.append(('%s / %s' % (ls(32625), ls(32626)), status, meta['poster'], priority))

# next_icon = xbmc.translatePath('special://home/addons/script.tiki.artwork/resources/media/light/item_next.png')
# def autoscoll_page():
# 	if xbmc.getInfoLabel('Container.PluginName') == 'plugin.video.fen':
# 		if xbmc.getInfoLabel('ListItem.dbtype') in ('movie', 'tvshow'):
# 			NumItems = int(xbmc.getInfoLabel('Container.NumItems'))
# 			NumPages = int(xbmc.getInfoLabel('Container.NumPages'))
# 			CurrentItem = int(xbmc.getInfoLabel('Container.CurrentItem'))
# 			CurrentPage = int(xbmc.getInfoLabel('Container.CurrentPage'))
# 			if CurrentPage == NumPages and NumItems - CurrentItem <= 5:
# 				if xbmc.getCondVisibility("Container.OnScrollNext | Container.OnScrollPrevious"):
# 					try:
# 						params = json.loads(xbmc.getInfoLabel('ListItem.Property(fen_next_page_params)'))
# 						xbmc.executebuiltin('Container.Update(%s)' % build_url(params))
# 						xbmcgui.Dialog().notification('Auto Scrolling....', 'Page %s' % str(params['new_page']), next_icon, 2000, False)
# 					except: pass
# 	return
