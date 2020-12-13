# -*- coding: utf-8 -*-
from windows.base_dialog import BaseDialog
# from modules.utils import logger

class SlideShow(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(SlideShow, self).__init__(self, args)
		self.window_id = 5000
		self.all_images = kwargs.get('all_images')
		self.index = kwargs.get('index')
		self.slide_items = []

	def onInit(self):
		super(SlideShow, self).onInit()
		self.make_items()
		self.win = self.getControl(self.window_id)
		self.win.addItems(self.slide_items)
		self.win.selectItem(self.index)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		return self.position

	def onAction(self, action):
		if action in self.closing_actions:
			self.position = self.get_position(self.window_id)
			self.close()

	def make_items(self):
		for item in self.all_images:
			listitem = self.make_listitem()
			listitem.setProperty('fen.slideshow.image', item)
			self.slide_items.append(listitem)
