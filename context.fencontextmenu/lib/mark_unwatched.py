# -*- coding: utf-8 -*-

import xbmc
import sys
from utils import build_url
import json
from urlparse import parse_qsl

listitem = sys.listitem
path = listitem.getPath()

orig_params = dict(parse_qsl(path.replace('plugin://plugin.video.fen/?','')))

meta = json.loads(orig_params['meta'])
if orig_params['vid_type'] == 'movie':
    params = {"mode": "mark_movie_as_watched_unwatched", "action": 'mark_as_unwatched',
    "media_id": meta['tmdb_id'], "title": meta['title'], "year": meta['year']}
else:
    params = {"mode": "mark_episode_as_watched_unwatched", "action": 'mark_as_unwatched',
    "season": meta['season'], "episode": meta['episode'], "media_id": meta['tmdb_id'],
    "imdb_id": meta['imdb_id'], "title": meta['title'], "year": meta['year']}
xbmc.executebuiltin("RunPlugin(%s)" % build_url(params))
xbmc.executebuiltin('UpdateLibrary(video,special://skin/foo)')
