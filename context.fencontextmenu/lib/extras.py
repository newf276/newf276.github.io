# -*- coding: utf-8 -*-

import xbmc
import sys
import json
from utils import build_url

listitem = sys.listitem

extras_menu_params = json.loads(listitem.getProperty("fen_extras_menu_params"))

xbmc.executebuiltin("ActivateWindow(Videos,%s,return)" % build_url(extras_menu_params))
