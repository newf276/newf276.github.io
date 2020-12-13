import xbmc, xbmcgui
import os, sys
import time
from threading import Thread
from caches.debrid_cache import DebridCache
from apis.real_debrid_api import RealDebridAPI
from apis.premiumize_api import PremiumizeAPI
from apis.alldebrid_api import AllDebridAPI
from modules.utils import chunks
from modules.utils import local_string as ls
from modules.settings import debrid_enabled as de
from modules.settings import display_sleep_time, debrid_priority
from modules.settings_reader import get_setting
# from modules.utils import logger

monitor = xbmc.Monitor()

rd_api = RealDebridAPI()
pm_api = PremiumizeAPI()
ad_api = AllDebridAPI()

def debrid_enabled():
	enabled_list = []
	if de('rd'): enabled_list.append(('Real-Debrid', debrid_priority('rd')))
	if de('pm'): enabled_list.append(('Premiumize.me', debrid_priority('pm')))
	if de('ad'): enabled_list.append(('AllDebrid', debrid_priority('ad')))
	enabled_list = [i[0] for i in sorted(enabled_list, key=lambda x: x[1])]
	return enabled_list

def debrid_type_enabled(debrid_type, enabled_debrids):
	debrid_list = [('Real-Debrid', 'rd'), ('Premiumize.me', 'pm'), ('AllDebrid', 'ad')]
	debrid_enabled = [i[0] for i in debrid_list if i[0] in enabled_debrids and get_setting('%s.%s.enabled' % (i[1], debrid_type)) == 'true']
	return debrid_enabled

def debrid_valid_hosts(enabled_debrids):
	def _get_hosts(function):
		debrid_hosts.append(function.get_hosts())
	functions = []
	debrid_hosts = []
	threads = []
	if enabled_debrids:
		for i in enabled_debrids:
			if i == 'Real-Debrid': functions.append(rd_api)
			elif i == 'Premiumize.me': functions.append(pm_api)
			else: functions.append(ad_api) # AllDebrid
		for i in functions: threads.append(Thread(target=_get_hosts, args=(i,)))
		[i.start() for i in threads]
		[i.join() for i in threads]
	return debrid_hosts

class DebridCheck:
	def __init__(self):
		self.db_cache = DebridCache()
		self.db_cache.check_database()
		self.timeout = 13.0
		self.sleep_time = display_sleep_time()
		self.cached_hashes = []
		self.main_threads = []
		self.rd_cached_hashes = []
		self.rd_hashes_unchecked = []
		self.rd_query_threads = []
		self.rd_process_results = []
		self.pm_cached_hashes = []
		self.pm_hashes_unchecked = []
		self.pm_process_results = []
		self.ad_cached_hashes = []
		self.ad_hashes_unchecked = []
		self.ad_query_threads = []
		self.ad_process_results = []
		self.starting_debrids = []

	def run(self, hash_list, background, debrid_enabled, progressDialog):
		xbmc.sleep(100)
		self.hash_list = hash_list
		self._query_local_cache(self.hash_list)
		if 'AllDebrid' in debrid_enabled:
			self.ad_cached_hashes = [str(i[0]) for i in self.cached_hashes if str(i[1]) == 'ad' and str(i[2]) == 'True']
			self.ad_hashes_unchecked = [i for i in self.hash_list if not any([h for h in self.cached_hashes if str(h[0]) == i and str(h[1]) =='ad'])]
			if self.ad_hashes_unchecked: self.starting_debrids.append(('AllDebrid', self.AD_cache_checker))
		if 'Premiumize.me' in debrid_enabled:
			self.pm_cached_hashes = [str(i[0]) for i in self.cached_hashes if str(i[1]) == 'pm' and str(i[2]) == 'True']
			self.pm_hashes_unchecked = [i for i in self.hash_list if not any([h for h in self.cached_hashes if str(h[0]) == i and str(h[1]) =='pm'])]
			if self.pm_hashes_unchecked: self.starting_debrids.append(('Premiumize.me', self.PM_cache_checker))
		if 'Real-Debrid' in debrid_enabled:
			self.rd_cached_hashes = [str(i[0]) for i in self.cached_hashes if str(i[1]) == 'rd' and str(i[2]) == 'True']
			self.rd_hashes_unchecked = [i for i in self.hash_list if not any([h for h in self.cached_hashes if str(h[0]) == i and str(h[1]) =='rd'])]
			if self.rd_hashes_unchecked: self.starting_debrids.append(('Real-Debrid', self.RD_cache_checker))
		if self.starting_debrids:
			for i in range(len(self.starting_debrids)):
				self.main_threads.append(Thread(target=self.starting_debrids[i][1], name=self.starting_debrids[i][0]))
			[i.start() for i in self.main_threads]
			if background: [i.join() for i in self.main_threads]
			else: self.debrid_check_dialog(progressDialog)
		try: progressDialog.close()
		except Exception: pass
		del progressDialog
		xbmc.sleep(100)
		return {'rd_cached_hashes': self.rd_cached_hashes, 'pm_cached_hashes': self.pm_cached_hashes, 'ad_cached_hashes': self.ad_cached_hashes}

	def debrid_check_dialog(self, progressDialog):
		if not progressDialog:
			xbmc.sleep(200)
			progressDialog = xbmcgui.DialogProgress()
			progressDialog.create('Fen', ls(32577), '..', '..')
		start_time = time.time()
		end_time = start_time + self.timeout
		plswait_str, checking_debrid, remaining_debrid = ls(32577), ls(32578), ls(32579)
		while not progressDialog.iscanceled():
			try:
				if monitor.abortRequested() is True: return sys.exit()
				remaining_debrids = [x.getName() for x in self.main_threads if x.is_alive() is True]
				current_time = time.time()
				current_progress = current_time - start_time
				try:
					line3 = remaining_debrid % ', '.join(remaining_debrids).upper()
					percent = int((current_progress/float(self.timeout))*100)
					progressDialog.update(percent, plswait_str, checking_debrid, line3)
				except: pass
				time.sleep(self.sleep_time)
				if len(remaining_debrids) == 0: break
				if current_time > end_time: break
			except Exception: pass
		xbmc.sleep(200)

	def RD_cache_checker(self):
		hash_chunk_list = list(chunks(self.rd_hashes_unchecked, 100))
		for item in hash_chunk_list: self.rd_query_threads.append(Thread(target=self._rd_lookup, args=(item,)))
		[i.start() for i in self.rd_query_threads]
		[i.join() for i in self.rd_query_threads]
		self._add_to_local_cache(self.rd_process_results, 'rd')

	def PM_cache_checker(self):
		hashes = self.pm_hashes_unchecked
		self._pm_lookup(hashes)
		self._add_to_local_cache(self.pm_process_results, 'pm')

	def AD_cache_checker(self):
		hashes = self.ad_hashes_unchecked
		self._ad_lookup(hashes)
		self._add_to_local_cache(self.ad_process_results, 'ad')

	def _rd_lookup(self, hash_list):
		rd_cache = rd_api.check_cache(hash_list)
		if not rd_cache: return
		try:
			if isinstance(rd_cache, dict):
				for h in hash_list:
					cached = 'False'
					if h in rd_cache:
						info = rd_cache[h]
						if isinstance(info, dict) and len(info.get('rd')) > 0:
							self.rd_cached_hashes.append(h)
							cached = 'True'
					self.rd_process_results.append((h, cached))
			else:
				for i in hash_list: self.rd_process_results.append((i, 'False'))
		except: pass

	def _pm_lookup(self, hash_list):
		pm_cache = pm_api.check_cache(hash_list)
		if not pm_cache: return
		try:
			pm_cache = pm_cache['response']
			if isinstance(pm_cache, list):
				for c, h in enumerate(hash_list):
					cached = 'False'
					if pm_cache[c] is True:
						self.pm_cached_hashes.append(h)
						cached = 'True'
					self.pm_process_results.append((h, cached))
			else:
				for i in hash_list: self.pm_process_results.append((i, 'False'))
		except: pass

	def _ad_lookup(self, hash_list):
		ad_cache = ad_api.check_cache(hash_list)
		if not ad_cache: return
		try:
			ad_cache = ad_cache['magnets']
			if isinstance(ad_cache, list):
				for i in ad_cache:
					try:
						cached = 'False'
						if i['instant'] == True:
							self.ad_cached_hashes.append(i['hash'])
							cached = 'True'
						self.ad_process_results.append((i['hash'], cached))
					except: pass
			else:
				for i in hash_list: self.ad_process_results.append((i, 'False'))
		except: pass

	def _query_local_cache(self, _hash):
		cached = self.db_cache.get_many(_hash)
		if cached:
			self.cached_hashes = cached

	def _add_to_local_cache(self, _hash, debrid):
		self.db_cache.set_many(_hash, debrid)







