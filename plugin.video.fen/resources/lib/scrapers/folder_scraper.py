# -*- coding: utf-8 -*-
import xbmcvfs
import os
from threading import Thread
try: from urlparse import urlparse
except ImportError: from urllib.parse import urlparse
from caches import fen_cache
from modules.source_utils import get_release_quality, get_file_info, supported_video_extensions
from modules.utils import clean_title, clean_file_name, normalize
from scrapers import internal_results
from modules.settings import source_folders_directory
# from modules.utils import logger

class FolderScraper:
	def __init__(self, scrape_provider, scraper_name):
		self.scrape_provider = scrape_provider
		self.scraper_name = scraper_name
		self.threads  = []
		self.sources = []
		self.scrape_results = []
		self.cache = fen_cache.FenCache()
		self.extensions = supported_video_extensions()

	def results(self, info):
		try:
			self.info = info
			self.db_type = self.info.get("db_type")
			self.folder_path = source_folders_directory(self.db_type, self.scrape_provider)
			if not self.folder_path: return internal_results(self.scrape_provider, self.sources)
			self.title = self.info.get("title")
			self.year = self.info.get("year")
			if self.year: self.rootname = '%s (%s)' % (self.title, self.year)
			else: self.rootname = self.title
			self.season = self.info.get("season")
			self.episode = self.info.get("episode")
			self.title_query = clean_title(normalize(self.title))
			self.folder_query = self._season_query_list() if self.db_type == 'episode' else self._year_query_list()
			self.file_query = self._episode_query_list() if self.db_type == 'episode' else self._year_query_list()
			self._scrape_directory((self.folder_path, False))
			if not self.scrape_results: return internal_results(self.scrape_provider, self.sources)
			def _process():
				for item in self.scrape_results:
					try:
						file_name = item[0]
						file_dl = item[1]
						URLName = clean_file_name(file_name).replace('html', ' ').replace('+', ' ').replace('-', ' ')
						try: size = item[2]
						except: size = self._get_size(file_dl) if not file_dl.endswith('.strm') else 'strm'
						details = get_file_info(file_name)
						video_quality = get_release_quality(file_name, file_dl)
						source_item = {'name': file_name,
											'title': file_name,
											'URLName': URLName,
											'quality': video_quality,
											'size': size,
											'size_label': '%.2f GB' % size,
											'extraInfo': details,
											'url_dl': file_dl,
											'id': file_dl,
											self.scrape_provider : True,
											'direct': True,
											'source': self.scraper_name,
											'scrape_provider': self.scrape_provider}
						yield source_item
					except: pass
			self.sources = list(_process())
		except Exception as e:
			from modules.utils import logger
			logger('FEN folders scraper Exception', e)
		internal_results(self.scrape_provider, self.sources)
		return self.sources

	def _assigned_content(self, raw_name):
		try:
			string = 'FEN_FOLDER_%s' % raw_name
			return self.cache.get(string)
		except:
			return False

	def _list_dirs(self, folder_name):
		return xbmcvfs.listdir(folder_name)

	def _scrape_directory(self, folder_info):
		def _process(item):
			file_type = item[1]
			item_name = clean_title(normalize(item[0]))
			if file_type == 'file':
				ext = os.path.splitext(urlparse(item[0]).path)[-1]
				if ext in self.extensions:
					if self.db_type == 'movie':
						if self.assigned_content or self.title_query in item_name:
							url_path = self.url_path(folder_name, item[0])
							size = self._get_size(url_path) if not url_path.endswith('.strm') else 'strm'
							self.scrape_results.append((item[0], url_path, size))
					elif any(x in item_name for x in self.file_query):
						if self.assigned_content or not folder_name in self.folder_path:
							url_path = self.url_path(folder_name, item[0])
							size = self._get_size(url_path) if not url_path.endswith('.strm') else 'strm'
							self.scrape_results.append((item[0], url_path, size))
						elif self.title_query in item_name:
							url_path = self.url_path(folder_name, item[0])
							size = self._get_size(url_path) if not url_path.endswith('.strm') else 'strm'
							self.scrape_results.append((item[0], url_path, size))  
			elif file_type == 'folder':
				if not assigned_folder:
					self.assigned_content = self._assigned_content(normalize(item[0]))
					if self.assigned_content:
						if self.assigned_content == self.rootname:
							new_folder = os.path.join(folder_name, item[0])
							folder_results.append((new_folder, True))
					elif self.title_query in item_name or any(x in item_name for x in self.folder_query):
						new_folder = os.path.join(folder_name, item[0])
						folder_results.append((new_folder, self.assigned_content))
				elif assigned_folder:
					if any(x in item_name for x in self.folder_query):
						new_folder = os.path.join(folder_name, item[0])
						folder_results.append((new_folder, True))
				elif self.title_query in item_name or any(x in item_name for x in self.folder_query):
					new_folder = os.path.join(folder_name, item[0])
					folder_results.append((new_folder, self.assigned_content))
		folder_files = []
		folder_results = []
		assigned_folder = folder_info[1]
		self.assigned_content = assigned_folder if assigned_folder else ''
		folder_name = folder_info[0]
		string = 'fen_FOLDERSCRAPER_%s_%s' % (self.scrape_provider, folder_name)
		dirs, files = fen_cache.cache_object(self._list_dirs, string, folder_name, json=False, expiration=1)
		for i in dirs: folder_files.append((i, 'folder'))
		for i in files: folder_files.append((i, 'file'))
		folder_threads = []
		for item in folder_files: folder_threads.append(Thread(target=_process, args=(item,)))
		[i.start() for i in folder_threads]
		[i.join() for i in folder_threads]
		if not folder_results: return
		return self._scraper_worker(folder_results)

	def _scraper_worker(self, folder_results):
		scraper_threads = []
		for i in folder_results: scraper_threads.append(Thread(target=self._scrape_directory, args=(i,)))
		[i.start() for i in scraper_threads]
		[i.join() for i in scraper_threads]

	def url_path(self, folder, file):
		url_path = os.path.join(folder, file)
		return url_path

	def _get_size(self, file):
		f = xbmcvfs.File(file)
		s = f.size()
		f.close()
		size = float(s)/1073741824
		return size

	def _year_query_list(self):
		return (str(self.year), str(int(self.year)+1), str(int(self.year)-1))

	def _season_query_list(self):
		return ['season%02d' % int(self.season), 'season%s' % self.season]

	def _episode_query_list(self):
		return ['s%02de%02d' % (int(self.season), int(self.episode)),
				'%dx%02d' % (int(self.season), int(self.episode)),
				'%02dx%02d' % (int(self.season), int(self.episode)),
				'season%02depisode%02d' % (int(self.season), int(self.episode)),
				'season%depisode%02d' % (int(self.season), int(self.episode)),
				'season%depisode%d' % (int(self.season), int(self.episode))]
