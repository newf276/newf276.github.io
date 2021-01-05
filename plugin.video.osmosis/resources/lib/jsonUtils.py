# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from kodi_six.utils import py2_decode

from .common import jsonrpc
from .utils import addon_log


def requestItem(file, type='video'):
    addon_log('requestItem, file = {0}'.format(file))
    if file.find('playMode=play') == -1:
        return requestList(file, type)

    return jsonrpc('Player.GetItem', dict(playerid=1, properties=['art', 'title', 'year', 'mpaa', 'imdbnumber', 'description', 'season', 'episode', 'playcount', 'genre', 'duration', 'runtime', 'showtitle', 'album', 'artist', 'plot', 'plotoutline', 'tagline', 'tvshowid']))


def requestList(path, type='video'):
    addon_log('requestList, path = {0}'.format(path))
    if path.find('playMode=play') != -1:
        return requestItem(path, type)

    return jsonrpc('Files.GetDirectory', dict(directory=path, media=type, properties=['art', 'title', 'year', 'track', 'mpaa', 'imdbnumber', 'description', 'season', 'episode', 'playcount', 'genre', 'duration', 'runtime', 'showtitle', 'album', 'artist', 'plot', 'plotoutline', 'tagline', 'tvshowid']))
