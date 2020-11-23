# -*- coding: utf-8 -*-

'''
	Simple XBMC Download Script
	Copyright (C) 2013 Sean Poyser (seanpoyser@gmail.com)

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import xbmc, xbmcgui, xbmcplugin, xbmcvfs
import re
import json
import os
from sys import argv

try: from urllib import unquote
except: from urllib.parse import unquote
try: from urlparse import parse_qsl, urlparse
except ImportError: from urllib.parse import parse_qsl, urlparse
try: from urllib2 import Request, urlopen
except ImportError: from urllib.request import Request, urlopen

from modules.nav_utils import hide_busy_dialog, notification
from modules.utils import clean_file_name, clean_title, to_utf8, safe_string, remove_accents
from modules.utils import local_string as ls
from modules.settings_reader import get_setting
from modules.settings import download_directory
# from modules.utils import logger

def download(params, url):
	def runner(headers, url, transname, image, dest, db_type, ext):
		folder_dest = dest
		dest = os.path.join(dest, transname + ext)
		doDownload(url, folder_dest, dest, transname, image, json.dumps(headers), db_type)
	
	if url is None:
		hide_busy_dialog()
		notification(ls(32692), 4000)
		return

	json_meta = params.get('meta')
	if json_meta:
		meta = json.loads(json_meta)
		db_type = meta.get('vid_type')
		title = meta.get('search_title')
		year = meta.get('year')
		image = meta.get('poster')
		season = meta.get('season')
		episode = meta.get('episode')
		name = params.get('name')
	else:
		db_type = params.get('db_type')
		image = params.get('image')
		title = params.get('name')

	title = clean_file_name(title)

	if url.startswith(('(', '[')):
		from ast import literal_eval
		url = literal_eval(url)

	if db_type in ('image', 'archive_direct'):
		transname = title
	elif not 'http' in url:
		from apis.furk_api import FurkAPI
		from indexers.furk import filter_furk_tlist
		from modules.source_utils import seas_ep_query_list
		t_files = FurkAPI().t_files(url)
		t_files = [i for i in t_files if 'video' in i['ct'] and 'bitrate' in i]
		name, url = filter_furk_tlist(t_files, (None if db_type == 'movie' else seas_ep_query_list(season, episode)))[0:2]
		transname = name.translate(None, '\/:*?"<>|').strip('.')
	else:
		name_url = unquote(url)
		file_name = clean_title(name_url.split('/')[-1])
		if clean_title(title).lower() in file_name.lower():
			transname = os.path.splitext(urlparse(name_url).path)[0].split('/')[-1]
		else:
			try: transname = name.translate(None, '\/:*?"<>|').strip('.')
			except: transname = os.path.splitext(urlparse(name_url).path)[0].split('/')[-1]

	transname = to_utf8(safe_string(remove_accents(transname)))
	
	dest = download_directory(db_type)
	if not dest: return hide_busy_dialog()
	
	levels =['../../../..', '../../..', '../..', '..']
	for level in levels:
		try: xbmcvfs.mkdir(os.path.abspath(os.path.join(dest, level)))
		except: pass
	xbmcvfs.mkdir(dest)

	if db_type == 'image':
		thumb_dest = os.path.join(dest, '.thumbs')
		url = [[url[0], dest], [url[1], thumb_dest]]
		for level in levels:
			try: xbmcvfs.mkdir(os.path.abspath(os.path.join(thumb_dest, level)))
			except: pass
		xbmcvfs.mkdir(thumb_dest)

	elif db_type in ('movie', 'episode'):
		folder_rootname = '%s (%s)' % (title, year)
		dest = os.path.join(dest, folder_rootname)
		if db_type == 'episode':
			dest = os.path.join(dest, 'Season %02d' %  int(season))

	elif db_type == 'archive_direct':
		dest = os.path.join(dest, transname)

	try: headers = dict(parse_qsl(url.rsplit('|', 1)[1]))
	except: headers = dict('')
	
	try:
		source = json.loads(params['source'])
		if source[0]['scrape_provider'] == 'pm-cloud':
			from apis.premiumize_api import PremiumizeAPI
			headers = PremiumizeAPI().headers()
	except: pass
	
	try: url = url.split('|')[0]
	except: pass

	if 'archive' in db_type:
		ext = '.zip'
	elif db_type == 'audio':
		ext = os.path.splitext(urlparse(url).path)[1][1:]
		if not ext in ['wav', 'mp3', 'ogg', 'flac', 'wma', 'aac']: ext = 'mp3'
		ext = '.%s' % ext
	elif db_type == 'image':
		image_urls = []
		for item in url:
			ext = os.path.splitext(urlparse(item[0]).path)[1][1:]
			if not ext in ['jpg', 'jpeg', 'jpe', 'jif', 'jfif', 'jfi', 'bmp', 'dib', 'png',
						   'gif', 'webp', 'tiff', 'tif', 'psd', 'raw', 'arw', 'cr2', 'nrw',
						   'k25', 'jp2', 'j2k', 'jpf', 'jpx', 'jpm', 'mj2']: ext = 'jpg'
		   	ext = '.%s' % ext
			image_urls.append([item[0], item[1], ext])
		url = image_urls
	else:
		ext = os.path.splitext(urlparse(url).path)[1][1:]
		if not ext in ['mp4', 'mkv', 'flv', 'avi', 'mpg']: ext = 'mp4'
		ext = '.%s' % ext
	if db_type == 'image':
		for item in url:
			runner(headers, item[0], transname, image, item[1], db_type, item[2])
	else:
		runner(headers, url, transname, image, dest, db_type, ext)

def getResponse(url, headers, size):
	try:
		if size > 0:
			size = int(size)
			headers['Range'] = 'bytes=%d-' % size

		req = Request(url, headers=headers)

		resp = urlopen(req, timeout=30)
		return resp
	except:
		return None

def done(title, db_type, downloaded, image):
	if db_type == 'image':
		if downloaded: notification('[I]%s[/I]' % ls(32576), 2500, image)
		else: notification('[I]%s[/I]' % ls(32691), 2500, image)
	else:
		playing = xbmc.Player().isPlaying()

		text = xbmcgui.Window(10000).getProperty('FEN-DOWNLOADED')

		if len(text) > 0:
			text += '[CR]'

		if downloaded:
			text += '[B]%s[/B] : %s' % (title, '[COLOR forestgreen]%s %s[/COLOR]' % (ls(32107), ls(32576)))
		else:
			text += '[B]%s[/B] : %s' % (title, '[COLOR red]%s %s[/COLOR]' % (ls(32107), ls(32490)))

		xbmcgui.Window(10000).setProperty('FEN-DOWNLOADED', text)

		if (not downloaded) or (not playing): 
			xbmcgui.Dialog().ok('Fen', text)
	xbmcgui.Window(10000).clearProperty('FEN-DOWNLOADED')

def doDownload(url, folder_dest, dest, title, image, headers, db_type):
	headers = json.loads(headers)
	file = dest.rsplit(os.sep, 1)[-1]
	resp = getResponse(url, headers, 0)

	if not resp:
		hide_busy_dialog()
		xbmcgui.Dialog().ok('Fen', ls(32490))
		return

	try:    content = int(resp.headers['Content-Length'])
	except: content = 0

	try:    resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
	except: resumable = False

	if resumable:
		print "Download is resumable"

	if content < 1:
		hide_busy_dialog()
		xbmcgui.Dialog().ok('Fen', ls(32490))
		return

	size = 1024 * 1024
	mb   = content / (1024 * 1024)

	if content < size:
		size = content

	total   = 0
	notify  = 0
	errors  = 0
	count   = 0
	resume  = 0
	sleep   = 0

	hide_busy_dialog()

	if db_type != 'image':
		if not xbmcgui.Dialog().yesno('Fen', '[B]%s[/B]' % title.upper(), ls(32688) % mb, ls(32689)):
			return
		
		notification_setting = get_setting('download.notification')
		show_notifications = True if notification_setting == '1' else False
		persistent_notifications = True if notification_setting == '2' else False
		suppress_during_playback = True if get_setting('download.suppress') == 'true' else False
		try: notification_frequency = int(get_setting('download.frequency'))
		except: notification_frequency = 10
		
		if persistent_notifications:
			progressDialog = xbmcgui.DialogProgressBG()
			progressDialog.create(ls(32690) % title, '')
			progressDialog.update(0, '')

	xbmcvfs.mkdir(folder_dest)

	f = xbmcvfs.File(dest, 'w')

	chunk  = None
	chunks = []


	while True:

		downloaded = total
		for c in chunks:
			downloaded += len(c)
		percent = min(100 * downloaded / content, 100)

		if db_type != 'image':
			playing = xbmc.Player().isPlaying()

			if persistent_notifications:
				progressDialog.update(percent, ls(32690) % title, '')

			elif show_notifications:
				if percent >= notify:
					line1 = ''
					if playing and not suppress_during_playback: notification('%s - [I]%s[/I]' % (str(percent)+'%', title), 10000, image)
					elif (not playing): notification('%s - [I]%s[/I]' % (str(percent)+'%', title), 10000, image)

					notify += notification_frequency

		chunk = None
		error = False

		try:        
			chunk  = resp.read(size)
			if not chunk:
				if percent < 99:
					error = True
				else:
					while len(chunks) > 0:
						c = chunks.pop(0)
						f.write(c)
						del c

					f.close()
					try:
						progressDialog.close()
					except Exception:
						pass
					return done(title, db_type, True, image)

		except Exception, e:
			print str(e)
			error = True
			sleep = 10
			errno = 0

			if hasattr(e, 'errno'):
				errno = e.errno

			if errno == 10035: # 'A non-blocking socket operation could not be completed immediately'
				pass

			if errno == 10054: #'An existing connection was forcibly closed by the remote host'
				errors = 10 #force resume
				sleep  = 30

			if errno == 11001: # 'getaddrinfo failed'
				errors = 10 #force resume
				sleep  = 30

		if chunk:
			errors = 0
			chunks.append(chunk)
			if len(chunks) > 5:
				c = chunks.pop(0)
				f.write(c)
				total += len(c)
				del c

		if error:
			errors += 1
			count  += 1
			xbmc.sleep(sleep*1000)

		if (resumable and errors > 0) or errors >= 10:
			if (not resumable and resume >= 50) or resume >= 500:
				#Give up!
				try:
					progressDialog.close()
				except Exception:
					pass
				return done(title, db_type, False, image)

			resume += 1
			errors  = 0
			if resumable:
				chunks  = []
				#create new response
				resp = getResponse(url, headers, total)
			else:
				#use existing response
				pass


