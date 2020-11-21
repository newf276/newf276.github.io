# -*- coding: utf-8 -*-
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

from modules.nav_utils import show_busy_dialog, hide_busy_dialog, notification
from modules.utils import clean_file_name, clean_title, to_utf8, safe_string, remove_accents
from modules.utils import local_string as ls
from modules.settings_reader import get_setting
from modules.settings import download_directory
from modules.utils import logger

window = xbmcgui.Window(10000)

image_extensions = ['jpg', 'jpeg', 'jpe', 'jif', 'jfif', 'jfi', 'bmp', 'dib', 'png', 'gif', 'webp', 'tiff', 'tif',
					'psd', 'raw', 'arw', 'cr2', 'nrw', 'k25', 'jp2', 'j2k', 'jpf', 'jpx', 'jpm', 'mj2']

# down_file_params = {'mode': 'downloader',
# 					'action': 'meta.single',
# 					'name': meta.get('rootname'),
# 					'source': source,
# 					'url': url_dl,
# 					'provider': scrape_provider,
# 					'meta': meta_json,
#					'db_type': [provided by meta or assigned],
#					'image': [provided by meta or assigned]}


class Downloader:
	def __init__(self, params):
		self.params = params
		self.downloads_string = 'fen.current_downloads'
		self.downPrep()

	@staticmethod
	def addDownload(add_dict):
		try: current_down_list = json.loads(window.getProperty(self.downloads_string))
		except: current_down_list = []
		current_down_list.append(add_dict)
		current_down_list = json.dumps(current_down_list)
		window.setProperty(self.downloads_string, current_down_list)

	# @staticmethod
	# def updateDownload(current_down_list, ):
	# 	window.setProperty(current_down_list)

	@staticmethod
	def removeDownload(remove_dict):
		try: current_down_list = json.loads(window.getProperty(self.downloads_string))
		except: return
		current_down_list.remove(remove_dict)
		current_down_list = json.dumps(current_down_list)
		window.setProperty(self.downloads_string, current_down_list)

	def run(self):
		show_busy_dialog()
		self.getURLandHeaders()
		if self.url in (None, 'None', ''):
			hide_busy_dialog()
			return notification(ls(32692), 4000)
		self.getDownFolder()
		self.getFilename()
		self.getExtension()
		self.getDestinationFolder()
		if self.db_type in ('image',):
			for item in self.url: self.download_runner(item[0], item[1], item[2])
		else:
			self.download_runner(self.url, self.final_destination, self.extension)

	def downPrep(self):
		if 'meta' in self.params:
			json_meta = self.params.get('meta')
			meta = json.loads(json_meta)
			title = meta.get('search_title')
			self.db_type = meta.get('vid_type')
			self.year = meta.get('year')
			self.image = meta.get('poster')
			self.season = meta.get('season')
			self.episode = meta.get('episode')
			self.name = self.params.get('name')
		else:
			title = self.params.get('name')
			self.db_type = self.params.get('db_type')
			self.image = self.params.get('image')
			self.name = None
		self.title = clean_file_name(title)
		self.provider = self.params.get('provider')
		self.action = self.params.get('action')
		self.source = self.params.get('source')
		self.final_name = None

	def download_runner(self, url, folder_dest, ext):
		dest = os.path.join(folder_dest, self.final_name + ext)
		# try: self.current_downloads = json.loads(window.getProperty(self.downloads_string))
		# except: self.current_downloads = []
		# self.current_downloads.append({'url': url, 'folder_dest': folder_dest, 'final_name': self.final_name})
		# window.setProperty(self.downloads_string, self.current_downloads)
		self.doDownload(url, folder_dest, dest)

	def getURLandHeaders(self):
		url = self.params.get('url')
		if url in (None, 'None', ''):
			if self.action == 'meta.single':
				from modules.sources import Sources
				source = json.loads(self.source)[0]
				url = Sources().resolve_sources(source)
		elif self.db_type == 'image':
			from ast import literal_eval
			url = literal_eval(url)
			image_urls = []
			for item in url:
				ext = os.path.splitext(urlparse(item).path)[1][1:]
				if not ext in image_extensions: ext = 'jpg'
			   	ext = '.%s' % ext
				item = item.split(ext)[0]
				image_urls.append([item, ext])
			url = image_urls
		try: headers = dict(parse_qsl(url.rsplit('|', 1)[1]))
		except: headers = dict('')
		try: url = url.split('|')[0]
		except: pass
		self.url = url
		self.headers = headers

	def getDownFolder(self):
		self.down_folder = download_directory(self.db_type)
		levels =['../../../..', '../../..', '../..', '..']
		for level in levels:
			try: xbmcvfs.mkdir(os.path.abspath(os.path.join(self.down_folder, level)))
			except: pass
		xbmcvfs.mkdir(self.down_folder)

	def getDestinationFolder(self):
		if self.db_type == 'image':
			thumb_dest = os.path.join(self.down_folder, '.thumbs')
			self.url = [[url[0], dest], [url[1], thumb_dest]]
			for level in levels:
				try: xbmcvfs.mkdir(os.path.abspath(os.path.join(thumb_dest, level)))
				except: pass
			xbmcvfs.mkdir(thumb_dest)
			self.final_destination = None
		elif self.db_type in ('movie', 'episode'):
			folder_rootname = '%s (%s)' % (self.title, self.year)
			self.final_destination = os.path.join(self.down_folder, folder_rootname)
			if self.db_type == 'episode':
				self.final_destination = os.path.join(self.down_folder, folder_rootname, 'Season %02d' %  int(self.season))
		elif self.db_type in ('archive',):
			self.final_destination = os.path.join(self.down_folder, self.final_name)

	def getFilename(self):
		if self.final_name: final_name = self.final_name
		elif self.db_type in ('image', 'archive'):
			final_name = self.title
		else:
			name_url = unquote(self.url)
			file_name = clean_title(name_url.split('/')[-1])
			if clean_title(self.title).lower() in file_name.lower():
				final_name = os.path.splitext(urlparse(name_url).path)[0].split('/')[-1]
			else:
				try: final_name = self.name.translate(None, '\/:*?"<>|').strip('.')
				except: final_name = os.path.splitext(urlparse(name_url).path)[0].split('/')[-1]
		self.final_name = to_utf8(safe_string(remove_accents(final_name)))

	def getExtension(self):
		if any(i in self.db_type for i in ['archive', 'pack']):
			ext = '.zip'
		elif self.db_type == 'audio':
			ext = os.path.splitext(urlparse(self.url).path)[1][1:]
			if not ext in ['wav', 'mp3', 'ogg', 'flac', 'wma', 'aac']: ext = 'mp3'
			ext = '.%s' % ext
		elif self.db_type == 'image':
			ext = None
		else:
			ext = os.path.splitext(urlparse(self.url).path)[1][1:]
			if not ext in ['mp4', 'mkv', 'flv', 'avi', 'mpg']: ext = 'mp4'
			ext = '.%s' % ext
		self.extension = ext

	def confirmDownload(self, mb):
		if self.db_type != 'image':
			if not xbmcgui.Dialog().yesno('Fen', '[B]%s[/B]' % self.final_name.upper(), ls(32688) % mb, ls(32689)): return False
		return True

	def doDownload(self, url, folder_dest, dest):
		headers = self.headers
		file = dest.rsplit(os.sep, 1)[-1]
		resp = self.getResponse(url, headers, 0)
		if not resp:
			hide_busy_dialog()
			xbmcgui.Dialog().ok('Fen', ls(32490))
			return
		try:    content = int(resp.headers['Content-Length'])
		except: content = 0
		try:    resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
		except: resumable = False
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
		if not self.confirmDownload(mb): return
		if self.db_type != 'image':
			notification_setting = get_setting('download.notification')
			show_notifications = True if notification_setting == '1' else False
			persistent_notifications = True if notification_setting == '2' else False
			suppress_during_playback = True if get_setting('download.suppress') == 'true' else False
			try: notification_frequency = int(get_setting('download.frequency'))
			except: notification_frequency = 10
			if persistent_notifications:
				progressDialog = xbmcgui.DialogProgressBG()
				progressDialog.create(ls(32690) % self.final_name, '')
				progressDialog.update(0, '')
		xbmcvfs.mkdir(folder_dest)
		f = xbmcvfs.File(dest, 'w')
		chunk  = None
		chunks = []
		while True:
			downloaded = total
			for c in chunks: downloaded += len(c)
			percent = min(100 * downloaded / content, 100)
			if self.db_type != 'image':
				playing = xbmc.Player().isPlaying()
				if persistent_notifications:
					progressDialog.update(percent, ls(32690) % self.final_name, '')
				elif show_notifications:
					if percent >= notify:
						line1 = ''
						if playing and not suppress_during_playback: notification('%s - [I]%s[/I]' % (str(percent)+'%', self.final_name), 10000, self.image)
						elif (not playing): notification('%s - [I]%s[/I]' % (str(percent)+'%', title), 10000, self.image)
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
						try: progressDialog.close()
						except Exception: pass
						return self.done(self.final_name, self.db_type, True, self.image)
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
					try:
						progressDialog.close()
					except Exception:
						pass
					return self.done(self.final_name, self.db_type, False, self.image)
				resume += 1
				errors  = 0
				if resumable:
					chunks  = []
					resp = self.getResponse(url, headers, total)
				else:
					pass

	def getResponse(self, url, headers, size):
		try:
			if size > 0:
				size = int(size)
				headers['Range'] = 'bytes=%d-' % size
			req = Request(url, headers=headers)
			resp = urlopen(req, timeout=15)
			return resp
		except:
			return None

	def done(self, title, db_type, downloaded, image):
		if db_type == 'image':
			if downloaded: notification('[I]%s[/I]' % ls(32576), 2500, image)
			else: notification('[I]%s[/I]' % ls(32691), 2500, image)
		else:
			playing = xbmc.Player().isPlaying()
			if downloaded:
				text = '[B]%s[/B] : %s' % (title, '[COLOR forestgreen]%s %s[/COLOR]' % (ls(32107), ls(32576)))
			else:
				text = '[B]%s[/B] : %s' % (title, '[COLOR red]%s %s[/COLOR]' % (ls(32107), ls(32490)))
			if (not downloaded) or (not playing): 
				xbmcgui.Dialog().ok('Fen', text)



