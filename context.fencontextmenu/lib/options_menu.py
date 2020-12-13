# -*- coding: utf-8 -*-

import xbmc
import sys
import json
from utils import build_url

listitem = sys.listitem

xbmc.executebuiltin("RunPlugin(%s)" % build_url(json.loads(listitem.getProperty("fen_options_menu_params"))))
