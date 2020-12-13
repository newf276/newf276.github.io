
import urllib

def build_url(query):
    return 'plugin://plugin.video.fen/?' + urllib.urlencode(query)