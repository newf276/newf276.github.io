# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import requests
import time
import re
from sys import exit as sysexit
from apis import simplejson as json
from caches.fen_cache import cache_object
from modules.utils import local_string as ls
from modules.settings_reader import get_setting, set_setting
# from modules.utils import logger

progressDialog = xbmcgui.DialogProgress()
dialog = xbmcgui.Dialog()

monitor = xbmc.Monitor()

class AllDebridAPI:
	def __init__(self):
		self.user_agent = 'fen_for_kodi'
		self.base_url = 'https://api.alldebrid.com/v4/'
		self.token = get_setting('ad.token')
		self.timeout = 13.0
		self.break_auth_loop = False

	def auth_loop(self):
		time.sleep(5)
		response = requests.get(self.check_url, timeout=self.timeout).json()
		response = response['data']
		if 'error' in response:
			self.token = 'failed'
			return xbmcgui.Dialog().ok('Fen', ls(32574))
		if response['activated']:
			try:
				progressDialog.close()
				self.token = str(response['apikey'])
				set_setting('ad.token', self.token)
			except:
				self.token = 'failed'
				self.break_auth_loop = True
				return xbmcgui.Dialog().ok('Fen', ls(32574))
		return

	def auth(self):
		self.token = ''
		url = self.base_url + 'pin/get?agent=%s' % self.user_agent
		response = requests.get(url, timeout=self.timeout).json()
		response = response['data']
		progressDialog.create('Fen', '')
		progressDialog.update(-1, ls(32517), ls(32700) % response.get('base_url'), ls(32701) % response.get('pin'))
		self.check_url = response.get('check_url')
		time.sleep(2)
		while not self.token:
			if self.break_auth_loop:
				break
			if progressDialog.iscanceled():
				progressDialog.close()
				break
			self.auth_loop()
		if self.token in (None, '', 'failed'): return
		time.sleep(2)
		account_info = self._get('user')
		set_setting('ad.account_id', str(account_info['user']['username']))
		xbmcgui.Dialog().ok('Fen', ls(32576))

	def account_info(self):
		response = self._get('user')
		return response

	def check_cache(self, hashes):
		data = {'magnets[]': hashes}
		response = self._post('magnet/instant', data)
		return response

	def check_single_magnet(self, hash_string):
		cache_info = self.check_cache(hash_string)['magnets'][0]
		return cache_info['instant']

	def user_cloud(self):
		url = 'magnet/status'
		string = "fen_ad_user_cloud"
		return cache_object(self._get, string, url, False, 2)

	def unrestrict_link(self, link):
		url = 'link/unlock'
		url_append = '&link=%s' % link
		response = self._get(url, url_append)
		try: return response['link']
		except: return None

	def create_transfer(self, magnet):
		url = 'magnet/upload'
		url_append = '&magnet=%s' % magnet
		result = self._get(url, url_append)
		result = result['magnets'][0]
		return result.get('id', "")

	def list_transfer(self, transfer_id):
		url = 'magnet/status'
		url_append = '&id=%s' % transfer_id
		result = self._get(url, url_append)
		result = result['magnets']
		return result

	def delete_transfer(self, transfer_id):
		url = 'magnet/delete'
		url_append = '&id=%s' % transfer_id
		result = self._get(url, url_append)
		if result.get('success', False):
			return True

	def resolve_magnet(self, magnet_url, info_hash, store_to_cloud, season, episode, ep_title):
		from modules.source_utils import supported_video_extensions, seas_ep_filter, episode_extras_filter
		try:
			file_url = None
			correct_files = []
			extensions = supported_video_extensions()
			extras_filtering_list = episode_extras_filter()
			transfer_id = self.create_transfer(magnet_url)
			transfer_info = self.list_transfer(transfer_id)
			valid_results = [i for i in transfer_info.get('links') if any(i.get('filename').lower().endswith(x) for x in extensions) and not i.get('link', '') == '']
			if len(valid_results) == 0: return
			if season:
				for item in valid_results:
					if seas_ep_filter(season, episode, item['filename']):
						correct_files.append(item)
					if len(correct_files) == 0: continue
					episode_title = re.sub('[^A-Za-z0-9-]+', '.', ep_title.replace('\'', '')).lower()
					for i in correct_files:
						compare_link = seas_ep_filter(season, episode, i['filename'], split=True)
						compare_link = re.sub(episode_title, '', compare_link)
						if not any(x in compare_link for x in extras_filtering_list):
							media_id = i['link']
							break
			else:
				media_id = max(valid_results, key=lambda x: x.get('size')).get('link', None)			
			if not store_to_cloud: self.delete_transfer(transfer_id)
			file_url = self.unrestrict_link(media_id)
			return file_url
		except Exception:
			if transfer_id: self.delete_transfer(transfer_id)
			return None
	
	def display_magnet_pack(self, magnet_url, info_hash):
		from modules.source_utils import supported_video_extensions, seas_ep_filter, episode_extras_filter
		try:
			extensions = supported_video_extensions()
			transfer_id = self.create_transfer(magnet_url)
			transfer_info = self.list_transfer(transfer_id)
			end_results = []
			for item in transfer_info.get('links'):
				if any(item.get('filename').lower().endswith(x) for x in extensions) and not item.get('link', '') == '':
					end_results.append({'link': item['link'], 'filename': item['filename'], 'size': item['size']})
			self.delete_transfer(transfer_id)
			return end_results
		except Exception:
			if transfer_id: self.delete_transfer(transfer_id)
			return None

	def add_uncached_torrent(self, magnet_url, pack=False):
		import xbmc
		from modules.nav_utils import show_busy_dialog, hide_busy_dialog
		def _return_failed(message=ls(32574), cancelled=False):
			try:
				progressDialog.close()
			except Exception:
				pass
			hide_busy_dialog()
			xbmc.sleep(500)
			if cancelled:
				if not dialog.yesno('Fen', ls(32044)):
					self.delete_transfer(transfer_id)
				else:
					xbmcgui.Dialog().ok(ls(32733), message)
			else:
				xbmcgui.Dialog().ok(ls(32733), message)
			return False
		show_busy_dialog()
		transfer_id = self.create_transfer(magnet_url)
		if not transfer_id: return _return_failed()
		transfer_info = self.list_transfer(transfer_id)
		if not transfer_info: return _return_failed()
		if pack:
			self.clear_cache()
			hide_busy_dialog()
			xbmcgui.Dialog().ok('Fen', ls(32732) % ls(32063))
			return True
		interval = 5
		line1 = '%s...' % (ls(32732) % ls(32063))
		line2 = transfer_info['filename']
		line3 = transfer_info['status']
		progressDialog.create(ls(32733), line1, line2, line3)
		while not transfer_info['statusCode'] == 4:
			xbmc.sleep(1000 * interval)
			transfer_info = self.list_transfer(transfer_id)
			file_size = transfer_info['size']
			line2 = transfer_info['filename']
			if transfer_info['statusCode'] == 1:
				download_speed = round(float(transfer_info['downloadSpeed']) / (1000**2), 2)
				progress = int(float(transfer_info['downloaded']) / file_size * 100) if file_size > 0 else 0
				line3 = ls(32734) % (download_speed, transfer_info['seeders'], progress, round(float(file_size) / (1000 ** 3), 2))
			elif transfer_info['statusCode'] == 3:
				upload_speed = round(float(transfer_info['uploadSpeed']) / (1000 ** 2), 2)
				progress = int(float(transfer_info['uploaded']) / file_size * 100) if file_size > 0 else 0
				line3 = ls(32735) % (upload_speed, progress, round(float(file_size) / (1000 ** 3), 2))
			else:
				line3 = transfer_info['status']
				progress = 0
			progressDialog.update(progress, line2=line2, line3=line3)
			if monitor.abortRequested() == True: return sysexit()
			try:
				if progressDialog.iscanceled():
					return _return_failed(ls(32736), cancelled=True)
			except Exception:
				pass
			if 5 <= transfer_info['statusCode'] <= 10:
				return _return_failed()
		xbmc.sleep(1000 * interval)
		try:
			progressDialog.close()
		except Exception:
			pass
		hide_busy_dialog()
		return True

	def get_hosts(self):
		string = "fen_ad_valid_hosts"
		url = 'hosts'
		hosts_dict = {'AllDebrid': []}
		hosts = []
		try:
			result = cache_object(self._get, string, url, False, 48)
			result = result['hosts']
			for k, v in result.items():
				try: hosts.extend(v['domains'])
				except: pass
			hosts = list(set(hosts))
			hosts_dict['AllDebrid'] = hosts
		except: pass
		return hosts_dict

	def _get(self, url, url_append=''):
		result = None
		try:
			if self.token == '': return None
			url = self.base_url + url + '?agent=%s&apikey=%s' % (self.user_agent, self.token) + url_append
			result = requests.get(url, timeout=self.timeout).json()
			if result.get('status') == 'success':
				if 'data' in result:
					result = result['data']
		except:
			pass
		return result

	def _post(self, url, data={}):
		result = None
		try:
			if self.token == '': return None
			url = self.base_url + url + '?agent=%s&apikey=%s' % (self.user_agent, self.token)
			result = requests.post(url, data=data, timeout=self.timeout).json()
			if result.get('status') == 'success':
				if 'data' in result:
					result = result['data']
		except: pass
		return result

	def revoke_auth(self):
		set_setting('ad.account_id', '')
		set_setting('ad.token', '')
		xbmcgui.Dialog().ok(ls(32063), '%s %s' % (ls(32059), ls(32576)))

	def clear_cache(self):
		try:
			import xbmc, xbmcvfs
			AD_DATABASE = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/fen_cache2.db')
			if not xbmcvfs.exists(AD_DATABASE): return True
			try: from sqlite3 import dbapi2 as database
			except ImportError: from pysqlite2 import dbapi2 as database
			window = xbmcgui.Window(10000)
			dbcon = database.connect(AD_DATABASE)
			dbcur = dbcon.cursor()
			# USER CLOUD
			dbcur.execute("""DELETE FROM fencache WHERE id=?""", ('fen_ad_user_cloud',))
			window.clearProperty('fen_ad_user_cloud')
			dbcon.commit()
			user_cloud_success = True
			# HOSTERS
			dbcur.execute("""DELETE FROM fencache WHERE id=?""", ("fen_ad_valid_hosts",))
			window.clearProperty("fen_ad_valid_hosts")
			dbcon.commit()
			dbcon.close()
			hoster_links_success = True
		except: return False
		if False in (user_cloud_success, hoster_links_success): return False
		return True
