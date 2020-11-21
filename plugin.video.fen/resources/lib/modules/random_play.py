# -*- coding: utf-8 -*-
import xbmc
import json
from random import choice
from modules.settings import adjusted_datetime
from modules.nav_utils import build_url, notification
from modules.utils import adjust_premiered_date, selection_dialog
from modules.utils import local_string as ls
from tikimeta import season_episodes_meta, retrieve_user_info
from modules.settings_reader import get_setting
# from modules.utils import logger

def play_fetch_random(db_type, meta, default_season=0, played_eps=[], first_run=True):
	meta = json.loads(meta)
	try: played_eps = json.loads('played_eps')
	except: pass
	try: default_season = int(default_season)
	except: default_season = 0
	if first_run:
		choices = [(ls(32853), False), (ls(32854), True)]
		continual_play = selection_dialog([i[0] for i in choices], [i[1] for i in choices], 'Fen')
		if continual_play is None: return
	else: continual_play = True
	meta_user_info = retrieve_user_info()
	adjust_hours = int(get_setting('datetime.offset'))
	current_adjusted_date = adjusted_datetime(dt=True)
	episodes_data = season_episodes_meta(meta['tmdb_id'], meta['tvdb_id'], None, meta['tvdb_summary']['airedSeasons'], meta['season_data'], meta_user_info, True)
	if default_season != 0: episodes_data = [i for i in episodes_data if i['season'] == int(default_season)]
	episodes_data = [i for i in episodes_data if not i['season']  == 0 and adjust_premiered_date(i['premiered'], adjust_hours)[0] <= current_adjusted_date and not i in played_eps]
	if not episodes_data:
		if played_eps:
			episodes_data = played_eps
			played_eps = []
		elif first_run: return notification(ls(32855))
		else: return {'pass': True}
	from modules.sources import Sources
	chosen_episode = choice(episodes_data)
	played_eps.append(chosen_episode)
	title = meta['title']
	season = int(chosen_episode['season'])
	episode = int(chosen_episode['episode'])
	query = title + ' S%.2dE%.2d' % (season, episode)
	display_name = '%s - %dx%.2d' % (title, season, episode)
	ep_name = chosen_episode['title']
	plot = chosen_episode['plot']
	try: premiered = adjust_premiered_date(chosen_episode['premiered'], adjust_hours)[1]
	except: premiered = chosen_episode['premiered']
	meta.update({'vid_type': 'episode', 'rootname': display_name, 'season': season,
				'episode': episode, 'premiered': premiered, 'ep_name': ep_name,
				'plot': plot, 'default_season': default_season, 'random_play': True})
	if continual_play: meta['played_eps'] = played_eps
	meta_json = json.dumps(meta)
	url_params = {'mode': 'play_media', 'vid_type': 'episode', 'tmdb_id': meta['tmdb_id'], 'query': query, 'tvshowtitle': meta['rootname'],
				  'season': season, 'episode': episode, 'ep_name': ep_name, 'plot': plot, 'meta': meta_json,
				  'background': 'false', 'autoplay': 'True'}
	if len(played_eps) > 1: url_params['background'] = 'true'
	if first_run: return xbmc.executebuiltin('RunPlugin(%s)' % build_url(url_params))
	else: return {'season': season, 'episode': episode, 'url': build_url(url_params)}

def play_random(random_info):
	xbmc.executebuiltin("RunPlugin(%s)" % random_info['url'])