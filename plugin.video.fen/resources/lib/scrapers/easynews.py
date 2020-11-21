# -*- coding: utf-8 -*-
import sys
from apis.easynews_api import import_easynews
from modules.source_utils import get_release_quality, get_file_info
from modules.utils import clean_file_name, normalize
from scrapers import internal_results, build_internal_scrapers_label, label_settings
from modules.settings_reader import get_setting
# from modules.utils import logger

EasyNews = import_easynews()

class EasyNewsSource:
	def __init__(self):
		self.scrape_provider = 'easynews'
		self.sources = []
		self.max_results = int(get_setting('easynews_limit'))

	def results(self, info):
		try:
			self.info = info
			search_name = self._search_name()
			files = EasyNews.search(search_name)
			if not files: return internal_results(self.scrape_provider, self.sources)
			files = files[0:self.max_results]
			self.label_settings = label_settings(self.info['scraper_settings'], self.scrape_provider)
			def _process():
				for item in files:
					try:
						file_name = normalize(item['name'])
						url_dl = item['url_dl']
						size = float(int(item['rawSize']))/1073741824
						details = get_file_info(file_name)
						video_quality = get_release_quality(file_name, url_dl)
						label, multiline_label = build_internal_scrapers_label(self.label_settings, file_name, details, size, video_quality)
						source_item = {'name': file_name,
										'label': label,
										'multiline_label': multiline_label,
										'quality': video_quality,
										'size': size,
										'url_dl': url_dl,
										'id': url_dl,
										'local': False,
										'direct': True,
										'source': self.scrape_provider,
										'scrape_provider': self.scrape_provider}
						yield source_item
					except Exception as e:
						from modules.utils import logger
						logger('FEN easynews yield source', str(e))
						pass
			self.sources = list(_process())
		except Exception as e:
			from modules.utils import logger
			logger('FEN easynews scraper Exception', str(e))
		internal_results(self.scrape_provider, self.sources)
		return self.sources

	def _search_name(self):
		search_title = clean_file_name(self.info.get("title"))
		db_type = self.info.get("db_type")
		year = self.info.get("year")
		years = '%s,%s,%s' % (str(int(year - 1)), year, str(int(year + 1)))
		season = self.info.get("season")
		episode = self.info.get("episode")
		if db_type == 'movie': search_name = '"%s" %s' % (search_title, years)
		else: search_name = '%s S%02dE%02d' % (search_title,  int(season), int(episode))
		return search_name

	def to_bytes(self, num, unit):
		unit = unit.upper()
		if unit.endswith('B'): unit = unit[:-1]
		units = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']
		try: mult = pow(1024, units.index(unit))
		except: mult = sys.maxint
		return int(float(num) * mult)

