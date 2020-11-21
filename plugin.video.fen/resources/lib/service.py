# -*- coding: utf-8 -*-
import xbmc, xbmcgui
from threading import Thread
from services import service_functions
from modules.settings_reader import make_settings_dict
# from modules.utils import logger

window = xbmcgui.Window(10000)

monitor = xbmc.Monitor()

class Main(xbmc.Monitor):
	def __init__ (self):
		xbmc.Monitor.__init__(self)
		xbmc.log('[FEN] Main Monitor Service Starting', 2)
		xbmc.log('[FEN] Settings Monitor Service Starting', 2)
		self.startUpServices()
	
	def startUpServices(self):
		threads = []
		functions = [service_functions.ListItemNotifications().run, service_functions.SubscriptionsUpdater().run]
		for item in functions: threads.append(Thread(target=item))
		while not monitor.abortRequested():
			service_functions.CheckSettingsFile().run()
			service_functions.SyncMyAccounts().run()
			service_functions.ReuseLanguageInvokerCheck().run()
			service_functions.AutoRun().run()
			service_functions.ClearSubs().run()
			service_functions.ClearTraktServices().run()
			service_functions.CleanExternalSourcesDatabase().run()
			[i.start() for i in threads]
			break

	def onSettingsChanged(self):
		window.clearProperty('fen_settings')
		xbmc.sleep(50)
		refreshed = make_settings_dict()

Main().waitForAbort()

xbmc.log('[FEN] Settings Monitor Service Finished', 2)
xbmc.log('[FEN] Main Monitor Service Finished', 2)
