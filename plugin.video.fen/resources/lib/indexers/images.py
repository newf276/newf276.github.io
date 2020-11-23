# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcvfs
import os
from sys import argv
import json
from threading import Thread
from apis.tmdb_api import tmdb_media_images, tmdb_people_pictures, tmdb_people_tagged_pictures
from apis.imdb_api import people_get_imdb_id, imdb_people_images
from modules.nav_utils import build_url, add_dir, setView
from modules.utils import local_string as ls
# from modules.utils import logger

addon_dir = xbmc.translatePath('special://home/addons/plugin.video.fen')
profile_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/')

icon = os.path.join(addon_dir, "icon.png")
fanart = os.path.join(addon_dir, "fanart.png")

def tmdb_artwork_image_results(db_type, tmdb_id, image_type):
	__handle__ = int(argv[1])
	image_base = 'https://image.tmdb.org/t/p/%s%s'
	results = tmdb_media_images(db_type, tmdb_id)
	image_info = sorted(results[image_type], key=lambda x: x['file_path'])
	all_images_json = json.dumps([image_base % ('original', i['file_path']) for i in image_info])
	for count, item in enumerate(image_info):
		try:
			cm = []
			image_url = image_base % ('original', i['file_path'])
			thumb_url = image_base % ('w185', item['file_path'])
			name = '%03d_%sx%s' % (count+1, i['height'], i['width'])
			url_params = {'mode': 'slideshow_image', 'all_images': all_images_json, 'current_index': count}
			down_file_params = {'mode': 'download_file', 'name': name, 'url': (image_url, thumb_url), 'db_type': 'image', 'image': icon}
			url = build_url(url_params)
			cm.append((ls(32747),'RunPlugin(%s)' % build_url(down_file_params)))
			listitem = xbmcgui.ListItem(name)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': thumb_url, 'poster': thumb_url, 'thumb': thumb_url, 'fanart': fanart, 'banner': thumb_url})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
		except: pass
	xbmcplugin.setContent(__handle__, 'images')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.images', 'images')

def imdb_image_results(imdb_id, page_no, rolling_count):
	from apis.imdb_api import imdb_images
	__handle__ = int(argv[1])
	image_info, next_page = imdb_images(imdb_id, page_no)
	image_info = sorted(image_info, key=lambda x: x['title'])
	all_images_json = json.dumps([i['image'] for i in image_info])
	rolling_count = int(rolling_count)
	for count, item in enumerate(image_info):
		try:
			rolling_count += 1
			cm = []
			thumb_url = item['thumb']
			image_url = item['image']
			name = '%s_%03d' % (item['title'], rolling_count)
			url_params = {'mode': 'slideshow_image', 'all_images': all_images_json, 'current_index': count}
			down_file_params = {'mode': 'download_file', 'name': name, 'url': (image_url, thumb_url), 'db_type': 'image', 'image': icon}
			url = build_url(url_params)
			cm.append((ls(32747),'RunPlugin(%s)' % build_url(down_file_params)))
			listitem = xbmcgui.ListItem(name)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': thumb_url, 'poster': thumb_url, 'thumb': thumb_url, 'fanart': fanart, 'banner': thumb_url})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
		except: pass
	if len(image_info) == 48: add_dir({'mode': 'imdb_image_results', 'imdb_id': imdb_id, 'page_no': int(page_no)+1, 'rolling_count': rolling_count}, ls(32799), iconImage='item_next.png')
	xbmcplugin.setContent(__handle__, 'images')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.images', 'images')

def people_image_results(actor_name, actor_id, actor_image, page_no, rolling_count):
	def get_tmdb():
		try: tmdb_results.append(tmdb_people_pictures(actor_id))
		except: pass
	def get_imdb():
		imdb_id = people_get_imdb_id(actor_name, actor_id)
		try: imdb_results.append(imdb_people_images(imdb_id, page_no)[0])
		except: pass
	__handle__ = int(argv[1])
	threads = []
	tmdb_images = []
	all_images = []
	tmdb_results = []
	imdb_results = []
	rolling_count = int(rolling_count)
	image_base = 'https://image.tmdb.org/t/p/%s%s'
	if page_no == 1: threads.append(Thread(target=get_tmdb))
	threads.append(Thread(target=get_imdb))
	[i.start() for i in threads]
	[i.join() for i in threads]
	if page_no == 1:
		tmdb_image_info = sorted(tmdb_results[0]['profiles'], key=lambda x: x['file_path'])
		tmdb_images = [('%03d_%sx%s' % (count, i['height'], i['width']), image_base % ('original', i['file_path']), image_base % ('w185', i['file_path'])) for count, i in enumerate(tmdb_image_info, rolling_count+1)]
		all_images.extend(tmdb_images)
	rolling_count = rolling_count + len(tmdb_images)
	imdb_image_info = sorted(imdb_results[0], key=lambda x: x['title'])
	imdb_images = [('%s_%03d' % (i['title'], count), i['image'], i['thumb']) for count, i in enumerate(imdb_image_info, rolling_count+1)]
	all_images.extend(imdb_images)
	all_images_json = json.dumps([i[1] for i in all_images])
	for count, item in enumerate(all_images):
		cm = []
		thumb_url = item[2]
		image_url = item[1]
		name = item[0]
		url_params = {'mode': 'slideshow_image', 'all_images': all_images_json, 'current_index': count}
		down_file_params = {'mode': 'download_file', 'name': name, 'url': (image_url, thumb_url), 'db_type': 'image', 'image': icon}
		cm.append((ls(32747),'RunPlugin(%s)' % build_url(down_file_params)))
		url = build_url(url_params)
		listitem = xbmcgui.ListItem(name)
		listitem.addContextMenuItems(cm)
		listitem.setArt({'icon': thumb_url, 'poster': thumb_url, 'thumb': thumb_url, 'fanart': fanart, 'banner': thumb_url, 'landscape': thumb_url})
		xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
	if len(imdb_images) == 48:
		rolling_count = rolling_count + len(imdb_images)
		params = {'mode': 'people_search.image_results', 'actor_id': actor_id, 'actor_name': actor_name, 'actor_image': actor_image, 'page_no': page_no+1, 'rolling_count': rolling_count}
		add_dir(params, ls(32799), iconImage='item_next.png', fanartImage=fanart, isFolder=True)
	xbmcplugin.setContent(__handle__, 'images')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.images', 'images')

def people_tagged_image_results(actor_name, actor_id, actor_image, page_no, rolling_count):
	__handle__ = int(argv[1])
	rolling_count = int(rolling_count)
	image_base = 'https://image.tmdb.org/t/p/%s%s'
	try: results = tmdb_people_tagged_pictures(actor_id, page_no)
	except: results = []
	image_info = sorted(results['results'], key=lambda x: x['file_path'])
	all_images_json = json.dumps([image_base % ('original', i['file_path']) for i in image_info])
	for count, item in enumerate(image_info):
		try:
			rolling_count += 1
			cm = []
			thumb_url = image_base % ('w185', item['file_path'])
			image_url = image_base % ('original', item['file_path'])
			name = '%03d_%s' % (rolling_count, item['media']['title'])
			url_params = {'mode': 'slideshow_image', 'all_images': all_images_json, 'current_index': count}
			down_file_params = {'mode': 'download_file', 'name': name, 'url': (image_url, thumb_url), 'db_type': 'image', 'image': icon}
			cm.append((ls(32747),'RunPlugin(%s)' % build_url(down_file_params)))
			url = build_url(url_params)
			listitem = xbmcgui.ListItem(name)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': thumb_url, 'poster': thumb_url, 'thumb': thumb_url, 'fanart': fanart, 'banner': thumb_url})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
		except: pass
	if results['total_pages'] > page_no:
		params = {'mode': 'people_search.image_results', 'actor_id': actor_id, 'actor_name': actor_name, 'actor_image': actor_image, 'page_no': page_no+1, 'rolling_count': rolling_count}
		add_dir(params, ls(32799), iconImage='item_next.png', fanartImage=fanart, isFolder=True)
	xbmcplugin.setContent(__handle__, 'images')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.images', 'images')

def browser_image(folder_path):
	import xbmcvfs
	import os
	__handle__ = int(argv[1])
	files = xbmcvfs.listdir(folder_path)[1]
	files = sorted(files)
	thumbs_path = os.path.join(folder_path, '.thumbs')
	thumbs = xbmcvfs.listdir(thumbs_path)[1]
	thumbs = sorted(thumbs)
	all_images_json = json.dumps([os.path.join(folder_path, i) for i in files])
	for count, item in enumerate(files):
		try:
			cm = []
			image_url = os.path.join(folder_path, item)
			try:
				thumb_url = [i for i in thumbs if i == item][0]
				thumb_url = os.path.join(thumbs_path, thumb_url)
			except:
				thumb_url = image_url
			url_params = {'mode': 'slideshow_image', 'all_images': all_images_json, 'current_index': count}
			url = build_url(url_params)
			cm.append(('[B]%s[/B]' % ls(32785),'RunPlugin(%s)' % build_url({'mode': 'delete_image', 'image_url': image_url, 'thumb_url': thumb_url})))
			listitem = xbmcgui.ListItem(item)
			listitem.addContextMenuItems(cm)
			listitem.setInfo(type='image', infoLabels={'Title': item})
			listitem.setArt({'icon': thumb_url, 'poster': thumb_url, 'thumb': thumb_url, 'fanart': fanart, 'banner': thumb_url})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
		except: pass
	xbmcplugin.setContent(__handle__, 'images')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.images', 'images')

def show_image(image_url):
	xbmc.executebuiltin('ShowPicture(%s)' % image_url)

def delete_image(image_url, thumb_url):
	if not xbmcgui.Dialog().yesno('Fen', ls(32580)): return
	import xbmcvfs
	from modules.nav_utils import notification
	xbmcvfs.delete(thumb_url)
	try: xbmcvfs.delete(image_url)
	except: return notification(ls(32490), 1500)
	xbmc.executebuiltin('Container.Refresh')
	return notification(ls(32576), 1500)

def slideshow_image(all_images, current_index):
	all_images = json.loads(all_images)
	current_window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
	focus_id = current_window.getFocusId()
	slide_items = []
	for item in all_images:
		listitem = xbmcgui.ListItem()
		listitem.setArt({'fen_slideshow_image': item})
		slide_items.append(listitem)
	slideshow = SlideShow('fen-pictureviewer.xml', addon_dir, listitems=slide_items, index=int(current_index))
	ending_position = slideshow.run()
	current_window.getControl(focus_id).selectItem(ending_position)

class SlideShow(xbmcgui.WindowXMLDialog):
	def __init__(self, *args, **kwargs):
		self.xml_window_id = 5000
		self.previous_menu_action = [9, 92, 10]
		self.listitems = kwargs.get('listitems')
		self.index = kwargs.get('index')
		self.action = None

	def onInit(self):
		super(SlideShow, self).onInit()
		self.getControl(self.xml_window_id).addItems(self.listitems)
		self.getControl(self.xml_window_id).selectItem(self.index)
		self.setFocusId(self.xml_window_id)

	def run(self):
		self.doModal()
		return self.position

	def onAction(self, action):
		if action in self.previous_menu_action:
			self.position = self.getControl(self.xml_window_id).getSelectedPosition()
			self.close()
