# -*- coding: utf-8 -*-
import xbmc, xbmcgui
# from modules.utils import logger

class BaseDialog(xbmcgui.WindowXMLDialog):
	def __init__(self, xml_file, location):
		xbmcgui.WindowXMLDialog.__init__(self, xml_file, location)
		self.closing_actions = [9, 10, 13, 92]
		self.selection_actions = [7, 100]
		self.context_actions = [101, 117]

	def make_listitem(self):
		return xbmcgui.ListItem()

	def contextmenu(self, items):
		index = xbmcgui.Dialog().contextmenu([i[0] for i in items])
		if index >= 0: action = items[index][1]
		else: action = None
		return action

	def execute_code(self, command):
		return xbmc.executebuiltin(command)
	
	def get_position(self, window_id):
		return self.getControl(window_id).getSelectedPosition()
