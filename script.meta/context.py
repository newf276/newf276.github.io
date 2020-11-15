import xbmc

def get_url(stream_file):
    return None

def main():
    stream_file = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    url = get_url(stream_file)
    if url is None:
        if xbmc.getInfoLabel('ListItem.Episode'): url = 'plugin://script.meta/tv/play_by_name/%s/%s/%s/en' % (xbmc.getInfoLabel('ListItem.TVShowTitle'), xbmc.getInfoLabel('ListItem.Season'), xbmc.getInfoLabel('ListItem.Episode'))
        elif xbmc.getInfoLabel('ListItem.IMDBNumber'): url = 'plugin://script.meta/movies/play/imdb/%s' % xbmc.getInfoLabel('ListItem.IMDBNumber')
        elif xbmc.getInfoLabel('ListItem.Title'): url = 'plugin://script.meta/movies/play_by_name/%s/en' % xbmc.getInfoLabel('ListItem.Title')
        else: url = 'plugin://script.meta/movies/play_by_name/%s/en' % xbmc.getInfoLabel('ListItem.Label')
        xbmc.executebuiltin('RunPlugin(%s)' % url)
    else: xbmc.executebuiltin('PlayMedia(%s)' % url)
    
if __name__ == '__main__': main()