# -*- coding: utf-8 -*-
import xbmc, xbmcplugin, xbmcgui
import os
from sys import argv
import re
import json
from apis.premiumize_api import PremiumizeAPI
from modules.settings import get_theme
from modules.nav_utils import build_url, setView
from modules.source_utils import supported_video_extensions
from modules.utils import clean_file_name, normalize
from modules.utils import local_string as ls
# from modules.utils import logger

addon_dir = xbmc.translatePath('special://home/addons/plugin.video.fen')
icon_directory = get_theme()
default_pm_icon = os.path.join(icon_directory, 'premiumize.png')
fanart = os.path.join(addon_dir, 'fanart.png')
dialog = xbmcgui.Dialog()

Premiumize = PremiumizeAPI()

def pm_torrent_cloud(folder_id=None, folder_name=None):
	__handle__ = int(argv[1])
	try:
		extensions = supported_video_extensions()
		cloud_files = Premiumize.user_cloud(folder_id)['content']
		cloud_files = [i for i in cloud_files if ('link' in i and i['link'].lower().endswith(tuple(extensions))) or i['type'] == 'folder']
		cloud_files = sorted(cloud_files, key=lambda k: k['name'])
		cloud_files = sorted(cloud_files, key=lambda k: k['type'], reverse=True)
	except: return
	folder_str, file_str, down_str, archive_str, rename_str, delete_str = ls(32742).upper(), ls(32743).upper(), ls(32747), ls(32982), ls(32748), ls(32785)
	for count, item in enumerate(cloud_files, 1):
		try:
			cm = []
			file_type = item['type']
			name = clean_file_name(item['name']).upper()
			rename_params = {'mode': 'premiumize.rename', 'file_type': file_type, 'id': item['id'], 'name': item['name']}
			delete_params = {'mode': 'premiumize.delete', 'id': item['id']}
			if file_type == 'folder':
				is_folder = True
				download_string = archive_str
				delete_params['file_type'] = 'folder'
				string = folder_str
				display = '%02d | [B]%s[/B] | [I]%s [/I]' % (count, folder_str, name)
				url_params = {'mode': 'premiumize.pm_torrent_cloud', 'id': item['id'], 'folder_name': normalize(item['name'])}
				down_file_params = {'mode': 'download_file', 'name': item['name'], 'url': item['id'],
									'db_type': 'archive_direct', 'provider': 'premiumize.me', 'image': default_pm_icon}
			else:
				is_folder = False
				download_string = down_str
				delete_params['file_type'] = 'item'
				string = file_str
				url_link = item['link']
				if url_link.startswith('/'): url_link = 'https' + url_link
				size = item['size']
				display_size = float(int(size))/1073741824
				display = '%02d | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, file_str, display_size, name)
				url_params = {'mode': 'media_play', 'url': url_link, 'rootname': 'video'}
				down_file_params = {'mode': 'download_file', 'name': item['name'], 'url': url_link,
									'db_type': 'premiumize_file', 'image': default_pm_icon}
			cm.append((download_string, 'RunPlugin(%s)' % build_url(down_file_params)))
			cm.append((rename_str % file_type.capitalize(),'RunPlugin(%s)' % build_url(rename_params)))
			cm.append(('[B]%s %s[/B]' % (delete_str, string.capitalize()),'RunPlugin(%s)' % build_url(delete_params)))
			url = build_url(url_params)
			listitem = xbmcgui.ListItem(display)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': default_pm_icon, 'poster': default_pm_icon, 'thumb': default_pm_icon, 'fanart': fanart, 'banner': default_pm_icon})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=is_folder)
		except: pass
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.premium')

def pm_transfers():
	__handle__ = int(argv[1])
	extensions = supported_video_extensions()
	transfer_files = Premiumize.transfers_list()['transfers']
	folder_str, file_str, down_str = ls(32742).upper(), ls(32743).upper(), ls(32747)
	for count, item in enumerate(transfer_files, 1):
		try:
			cm = []
			file_type = 'folder' if item['file_id'] is None else 'file'
			name = clean_file_name(item['name']).upper()
			status = item['status']
			progress = item['progress']
			if status == 'finished': progress = 100
			else:
				try: progress = re.findall('\.{0,1}(\d+)', str(progress))[0][:2]
				except: progress = ''
			if file_type == 'folder':
				is_folder = True if status == 'finished' else False
				display = '%02d | %s%% | [B]%s[/B] | [I]%s [/I]' % (count, str(progress), folder_str, name)
				url_params = {'mode': 'premiumize.pm_torrent_cloud', 'id': item['folder_id'], 'folder_name': normalize(item['name'])}
			else:
				is_folder = False
				details = Premiumize.get_item_details(item['file_id'])
				url_link = details['link']
				if url_link.startswith('/'): url_link = 'https' + url_link
				size = details['size']
				display_size = float(int(size))/1073741824
				display = '%02d | %s%% | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, str(progress), file_str, display_size, name)
				url_params = {'mode': 'media_play', 'url': url_link, 'rootname': 'video'}
				down_file_params = {'mode': 'download_file', 'name': item['name'], 'url': url_link,
									'db_type': 'premiumize_file', 'image': default_pm_icon}
				cm.append((down_str,'RunPlugin(%s)' % build_url(down_file_params)))
			url = build_url(url_params)
			listitem = xbmcgui.ListItem(display)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': default_pm_icon, 'poster': default_pm_icon, 'thumb': default_pm_icon, 'fanart': fanart, 'banner': default_pm_icon})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=is_folder)
		except: pass
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.premium')

def pm_rename(file_type, file_id, current_name):
	new_name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM, defaultt=current_name)
	if not new_name: return
	result = Premiumize.rename_cache_item(file_type, file_id, new_name)
	if result == 'success':
		Premiumize.clear_cache()
		xbmc.executebuiltin('Container.Refresh()')
	else:
		return dialog.ok('Fen', ls(32574))

def pm_delete(file_type, file_id):
	if not dialog.yesno('Fen', ls(32580)): return
	result = Premiumize.delete_object(file_type, file_id)
	if result == 'success':
		Premiumize.clear_cache()
		xbmc.executebuiltin('Container.Refresh()')
	else:
		return dialog.ok('Fen', ls(32574))

def pm_zip(folder_id):
	result = Premiumize.zip_folder(folder_id)
	if result['status'] == 'success':
		return result['location']
	else: return None

def pm_account_info():
	from datetime import datetime
	import math
	try:
		account_info = Premiumize.account_info()
		customer_id = account_info['customer_id']
		expires = datetime.fromtimestamp(account_info['premium_until'])
		days_remaining = (expires - datetime.today()).days
		points_used = int(math.floor(float(account_info['space_used']) / 1073741824.0))
		space_used = float(int(account_info['space_used']))/1073741824
		percentage_used = str(round(float(account_info['limit_used']) * 100.0, 1))
		heading = ls(32061).upper()
		body = []
		body.append(ls(32749) % customer_id)
		body.append(ls(32750) % expires)
		body.append(ls(32751) % days_remaining)
		body.append(ls(32752) % points_used)
		body.append(ls(32753) % space_used)
		body.append(ls(32754) % (percentage_used + '%'))
		return dialog.select(heading, body)
	except Exception as e:
		return dialog.ok('Fen', ls(32574), str(e))
