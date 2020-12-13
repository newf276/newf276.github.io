# -*- coding: utf-8 -*-
from datetime import timedelta
from apis.furk_api import FurkAPI
from modules.source_utils import get_release_quality, get_file_info
from modules.utils import clean_file_name, to_utf8, normalize
from scrapers import internal_results
# from modules.utils import logger

Furk = FurkAPI()

class FurkSource:
	def __init__(self):
		self.scrape_provider = 'furk'
		self.sources = []

	def results(self, info):
		try:
			self.info = info
			search_name = self._search_name()
			files = Furk.search(search_name)
			if not files: return internal_results(self.scrape_provider, self.sources)
			cached_files = [i for i in files if i.get('type') not in ('default', 'audio', '') and i.get('is_ready') == '1']
			def _process():
				for i in cached_files:
					try:
						file_name = normalize(i['name'])
						URLName = clean_file_name(file_name).replace('html', ' ').replace('+', ' ').replace('-', ' ')
						file_id = i['id']
						files_num_video = int(i['files_num_video'])
						size = float(int(i['size']))/1073741824
						package = 'false'
						if self.info.get('db_type') == 'movie':
							files_num_video = 1
						elif files_num_video > 3:
							package = 'true'
							size = float(size)/files_num_video
						file_dl = i['url_dl']
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
										'id': file_id,
										'local': False,
										'direct': True,
										'package': package,
										'source': self.scrape_provider,
										'scrape_provider': self.scrape_provider}
						yield source_item
					except Exception as e:
						from modules.utils import logger
						logger('FURK ERROR - 65', e)
						pass
			self.sources = list(_process())
		except Exception as e:
			from modules.utils import logger
			logger('FEN furk scraper Exception', e)
			pass
		internal_results(self.scrape_provider, self.sources)
		return self.sources

	def _search_name(self):
		search_title = clean_file_name(to_utf8(self.info.get("title")))
		search_title = search_title.replace(' ', '+')
		db_type = self.info.get("db_type")
		if db_type == 'movie':
			year = self.info.get("year")
			years = '%s+|+%s+|+%s' % (str(int(year - 1)), year, str(int(year + 1)))
			search_name = '@name+%s+%s' % (search_title, years)
		else:
			season = self.info.get("season")
			episode = self.info.get("episode")
			queries = self._seas_ep_query_list(season, episode)
			search_name = '@name+%s+@files+%s+|+%s+|+%s+|+%s+|+%s' % (search_title, queries[0], queries[1], queries[2], queries[3], queries[4])
		return search_name

	def _seas_ep_query_list(self, season, episode):
		return ['s%02de%02d' % (int(season), int(episode)),
				'%dx%02d' % (int(season), int(episode)),
				'%02dx%02d' % (int(season), int(episode)),
				'"season %d episode %d"' % (int(season), int(episode)),
				'"season %02d episode %02d"' % (int(season), int(episode))]
