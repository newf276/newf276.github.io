import xbmc
import json

__msgtemplate = u'service.strmfilemarker: {}'

def __log(msg, level):
    xbmc.log(msg.encode('utf-8', errors='replace'), level)

def fatal(msg):
    __log(__msgtemplate.format(msg), xbmc.LOGFATAL)

def severe(msg):
    __log(__msgtemplate.format(msg), xbmc.LOGSEVERE)

def error(msg):
    __log(__msgtemplate.format(msg), xbmc.LOGERROR)

def warn(msg):
    __log(__msgtemplate.format(msg), xbmc.LOGWARNING)

def notice(msg):
    __log(__msgtemplate.format(msg), xbmc.LOGNOTICE)

def debug(msg):
    __log(__msgtemplate.format(msg), xbmc.LOGDEBUG)

class MarkerService(xbmc.Monitor):
    def __init__(self):
        super(MarkerService, self).__init__()
        self.reset_state()
        
    def reset_state(self):
        self.player = None
        self.completed = -1
        self.currently_playing = None

    def onNotification(self, sender, method, data):
        data = json.loads(unicode(data, 'utf-8', errors='ignore'))

        if sender == 'xbmc':
            if method == 'Player.OnPlay':
                if 'item' in data and 'title' in data['item']:
                    self.on_start(data['item']['title'], data['item']['type'] if type in data['item'] else None, data['item']['year'] if 'year' in data['item'] else None)
                else:
                    warn(u'Playback started, but there\'s no way of knowing what it is :( - {}'.format(data))
            elif method == 'Player.OnStop':
                self.on_stop(data['end'])
    
    def on_start(self, title, indicated_type, year=None):
        debug(u'Started playback of {} (probably of type {})'.format(title, indicated_type))
        
        self.player = xbmc.Player()
        
        #wait for player
        xbmc.sleep(1000)

        if self.player.isPlaying() and indicated_type in ['movie', 'episode', '', None]:
            self.currently_playing = self.find_playing_item_info(title, year)
            
            if self.currently_playing:
                if self.currently_playing['file'].lower().endswith('.strm'):
                    notice(u'Tracking playback of {} {} with id {}'.format(self.currently_playing['type'], self.currently_playing['title'], self.currently_playing['id']))
                else:
                    debug(u'Currently playing {} is not associated with a .strm file - will not track'.format(self.currently_playing['type']))
            else:
                notice(u'Could not find library item for current playback of {} - will not track'.format(title))
        else:
            debug(u'Not tracking playback of items with type {}'.format(indicated_type))

    def on_stop(self, ended):
        if self.currently_playing:
            if ended or self.completed >= 0.9:
                rpc_res = self.mark_as_watched(self.currently_playing)
                debug(rpc_res)
            else:
                notice(u'Playback of {} with id {} stopped, but not marking as watched due to insufficient progress ({}%)'.format(self.currently_playing['title'], self.currently_playing['id'], self.completed * 100))
        else:
            debug(u'Playback stopped, but item is not being tracked')
        
        self.reset_state()

    def mark_as_watched(self, info):
        notice(u'Marking {} {} with id {} as watched'.format(info['type'], info['title'], info['id']))
        
        method = 'VideoLibrary.Set{}Details'.format(info['type'].capitalize())
        params = {'{}id'.format(info['type']) : info['id'], 'playcount': info['playcount'] + 1}
        
        return self.json_rpc(method, additional_params=params)

    def find_playing_item_info(self, title, year=None):
        if year:
            return self.find_movie_info(title, year) or self.find_episode_info(title)
        else:
            return self.find_episode_info(title) or self.find_movie_info(title, year)
    
    def find_episode_info(self, title):
        resp = self.json_rpc('VideoLibrary.GetEpisodes', properties=['file','playcount','showtitle','season','episode'])

        if 'result' in resp and 'episodes' in resp['result']:
            for episode in resp['result']['episodes']:
                episode_numbering = u'S%02dE%02d' % (episode['season'], episode['episode'])
                if ((episode['showtitle'] in title and episode_numbering in title)
                    or episode['label'] in title
                    or title in episode['label']):
                    return {
                        'title': u'{} {} ({})'.format(episode['showtitle'], episode_numbering, episode['label']),
                        'id': episode['episodeid'],
                        'file': episode['file'],
                        'playcount': episode['playcount'],
                        'type': 'episode'
                    }
        else:
            return None
    
    def find_movie_info(self, title, year=None):
        resp = self.json_rpc('VideoLibrary.GetMovies', properties=['file','playcount'], filters={ 'year': year } if year else None)

        if 'result' in resp and 'movies' in resp['result']:
            for movie in resp['result']['movies']:
                if movie['label'] == title:
                    return {
                        'title': movie['label'],
                        'id': movie['movieid'],
                        'file': movie['file'],
                        'playcount': movie['playcount'],
                        'type': 'movie'
                    }
        else:
            return None
    
    def json_rpc(self, method, properties=None, filters=None, additional_params=None):
        req = {'jsonrpc': '2.0', 'method': method, 'id': 1, 'params': additional_params or {}}

        if properties:
            req['params']['properties'] = properties
        if filters:
            req['params']['filter'] = filters

        return json.loads(unicode(xbmc.executeJSONRPC(json.dumps(req)), 'utf-8', errors='ignore'))
    
    def run(self):
        notice('Started')
        while not self.abortRequested():
            if self.waitForAbort(1):
                notice(u'Abort requested - shutting down service')
                break
            
            if self.player and self.player.isPlayingVideo() and self.currently_playing:
                self.completed = self.player.getTime() / self.player.getTotalTime()
                debug(u'Playback of {} with id {} is {}% complete'.format(self.currently_playing['title'], self.currently_playing['id'], self.completed * 100))

if __name__ == '__main__':
    MarkerService().run()