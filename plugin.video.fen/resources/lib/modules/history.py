# -*- coding: utf-8 -*-

from sys import argv
from datetime import timedelta
from caches import fen_cache
from modules.utils import local_string as ls
# from modules.utils import logger

_cache = fen_cache.FenCache()

def add_to_search_history(search_name, search_list):
	try:
		result = []
		cache = _cache.get(search_list)
		if cache: result = cache
		if search_name in result: result.remove(search_name)
		result.insert(0, search_name)
		result = result[:10]
		_cache.set(search_list, result, expiration=timedelta(days=365))
	except: return

def remove_from_history(**kwargs):
	import xbmc
	from modules.nav_utils import notification
	try:
		result = _cache.get(kwargs['setting_id'])
		result.remove(kwargs.get('name'))
		_cache.set(kwargs['setting_id'], result, expiration=timedelta(days=365))
		notification(ls(32576), 3500)
		xbmc.executebuiltin('Container.Refresh')
	except: return

def clear_search_history():
	import xbmcgui
	from modules.nav_utils import notification
	dialog = xbmcgui.Dialog()
	delete_str, search_str, hist_str, vid_str, mov_str, tv_str, aud_str, furk_str, easy_str, peop_str = ls(32785), ls(32450), ls(32486), ls(32491), ls(32028), ls(32029), ls(32492), ls(32069), ls(32070), ls(32507)
	choice_list = [('%s %s %s %s' % (delete_str, mov_str, search_str, hist_str), 'movie_queries', 'Movie'),
				   ('%s %s %s %s' % (delete_str, tv_str, search_str, hist_str), 'tvshow_queries', 'TV Show'), 
				   ('%s %s %s %s' % (delete_str, peop_str, search_str, hist_str), 'people_queries', 'People'),
				   ('%s %s %s %s %s' % (delete_str, furk_str, vid_str, search_str, hist_str), 'furk_video_queries', 'Furk Video'), 
				   ('%s %s %s %s %s' % (delete_str, furk_str, aud_str, search_str, hist_str), 'furk_audio_queries', 'Furk Audio'), 
				   ('%s %s %s %s' % (delete_str, easy_str, search_str, hist_str), 'easynews_video_queries', 'Easynews Video')]
	try:
		selection = dialog.select('Fen', [i[0] for i in choice_list])
		if selection < 0: return
		setting = choice_list[selection][1]
		_cache.set(setting, '', expiration=timedelta(days=365))
		notification(ls(32576), 3500)
	except: return

def search_history(params):
	import xbmc, xbmcgui, xbmcplugin
	import sys, os
	try: from urllib import unquote
	except ImportError: from urllib.parse import unquote
	from modules.nav_utils import build_url, setView
	from modules.settings import get_theme
	sear_str = ls(32450).upper()
	mov_str = ls(32028).upper()
	tv_str = ls(32029).upper()
	peop_str = ls(32507).upper()
	furkvid_str = '%s %s' % (ls(32069).upper(), ls(32491).upper())
	furkaud_str = '%s %s' % (ls(32069).upper(), ls(32492).upper())
	remove_str = ls(32786)
	easy_str = ls(32070).upper()
	action = params['action']
	try:
		(search_setting, display_title) = ('movie_queries', mov_str) if action == 'movie' \
									 else ('tvshow_queries', tv_str) if action == 'tvshow' \
									 else ('people_queries', peop_str) if action == 'people' \
									 else ('furk_video_queries', furkvid_str) if action == 'furk_video' \
									 else ('furk_audio_queries', furkaud_str) if action == 'furk_audio' \
									 else ('easynews_video_queries', easy_str) if action == 'easynews_video' \
									 else ''
		history = _cache.get(search_setting)
		if not history: return
	except: return
	icon = os.path.join(get_theme(), 'search.png')
	fanart = os.path.join(xbmc.translatePath('special://home/addons/plugin.video.fen'), 'fanart.png')
	for h in history:
		try:
			cm = []
			name = unquote(h)
			url_params = {'mode': 'get_search_term', 'db_type': 'movie', 'query': name} if action == 'movie' \
					else {'mode': 'get_search_term', 'db_type': 'tv_show', 'query': name} if action == 'tvshow' \
					else {'mode': 'people_search.search', 'actor_name': name} if action == 'people' \
					else {'mode': 'furk.search_furk', 'db_type': 'video', 'query': name} if action == 'furk_video' \
					else {'mode': 'furk.search_furk', 'db_type': 'audio', 'music': True, 'query': name} if action == 'furk_audio' \
					else {'mode': 'easynews.search_easynews', 'query': name} if action == 'easynews_video' \
					else ''
			isFolder = False if action in ('movie', 'tvshow') else True
			display = '[B]%s %s : [/B]' % (display_title, sear_str) + name 
			url = build_url(url_params)
			cm.append((remove_str,'RunPlugin(%s?mode=%s&setting_id=%s&name=%s)' \
				% (argv[0], 'remove_from_history', search_setting, name)))
			listitem = xbmcgui.ListItem(display)
			listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': fanart, 'banner': icon})
			listitem.addContextMenuItems(cm)
			xbmcplugin.addDirectoryItem(int(argv[1]), url, listitem, isFolder=isFolder)
		except: pass
	xbmcplugin.setContent(int(argv[1]), 'addons')
	xbmcplugin.endOfDirectory(int(argv[1]))
	setView('view.main')
	