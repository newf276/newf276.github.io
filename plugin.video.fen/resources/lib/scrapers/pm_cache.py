# -*- coding: utf-8 -*-
from apis.premiumize_api import PremiumizeAPI
from modules.source_utils import get_release_quality, get_file_info, supported_video_extensions
from modules.utils import clean_title, clean_file_name, normalize
from scrapers import internal_results
from modules.settings import debrid_enabled
# from modules.utils import logger

Premiumize = PremiumizeAPI()

class PremiumizeSource:
	def __init__(self):
		self.scrape_provider = 'pm-cloud'
		self.enabled = debrid_enabled('pm')
		self.sources = []
		self.threads  = []
		self.scrape_results = []

	def results(self, info):
		try:
			if not self.enabled: return internal_results(self.scrape_provider, self.sources)
			self.info = info
			self.db_type = self.info.get("db_type")
			self.title = self.info.get("title")
			self.year = self.info.get("year")
			if self.year: self.rootname = '%s (%s)' % (self.title, self.year)
			else: self.rootname = self.title
			self.season = self.info.get("season")
			self.episode = self.info.get("episode")
			self.query = clean_title(self.title)
			self.file_query = self._episode_query_list() if self.db_type == 'episode' else self._year_query_list()
			self.extensions = supported_video_extensions()
			self._scrape_cloud()
			if not self.scrape_results: return internal_results(self.scrape_provider, self.sources)
			def _process():
				for item in self.scrape_results:
					try:
						file_name = normalize(item['name'])
						URLName = clean_file_name(file_name).replace('html', ' ').replace('+', ' ').replace('-', ' ')
						path = item['path']
						file_dl = item['id']
						size = float(item['size'])/1073741824
						video_quality = get_release_quality(file_name, path)
						details = get_file_info(file_name)
						if not details: details = get_file_info(path)
						source_item = {'name': file_name,
										'title': file_name,
										'URLName': URLName,
										'quality': video_quality,
										'size': size,
										'size_label': '%.2f GB' % size,
										'extraInfo': details,
										'url_dl': file_dl,
										'id': file_dl,
										'downloads': False,
										'direct': True,
										'source': self.scrape_provider,
										'scrape_provider': self.scrape_provider}
						yield source_item
					except: pass
			self.sources = list(_process())
		except Exception as e:
			from modules.utils import logger
			logger('FEN premiumize scraper Exception', e)
		internal_results(self.scrape_provider, self.sources)
		return self.sources

	def _scrape_cloud(self):
		try:
			cloud_files = Premiumize.user_cloud_all()['files']
			cloud_files = [i for i in cloud_files if i['path'].lower().endswith(tuple(self.extensions))]
			cloud_files = sorted(cloud_files, key=lambda k: k['name'])
		except: return self.sources
		for item in cloud_files:
			item_name = clean_title(normalize(item['name']))
			if self.query in item_name:
				if self.db_type == 'movie':
					if any(x in item['name'] for x in self.file_query):
						self.scrape_results.append(item)
				else:
					if any(x in item_name for x in self.file_query):
						self.scrape_results.append(item)

	def _year_query_list(self):
		return [str(self.year), str(int(self.year)+1), str(int(self.year)-1)]

	def _episode_query_list(self):
		return ['s%02de%02d' % (int(self.season), int(self.episode)),
				'%dx%02d' % (int(self.season), int(self.episode)),
				'%02dx%02d' % (int(self.season), int(self.episode)),
				'season%02depisode%02d' % (int(self.season), int(self.episode)),
				'season%depisode%02d' % (int(self.season), int(self.episode)),
				'season%depisode%d' % (int(self.season), int(self.episode))]

