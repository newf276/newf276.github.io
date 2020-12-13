# -*- coding: utf-8 -*-
import xbmc, xbmcplugin, xbmcgui
import os
from sys import argv
import json
from apis.alldebrid_api import AllDebridAPI
from caches import fen_cache
from modules.settings import get_theme
from modules.nav_utils import build_url, setView
from modules.source_utils import supported_video_extensions
from modules.utils import clean_file_name, normalize
from modules.utils import local_string as ls
# from modules.utils import logger

addon_dir = xbmc.translatePath('special://home/addons/plugin.video.fen/')
icon_directory = get_theme()
default_ad_icon = os.path.join(icon_directory, 'alldebrid.png')
fanart = os.path.join(addon_dir, 'fanart.png')
dialog = xbmcgui.Dialog()

AllDebrid = AllDebridAPI()
_cache = fen_cache.FenCache()

def ad_torrent_cloud(folder_id=None):
	__handle__ = int(argv[1])
	folder_str, archive_str, linkedto_str, addlink_str, clearlink_str = ls(32742).upper(), ls(32982), ls(32744), ls(32745), ls(32746)
	cloud_dict = AllDebrid.user_cloud()['magnets']
	cloud_dict = [i for i in cloud_dict if i['statusCode'] == 4]
	for count, item in enumerate(cloud_dict, 1):
		try:
			cm = []
			# try: all_links = [(i['filename'], i['link']) for i in item['links'] if i['filename'].lower().endswith(tuple(supported_video_extensions()))]
			# except: all_links = []
			folder_name = item['filename']
			normalized_folder_name = normalize(folder_name)
			string = 'FEN_AD_%s' % normalized_folder_name
			link_folders_add = {'mode': 'link_folders', 'service': 'AD', 'folder_name': normalized_folder_name, 'action': 'add'}
			link_folders_remove = {'mode': 'link_folders', 'service': 'AD', 'folder_name': normalized_folder_name, 'action': 'remove'}
			current_link = _cache.get(string)
			if current_link: ending = '[COLOR=limegreen][B][I]\n      %s[/I][/B][/COLOR]' % (linkedto_str % current_link)
			else: ending = ''
			display = '%02d | [B]%s[/B] | [I]%s [/I]%s' % (count, folder_str, clean_file_name(normalized_folder_name).upper(), ending)
			url_params = {'mode': 'alldebrid.browse_ad_cloud', 'folder': json.dumps(item)}
			url = build_url(url_params)
			# if all_links:
			# 	down_file_params = {'mode': 'download_file', 'name': folder_name, 'url': all_links,
			# 						'db_type': 'archive_direct', 'provider': 'alldebrid', 'image': default_ad_icon}
			# 	cm.append((archive_str,'RunPlugin(%s)' % build_url(down_file_params)))
			cm.append((addlink_str,'RunPlugin(%s)' % build_url(link_folders_add)))
			cm.append((clearlink_str,'RunPlugin(%s)' % build_url(link_folders_remove)))
			listitem = xbmcgui.ListItem(display)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': default_ad_icon, 'poster': default_ad_icon, 'thumb': default_ad_icon, 'fanart': fanart, 'banner': default_ad_icon})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
		except: pass
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.premium')

def ad_transfers():
	__handle__ = int(argv[1])
	AllDebrid.clear_cache()
	cloud_dict = AllDebrid.user_cloud()['magnets']
	folder_str = ls(32742).upper()
	for count, item in enumerate(cloud_dict, 1):
		try:
			if item['statusCode'] in (0,1,2,3):
				active = True
				downloaded = item['downloaded']
				size = item['size']
				percent = str(int(float(downloaded)/size*100))
			else: active = False
			cm = []
			folder_name = item['filename']
			normalized_folder_name = normalize(folder_name)
			if active: display = '%02d | [B]%s (%s)[/B] | [I]%s [/I]' % (count, item['status'].upper(), percent+'%', clean_file_name(normalized_folder_name).upper())
			else: display = '%02d | [B]%s[/B] | [I]%s [/I]' % (count, folder_str, clean_file_name(normalized_folder_name).upper())
			url_params = {'mode': 'alldebrid.browse_ad_cloud', 'folder': json.dumps(item)}
			url = build_url(url_params)
			listitem = xbmcgui.ListItem(display)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': default_ad_icon, 'poster': default_ad_icon, 'thumb': default_ad_icon, 'fanart': fanart, 'banner': default_ad_icon})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
		except: pass
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.premium')

def browse_ad_cloud(folder):
	__handle__ = int(argv[1])
	final_files = []
	extensions = supported_video_extensions()
	torrent_folder = json.loads(folder)
	links = torrent_folder['links']
	links = [i for i in links if i['filename'].lower().endswith(tuple(extensions))]
	file_str, down_str = ls(32743).upper(), ls(32747)
	for count, item in enumerate(links, 1):
		try:
			cm = []
			url_link = item['link']
			name = clean_file_name(item['filename']).upper()
			size = item['size']
			display_size = float(int(size))/1073741824
			display = '%02d | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, file_str, display_size, name)
			url_params = {'mode': 'alldebrid.resolve_ad', 'url': url_link, 'play': 'true'}
			url = build_url(url_params)
			down_file_params = {'mode': 'download_file', 'name': name, 'url': url_link,
								'db_type': 'alldebrid_file', 'image': default_ad_icon}
			cm.append((down_str,'RunPlugin(%s)' % build_url(down_file_params)))
			listitem = xbmcgui.ListItem(display)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': default_ad_icon, 'poster': default_ad_icon, 'thumb': default_ad_icon, 'fanart': fanart, 'banner': default_ad_icon})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
		except: pass
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.premium')

def resolve_ad(params):
	url = params['url']
	resolved_link = AllDebrid.unrestrict_link(url)
	if params.get('play', 'false') != 'true' : return resolved_link
	from modules.player import FenPlayer
	FenPlayer().play(resolved_link)

def ad_account_info():
	from datetime import datetime
	try:
		account_info = AllDebrid.account_info()['user']
		username = account_info['username']
		email = account_info['email']
		status = 'Premium' if account_info['isPremium'] else 'Not Active'
		expires = datetime.fromtimestamp(account_info['premiumUntil'])
		days_remaining = (expires - datetime.today()).days
		heading = ls(32063).upper()
		body = []
		body.append(ls(32755) % username)
		body.append(ls(32756) % email)
		body.append(ls(32757) % status)
		body.append(ls(32750) % expires)
		body.append(ls(32751) % days_remaining)
		return dialog.select(heading, body)
	except Exception as e:
		return dialog.ok('Fen', ls(32574), str(e))

