# -*- coding: utf-8 -*-
import requests
import re
import datetime
import base64
try: from urllib import urlencode, quote # Python 2
except ImportError: from urllib.parse import urlencode, quote # Python 3
from apis import simplejson as json
from caches import fen_cache
from modules.utils import to_utf8
from modules.settings_reader import get_setting, set_setting
# from modules.utils import logger

_cache = fen_cache.FenCache()

SORT = {'s1': 'relevance', 's1d': '-', 's2': 'dsize', 's2d': '-', 's3': 'dtime', 's3d': '-'}
SEARCH_PARAMS = {'st': 'adv', 'sb': 1, 'fex': 'mkv, mp4, avi, mpg, wemb', 'fty[]': 'VIDEO', 'spamf': 1, 'u': '1', 'gx': 1, 'pno': 1, 'sS': 3}
SEARCH_PARAMS.update(SORT)

def import_easynews():
	if get_setting('easynews.api_version') == '0':
		return EasyNewsAPI()
	else:
		return EasyNewsAPIv3()

class EasyNewsAPI:
	def __init__(self):
		self.base_url = 'https://members.easynews.com'
		self.search_link = '/2.0/search/solr-search/advanced'
		self.username = get_setting('easynews_user')
		self.password = get_setting('easynews_password')
		self.moderation = 1 if get_setting('easynews_moderation') == 'true' else 0
		self.auth = self._get_auth()
		self.account_link = 'https://account.easynews.com/editinfo.php'
		self.usage_link = 'https://account.easynews.com/usageview.php'
		self.timeout = 40.0
		self.base_get = self._get
		self.base_process = self._process_files
		self.base_resolver = self.resolver

	def _get_auth(self):
		try:
			auth = 'Basic ' + base64.b64encode('%s:%s' % (self.username, self.password))
		except:
			user_info = '%s:%s' % (self.username, self.password)
			user_info = user_info.encode('utf-8')
			auth = 'Basic ' + base64.b64encode(user_info).decode('utf-8')
		return auth

	def search(self, query):
		search_url, params = self._translate_search(query)
		cache_name = 'fen_EASYNEWS_SEARCH_' + urlencode(params)
		cache = _cache.get(cache_name)
		if cache:
			files = cache
		else:
			results = self.base_get(search_url, params)
			files = to_utf8(self.base_process(results))
			_cache.set(cache_name, files,
				expiration=datetime.timedelta(hours=24))
		return files

	def account(self):
		try:
			from bs4 import BeautifulSoup
			account_html = self._get(self.account_link)
			if account_html == None or account_html == '': raise Exception()
			account_html = BeautifulSoup(account_html, "html.parser")
			account_html = account_html.find_all('form', id='accountForm')[0]
			account_html = account_html.find_all('table', recursive=False)[0]
			account_html = account_html.find_all('tr', recursive=False)
			usage_html = self._get(self.usage_link)
			if usage_html == None or usage_html == '': raise Exception()
			usage_html = BeautifulSoup(usage_html, "html.parser")
			usage_html = usage_html.find_all('div', class_='table-responsive')[0]
			usage_html = usage_html.find_all('table', recursive=False)[0]
			usage_html = usage_html.find_all('tr', recursive=False)
			return account_html, usage_html
		except Exception:
			pass

	def _process_files(self, files):
		def _process():
			for item in files:
				try:
					post_hash, size, post_title, ext, duration = item['0'], item['4'], item['10'], item['11'], item['14']
					checks = [False] * 5
					if 'alangs' in item and item['alangs'] and 'eng' not in item['alangs']: checks[1] = True
					if re.match('^\d+s', duration) or re.match('^[0-5]m', duration): checks[2] = True
					if 'passwd' in item and item['passwd']: checks[3] = True
					if 'virus' in item and item['virus']: checks[4] = True
					if 'type' in item and item['type'].upper() != 'VIDEO': checks[5] = True
					if any(checks):
						continue
					stream_url = down_url + quote('/%s/%s/%s%s/%s%s' % (dl_farm, dl_port, post_hash, ext, post_title, ext))
					file_name = post_title
					file_dl = stream_url + '|Authorization=%s' % (quote(self.auth))
					result = {'name': file_name,
							  'size': size,
							  'rawSize': item['rawSize'],
							  'url_dl': file_dl,
							  'version': 'version2',
							  'full_item': item}
					yield result
				except: pass
		down_url = files.get('downURL')
		dl_farm = files.get('dlFarm')
		dl_port = files.get('dlPort')
		files = files.get('data', [])
		results = list(_process())
		return results

	def _process_files_v3(self, results):
		def _process():
			for item in files:
				try:
					post_hash, size, post_title, ext, duration, sig = item['hash'], item['bytes'], item['filename'], item['extension'], item['runtime'], item['sig']
					checks = [False] * 5
					if 'alang' in item and item['alang'] and 'eng' not in item['alang']: checks[1] = True
					if re.match('^\d+s', duration) or re.match('^[0-5]m', duration): checks[2] = True
					if 'passwd' in item and item['passwd']: checks[3] = True
					if 'virus' in item and item['virus']: checks[4] = True
					if 'type' in item and item['type'].upper() != 'VIDEO': checks[5] = True
					if any(checks):
						continue
					url_dl = self.stream_url % (post_hash, ext, post_title, sid, sig)
					result = {'name': post_title,
							  'size': size,
							  'rawSize': size,
							  'url_dl': url_dl,
							  'version': 'version3',
							  'full_item': item}
					yield result
				except: pass
		files = results.get('data', [])
		sid = results.get('sid')
		results = list(_process())
		return results

	def _translate_search(self, query):
		params = SEARCH_PARAMS
		params['pby'] = 100
		params['safeO'] = self.moderation
		params['gps'] = params['sbj'] = query
		url = self.base_url + self.search_link
		return url, params

	def _get(self, url, params={}):
		headers = {'Authorization': self.auth}
		response = requests.get(url, params=params, headers=headers, timeout=self.timeout).text
		try: return to_utf8(json.loads(response))
		except: return to_utf8(response)

	def _get_v3(self, url, params={}):
		headers = {'Authorization': self.auth}
		response = requests.get(url, params=params, headers=headers, timeout=self.timeout).content
		response = re.compile(self.regex,re.DOTALL).findall(response)[0]
		response = response + '}'
		try: return to_utf8(json.loads(response))
		except: return to_utf8(response)

	def resolve_easynews(self, url_dl):
		return self.base_resolver(url_dl)

	def resolver(self, url_dl):
		return url_dl

	def resolver_v3(self, url_dl):
		headers = {'Authorization': self.auth}
		response = requests.get(url_dl, headers=headers, stream=True, timeout=40.0)
		stream_url = response.url
		resolved_link = stream_url + '|Authorization=%s' % (quote(self.auth))
		return resolved_link

class EasyNewsAPIv3(EasyNewsAPI):
	def __init__(self):
		EasyNewsAPI.__init__(self)
		self.base_url = 'https://members-beta.easynews.com/3.0/index/basic'
		self.stream_url = 'https://members-beta.easynews.com/os/3.0/auto/443/%s%s/%s?sid=%s&sig=%s'
		self.search_link = ''
		self.regex='var INIT_RES = (.+?)};'
		self.base_get = self._get_v3
		self.base_process = self._process_files_v3
		self.base_resolver = self.resolver_v3

def clear_media_results_database():
	import xbmc, xbmcgui
	import os
	try: from sqlite3 import dbapi2 as database
	except ImportError: from pysqlite2 import dbapi2 as database
	window = xbmcgui.Window(10000)
	EASYNEWS_DATABASE = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/fen_cache2.db')
	dbcon = database.connect(EASYNEWS_DATABASE)
	dbcur = dbcon.cursor()
	dbcur.execute("SELECT id FROM fencache WHERE id LIKE 'fen_EASYNEWS_SEARCH_%'")
	easynews_results = [str(i[0]) for i in dbcur.fetchall()]
	if not easynews_results: return 'success'
	try:
		dbcur.execute("DELETE FROM fencache WHERE id LIKE 'fen_EASYNEWS_SEARCH_%'")
		dbcon.commit()
		for i in easynews_results: window.clearProperty(i)
		return 'success'
	except: return 'failed'

