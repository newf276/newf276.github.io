# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcvfs
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from threading import Thread
import _strptime  # fix bug in python import
from modules.source_utils import cleanProviderDatabase, checkDatabase
from modules.settings_reader import get_setting, set_setting, make_settings_dict
from modules.nav_utils import get_kodi_version, sync_MyAccounts
from services import listitem_actions
from modules.utils import gen_file_hash, local_string
from modules import settings
# from modules.utils import logger

window = xbmcgui.Window(10000)

monitor = xbmc.Monitor()

_db_types = ['movie', 'tvshow', 'season', 'episode']

class CheckSettingsFile:
	def run(self):
		xbmc.log('[FEN] CheckSettingsFile Service Starting', 2)
		window.clearProperty('fen_settings')
		profile_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/')
		if not xbmcvfs.exists(profile_dir):
			xbmcvfs.mkdirs(profile_dir)
		settings_xml = os.path.join(profile_dir, 'settings.xml')
		if not xbmcvfs.exists(settings_xml):
			__addon__ = settings.addon()
			addon_version = __addon__.getAddonInfo('version')
			__addon__.setSetting('version_number', addon_version)
			monitor.waitForAbort(0.5)
		make_settings_dict()
		return xbmc.log('[FEN] CheckSettingsFile Service Finished', 2)

class SyncMyAccounts:
	def run(self):
		xbmc.log('[FEN] SyncMyAccounts Service Starting', 2)
		sync_MyAccounts(silent=True)
		return xbmc.log('[FEN] SyncMyAccounts Service Finished', 2)

class ReuseLanguageInvokerCheck:
	def run(self):
		xbmc.log('[FEN] ReuseLanguageInvokerCheck Service Starting', 2)
		if get_kodi_version() < 18: return
		xbmc.sleep(2000)
		addon_dir = xbmc.translatePath('special://home/addons/plugin.video.fen')
		addon_xml = os.path.join(addon_dir, 'addon.xml')
		tree = ET.parse(addon_xml)
		root = tree.getroot()
		current_addon_setting = get_setting('reuse_language_invoker', 'true')
		try: current_xml_setting = [str(i.text) for i in root.iter('reuselanguageinvoker')][0]
		except: return xbmc.log('[FEN] ReuseLanguageInvokerCheck Service Finished', 2)
		if current_xml_setting == current_addon_setting:
			return xbmc.log('[FEN] ReuseLanguageInvokerCheck Service Finished', 2)
		xbmcgui.Dialog().ok('Fen', '%s\n%s' % (local_string(33021), local_string(33020)))
		for item in root.iter('reuselanguageinvoker'):
			item.text = current_addon_setting
			hash_start = gen_file_hash(addon_xml)
			tree.write(addon_xml)
			hash_end = gen_file_hash(addon_xml)
			xbmc.log('[FEN] ReuseLanguageInvokerCheck Service Finished', 2)
			if hash_start != hash_end:
				current_profile = xbmc.getInfoLabel('system.profilename')
				xbmc.executebuiltin('LoadProfile(%s)' % current_profile)
			else: xbmcgui.Dialog().ok('Fen', local_string(32574))

class AutoRun:
	def run(self):
		try:
			xbmc.log('[FEN] AutoRun Service Starting', 2)
			if settings.auto_start_fen(): xbmc.executebuiltin('RunAddon(plugin.video.fen)')
			xbmc.log('[FEN] AutoRun Service Finished', 2)
			return
		except: return

class ClearSubs:
	def run(self):
		xbmc.log('[FEN] Clear Subtitles Service Starting', 2)
		if get_setting('subtitles.clear_on_start') == 'true':
			subtitle_path = xbmc.translatePath('special://temp/')
			files = xbmcvfs.listdir(subtitle_path)[1]
			for i in files:
				try:
					if i.startswith('FENSubs_'): xbmcvfs.delete(os.path.join(subtitle_path, i))
				except: pass
		xbmc.log('[FEN] Clear Subtitles Service Finished', 2)

class ClearTraktServices:
	def run(self):
		xbmc.log('[FEN] Trakt Service Starting', 2)
		if settings.refresh_trakt_on_startup():
			try:
				from caches.trakt_cache import clear_cache_on_startup
				clear_cache_on_startup()
			except: pass
		if settings.sync_fen_watchstatus():
			try:
				from apis.trakt_api import sync_watched_trakt_to_fen
				sync_watched_trakt_to_fen(dialog=False)
			except: pass
		xbmc.log('[FEN] Trakt Service Finished', 2)

class CleanExternalSourcesDatabase:
	def run(self):
		xbmc.log('[FEN] Clean External Sources Service Starting', 2)
		checkDatabase()
		cleanProviderDatabase()
		xbmc.log('[FEN] Clean External Sources Service Finished', 2)

class AutoScrollMonitor:
	def run(self):
		xbmc.log('[FEN] Auto Scroll Monitor Service starting', 2)
		while not monitor.abortRequested():
			try:
				if get_setting('autoscroll.page') == 'true':
					try: listitem_actions.autoscoll_page()
					except: pass
			except: pass
			monitor.waitForAbort()
		xbmc.log('[FEN] Auto Scroll Monitor Service Finished', 2)

class ListItemNotifications():
	def run(self):
		xbmc.log('[FEN] Listitem Monitor Service Starting', 2)
		previous_label, current_label, highlight_time = '', '', 0
		while not monitor.abortRequested():
			if get_setting('notification.enabled', 'false') == 'true':
				try:
					threads = []
					settings.list_actions_global()
					previous_label, highlight_time, activate_function, current_dbtype, current_label = self.getInfo(previous_label, highlight_time)
					if activate_function:
						if get_setting('notification.nextep') == 'true' and current_dbtype == 'tvshow':
							threads.append(Thread(target=listitem_actions.nextep_notification, args=(0,)))
						if get_setting('notification.watched_status') == 'true' and current_dbtype in ('tvshow', 'season'):
							threads.append(Thread(target=listitem_actions.watched_status_notification, args=(current_dbtype,1)))
						if get_setting('notification.progress') == 'true':
							threads.append(Thread(target=listitem_actions.progress_notification, args=(current_dbtype,2)))
						if get_setting('notification.duration_finish') == 'true' and current_dbtype in ('movie', 'episode'):
							threads.append(Thread(target=listitem_actions.duration_finish_notification, args=(current_dbtype, 3)))
						if get_setting('notification.last_aired') == 'true' and current_dbtype == 'tvshow':
							threads.append(Thread(target=listitem_actions.last_aired_notification, args=(4,)))
						if get_setting('notification.next_aired') == 'true' and current_dbtype == 'tvshow':
							threads.append(Thread(target=listitem_actions.next_aired_notification, args=(5,)))
						if get_setting('notification.production_status') == 'true' and current_dbtype in ('movie', 'tvshow'):
							threads.append(Thread(target=listitem_actions.production_status_notification, args=(6,)))
						if get_setting('notification.budget_revenue') == 'true' and current_dbtype == 'movie':
							threads.append(Thread(target=listitem_actions.budget_revenue_notification, args=(7,)))
						[i.start() for i in threads]
						[i.join() for i in threads]
				except: pass
				try: self.processNotifications(current_dbtype, current_label)
				except: pass
				monitor.waitForAbort(0.1)
			else:
				monitor.waitForAbort(5.0)
		xbmc.log('[FEN] Listitem Monitor Service Finished', 2)
		return

	def getInfo(self, previous_label, highlight_time):
		activate_function = False
		in_fen = xbmc.getInfoLabel('Container.PluginName') == 'plugin.video.fen'
		widget = xbmc.getInfoLabel('ListItem.Property(fen_widget)') == 'true'
		current_dbtype = xbmc.getInfoLabel('ListItem.dbtype')
		current_label = xbmc.getInfoLabel('ListItem.label')
		proceed = (in_fen or widget) and current_dbtype in _db_types
		if proceed:
			if current_label != previous_label:
				highlight_time = time.time()
			pause = time.time() - highlight_time
			previous_label = current_label
			try: delay = float(int(get_setting('notification.delay')))/1000
			except: delay = float(2000)/1000
			if highlight_time and pause >= delay:
				activate_function = True
				highlight_time = 0
		else: previous_label = ''
		return previous_label, highlight_time, activate_function, current_dbtype, current_label

	def processNotifications(self, current_dbtype, current_label):
		try: duration = int(get_setting('notification.duration'))
		except: duration = 2500
		wait = float(duration)/1000
		notifications = sorted([i for i in settings.list_actions if i is not None], key=lambda x: x[3])
		length = len(notifications)
		for count, item in enumerate(notifications, 1):
			try:
				if self.visibilityCheck(current_dbtype, current_label):
					xbmcgui.Dialog().notification(item[0], item[1], item[2], duration, False)
					if not count == length: monitor.waitForAbort(wait)
				else: break
			except: pass

	def visibilityCheck(self, current_dbtype, current_label):
		if not xbmc.getInfoLabel('ListItem.dbtype') == current_dbtype: return False
		if not xbmc.getInfoLabel('ListItem.label') == current_label: return False
		if xbmc.getCondVisibility('Window.IsVisible(busydialog)'): return False
		if xbmc.getCondVisibility('Window.IsVisible(movieinformation)'): return False
		if xbmc.getCondVisibility('Window.IsVisible(progressdialog)'): return False
		if xbmc.getCondVisibility('Window.IsVisible(contextmenu)'): return False
		if monitor.abortRequested(): return False
		return True

class SubscriptionsUpdater:
	def run(self):
		xbmc.log('[FEN] Subscription Service Starting', 2)
		hours = settings.subscription_timer()
		while not monitor.abortRequested():
			if settings.subscription_update():
				try:
					next_run  = datetime.fromtimestamp(time.mktime(time.strptime(get_setting('service_time'), "%Y-%m-%d %H:%M:%S")))
					now = datetime.now()
					if now > next_run:
						if xbmc.Player().isPlaying() == False:
							if xbmc.getCondVisibility('Library.IsScanningVideo') == False:
								monitor.waitForAbort(3)
								xbmc.log('[FEN] Updating Video Subscriptions', 2)
								if settings.trakt_list_subscriptions():
									from modules.subscriptions import subscriptions_update_list
									subscriptions_update_list()
								else:
									from modules.subscriptions import Subscriptions
									Subscriptions().update_subscriptions()
								monitor.waitForAbort(0.5)
								if get_setting('subsciptions.update_type') == '1':
									next_update = datetime.now() + timedelta(hours=24)
									next_update = next_update.strftime('%Y-%m-%d') + ' %s:00' % get_setting('subscriptions_update_label2')
								else:
									next_update = str(now + timedelta(hours=hours)).split('.')[0]
								set_setting('service_time', next_update)
								monitor.waitForAbort(0.5)
								xbmc.log('[FEN] Subscriptions Updated. Next Run at ' + get_setting('service_time'), 2)
								monitor.waitForAbort(3)
						else:
							xbmc.log('[FEN] Player is Running, Waiting Until Finished', 2)
				except: pass
			monitor.waitForAbort(60)
		xbmc.log('[FEN] Subscription Service Finished', 2)
		return


