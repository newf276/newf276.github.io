import xbmc, xbmcgui, xbmcvfs
import os
from tikimeta.utils import get_kodi_version
from tikimeta.setting_reader import make_settings_dict
# from tikimeta.utils import logger

window = xbmcgui.Window(10000)

monitor = xbmc.Monitor()

class CheckSettingsFile():
	def run(self):
		profile_dir = xbmc.translatePath('special://profile/addon_data/script.module.tikimeta')
		if not xbmcvfs.exists(profile_dir): xbmcvfs.mkdirs(profile_dir)
		settings_xml = os.path.join(profile_dir, 'settings.xml')
		if not xbmcvfs.exists(settings_xml):
			from xbmcaddon import Addon
			xbmc.log("[TIKIMETA] Remaking Settings File...", 2)
			Addon(id='script.module.tikimeta').setSetting('get_fanart_data', 'false')
		make_settings_dict()
		return

class SettingsMonitor(xbmc.Monitor):
	def __init__ (self):
		xbmc.Monitor.__init__(self)
		xbmc.log("[TIKIMETA] Settings Monitor Service Starting...", 2)

	def onSettingsChanged(self):
		window.clearProperty('tikimeta_settings')
		xbmc.sleep(50)
		refreshed = make_settings_dict()

CheckSettingsFile().run()
settings_monitor = SettingsMonitor()
settings_monitor.waitForAbort()
