# -*- coding: utf-8 -*-

import xbmc
import sys
from utils import build_url
from urlparse import parse_qsl

listitem = sys.listitem
path = listitem.getPath()

orig_params = dict(parse_qsl(path.replace('plugin://plugin.video.fen/?','')))

params = {'mode': 'build_season_list', 'meta': orig_params['meta']}
xbmc.executebuiltin("ActivateWindow(Videos,%s)" % build_url(params))