# -*- coding: utf-8 -*-
import requests
import gzip
import time
from datetime import timedelta
try: from StringIO import StringIO
except ImportError: from io import StringIO
try: from urllib import quote
except ImportError: from urllib.parse import quote
from apis import simplejson as json
from caches import fen_cache
from modules.nav_utils import notification
from modules.utils import to_utf8
# from modules.utils import logger

_cache = fen_cache.FenCache()

class OpenSubtitlesAPI:
	def __init__(self):
		self.base_url = 'https://rest.opensubtitles.org/search'
		self.user_agent = 'Fen v1.0'
		self.headers = {'User-Agent': self.user_agent}

	def search(self, query, imdb_id, language, season=None, episode=None):
		cache_name = 'opensubtitles_%s' % imdb_id
		if season: cache_name += '_%s_%s' % (season, episode)
		cache = _cache.get(cache_name)
		if cache:
			response = cache
		else:
			url = '/imdbid-%s/query-%s' % (imdb_id, quote(query))
			if season: url += '/season-%d/episode-%d' % (season, episode)
			url += '/sublanguageid-%s' % language
			url = self.base_url + url
			response = self._get(url, retry=True)
			response = to_utf8(json.loads(response.text))
			_cache.set(cache_name, response,
				expiration=timedelta(hours=24))
		return response

	def download(self, url):
		response = self._get(url, stream=True, retry=True)
		content = gzip.GzipFile(fileobj=StringIO(response.content)).read()
		return content

	def _get(self, url, stream=False, retry=False):
		response = requests.get(url, headers=self.headers, stream=stream)
		if '200' in str(response):
			return response
		elif '429' in str(response) and retry:
			from modules.utils import local_string as ls
			notification(ls(32740), 3500)
			time.sleep(10)
			return self._get(url, stream)
		else: return
