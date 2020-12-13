# -*- coding: utf-8 -*-

import xbmc
import sys
from utils import build_url
import json
from urlparse import parse_qsl

listitem = sys.listitem
path = listitem.getPath()
widget_status = listitem.getProperty("fen_widget")

orig_params = dict(parse_qsl(path.replace('plugin://plugin.video.fen/?','')))

meta = json.loads(orig_params['meta'])
media_type = orig_params.get('vid_type', 'tvshow')
params = {"mode": "build_add_to_remove_from_list", "media_type": media_type, "meta": orig_params['meta']}
xbmc.executebuiltin("RunPlugin(%s)" % build_url(params))
