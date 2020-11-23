#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

import xbmc, xbmcvfs
import re
pluginid = "plugin.video.discover"

def get_url(stream_file):
    if stream_file.endswith(".strm"):
        f = xbmcvfs.File(stream_file)
        try:
            content = f.read()
            if content.startswith("plugin://" + pluginid):
                return content.replace("/library", "/context")
        finally: f.close()
    return None

def main():
    stream_file = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    url = get_url(stream_file)
    #title = "Testing 123"
    #msg = xbmc.getInfoLabel('Container.Content')
    #xbmc.executebuiltin('XBMC.Notification("%s", "%s", "%s", "%s")' % (msg, title, 6000, ''))
    if url is None:
        if xbmc.getCondVisibility('Container.Content(movies)') == True:
            if xbmc.getInfoLabel('ListItem.IMDBNumber'): url = "plugin://{0}/movies/play/imdb/{1}/context".format(pluginid, xbmc.getInfoLabel('ListItem.IMDBNumber'))
            elif xbmc.getInfoLabel('ListItem.Title'): url = "plugin://{0}/movies/play_by_name/{1}/en".format(pluginid, xbmc.getInfoLabel('ListItem.Title'))
            else: url = "plugin://{0}/movies/play_by_name/{1}/en".format(pluginid, xbmc.getInfoLabel('ListItem.Label'))
        elif xbmc.getCondVisibility('Container.Content(tvshows)') == True or xbmc.getCondVisibility('Container.Content(seasons)') == True or xbmc.getCondVisibility('Container.Content(episodes)') == True:
            if xbmc.getInfoLabel('ListItem.TVShowTitle'):
                if xbmc.getCondVisibility('Container.Content(tvshows)'): url = "plugin://{0}/tv/play_by_name_only/{1}/en".format(pluginid, xbmc.getInfoLabel('ListItem.TVShowTitle'))
                elif xbmc.getCondVisibility('Container.Content(seasons)'):
                    if xbmc.getInfoLabel('ListItem.Season') and xbmc.getInfoLabel('ListItem.Episode'): url = "plugin://{0}/tv/play_by_name/{1}/{2}/1/en/context".format(pluginid, xbmc.getInfoLabel('ListItem.TVShowTitle'), xbmc.getInfoLabel('ListItem.Season'), xbmc.getInfoLabel('ListItem.Episode'))
                    else: url = "plugin://{0}/tv/play_by_name_only/{1}/en".format(pluginid, xbmc.getInfoLabel('ListItem.TVShowTitle'))
                elif xbmc.getCondVisibility('Container.Content(episodes)'):
                    if xbmc.getInfoLabel('ListItem.Season') and xbmc.getInfoLabel('ListItem.Episode'): url = "plugin://{0}/tv/play_by_name/{1}/{2}/{3}/en/context".format(pluginid, xbmc.getInfoLabel('ListItem.TVShowTitle'), xbmc.getInfoLabel('ListItem.Season'), xbmc.getInfoLabel('ListItem.Episode'))
                    else: url = "plugin://{0}/tv/play_by_name_only/{1}/en".format(pluginid, xbmc.getInfoLabel('ListItem.TVShowTitle'))
        elif xbmc.getInfoLabel('ListItem.Label'):url = "plugin://{0}/play/{1}".format(pluginid, re.sub(r'\[[^)].*?\]', '', xbmc.getInfoLabel('ListItem.Label')))
        else: 
            url = None
#        if url is None:
#            title = "Discover"
#            msg = "Invalid media file. Try using the MetaQ-Context-Menu addon instead"
#            xbmc.executebuiltin('XBMC.Notification("%s", "%s", "%s", "%s")' % (msg, title, 2000, ''))
            return
        xbmc.executebuiltin("RunPlugin({0})".format(url))
    else:
        xbmc.executebuiltin("PlayMedia({0})".format(url))
    
if __name__ == '__main__':
    main()
