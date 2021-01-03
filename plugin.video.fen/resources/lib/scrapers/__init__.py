# -*- coding: utf-8 -*-
import xbmcgui
from apis import simplejson as json
# from modules.utils import logger

window = xbmcgui.Window(10000)

def internal_results(provider, sources):
	window.setProperty('%s.internal_results' % provider, json.dumps(sources))

