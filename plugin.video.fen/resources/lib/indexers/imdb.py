# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import os
from sys import argv
import json
from apis.imdb_api import imdb_user_lists, imdb_videos
from modules.settings import get_theme
from modules.nav_utils import build_url, setView
from modules.utils import local_string as ls
# from modules.utils import logger

addon_dir = xbmc.translatePath('special://home/addons/plugin.video.fen')
icon_directory = get_theme()
default_imdb_icon = os.path.join(icon_directory, 'imdb.png')
fanart = os.path.join(addon_dir, 'fanart.png')

def imdb_build_user_lists(db_type):
	__handle__ = int(argv[1])
	user_lists = imdb_user_lists(db_type)
	mode = 'build_movie_list' if db_type == 'movies' else 'build_tvshow_list'
	for item in user_lists:
		cm = []
		url_params = {'mode': mode, 'action': 'imdb_user_list_contents', 'list_id': item['list_id']}
		imdb_selection_url = {'mode': 'navigator.adjust_main_lists', 'method': 'add_imdb_external', 'name': item['title'], 'imdb_params': json.dumps(url_params)}
		imdb_folder_selection_url = {'mode': 'navigator.adjust_shortcut_folder_lists', 'method': 'add_imdb_external', 'name': item['title'], 'imdb_params': json.dumps(url_params)}
		url = build_url(url_params)
		listitem = xbmcgui.ListItem(item['title'])
		listitem.setArt({'icon': default_imdb_icon, 'poster': default_imdb_icon, 'thumb': default_imdb_icon, 'fanart': fanart, 'banner': default_imdb_icon})
		cm.append((ls(32730),'RunPlugin(%s)' % build_url(imdb_selection_url)))
		cm.append((ls(32731),'RunPlugin(%s)' % build_url(imdb_folder_selection_url)))
		listitem.addContextMenuItems(cm)
		xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.main')

def imdb_build_videos_list(imdb_id):
	__handle__ = int(argv[1])
	try: videos_list = imdb_videos(imdb_id)
	except: return
	for item in videos_list:
		title = item['title']
		poster = item['poster']
		url_params = {'mode': 'imdb_videos_choice', 'videos': json.dumps(item['videos'])}
		url = build_url(url_params)
		listitem = xbmcgui.ListItem(title)
		listitem.setArt({'icon': poster, 'poster': poster, 'thumb': poster, 'fanart': fanart})
		xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
	xbmcplugin.setContent(__handle__, 'images')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.images', 'images')




