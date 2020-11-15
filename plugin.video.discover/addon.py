import os, sys, time, shutil
import xbmc, xbmcplugin
from resources.lib import Trakt
from resources.lib import lists
from resources.lib import updater
from resources.lib import dialogs
from resources.lib import settings
from resources.lib import nav_base
from resources.lib import properties
from resources.lib import lib_movies
from resources.lib import nav_movies
from resources.lib import nav_tvshows
from resources.lib import lib_tvshows
from resources.lib.xswift2 import plugin

@plugin.route('/')
def root():
    items = [
        {'label': 'Movies',
         'path': plugin.url_for('movies'),
         'icon': nav_base.get_icon_path('movies'),
         'thumbnail': nav_base.get_icon_path('movies')
        },
        {'label': 'TV Shows',
         'path': plugin.url_for('tv'),
         'icon': nav_base.get_icon_path('tv'),
         'thumbnail': nav_base.get_icon_path('tv')
        },
        {'label': 'Trakt collections',
         'path': plugin.url_for('lists'),
         'icon': nav_base.get_icon_path('trakt'),
         'thumbnail': nav_base.get_icon_path('trakt')
        },
        {'label': 'Search',
         'path': plugin.url_for('root_search'),
         'icon': nav_base.get_icon_path('search'),
         'thumbnail': nav_base.get_icon_path('search')}]
    for item in items: item['properties'] = {'fanart_image': nav_base.get_background_path()}
    return items

@plugin.route('/clear_cache')
def clear_cache():
    for filename in os.listdir(plugin.storage_path):
        file_path = os.path.join(plugin.storage_path, filename)
        if os.path.isfile(file_path): os.unlink(file_path)
        elif os.path.isdir(file_path): shutil.rmtree(file_path)
    dialogs.notify(title='Cache', msg='Cleared', delay=3000, image=nav_base.get_icon_path('meta'))

@plugin.route('/update_library')
def update_library():  ##### TODO SPLIT UPDATE & SYNC LIBRARY(no need to sync everytime we update) #####
#@plugin.route('/sync_library')
#def sync_library():
    now = time.time()
    is_syncing = properties.get_property('syncing_library')
    if is_syncing and now - int(is_syncing) < 120: plugin.log.debug('Skipping library sync')
    else:
        if plugin.get_setting(settings.SETTING_LIBRARY_SYNC_COLLECTION, bool) == True:
            try:
                properties.set_property('syncing_library', int(now))
                lib_tvshows.sync_trakt_collection()
                lib_movies.sync_trakt_collection()
            finally: properties.clear_property('syncing_library')
        else: properties.clear_property('syncing_library')
#@plugin.route('/update_library')
#def update_library():
#    now = time.time()
    is_updating = properties.get_property('updating_library')
    if is_updating and now - int(is_updating) < 120:
        plugin.log.debug('Skipping library update')
        return
    else:
        if plugin.get_setting(settings.SETTING_LIBRARY_UPDATES, bool) == True:
            try:
                properties.set_property('updating_library', int(now))
                lib_tvshows.update_library()
            finally: properties.clear_property('updating_library')
        else: properties.clear_property('updating_library')

@plugin.route('/update_players')
@plugin.route('/update_players/<url>', name='update_players_url')
def update_players():
    if updater.update_players('https://github.com/newf276/Player-Files/raw/master/players.zip'): dialogs.notify(title='Discover players update', msg='Done', delay=3000, image=nav_base.get_icon_path('meta'))
    else: dialogs.notify(title='Discover players update', msg='Failed', delay=3000)

@plugin.route('/setup/total')
def total_setup():
    dialogs.notify(title='Total Setup', msg='Started', delay=2000, image=nav_base.get_icon_path('meta'))
    if sources_setup() == True: pass
    if players_setup() == True: pass
    xbmc.sleep(1000)
    dialogs.notify(title='Total Setup', msg='Done', delay=3000, image=nav_base.get_icon_path('meta'))

@plugin.route('/setup/silent')
def silent_setup():
    xbmc.executebuiltin('SetProperty(running,totalmeta,home)')
    movielibraryfolder = plugin.get_setting(settings.SETTING_MOVIES_LIBRARY_FOLDER, unicode)
    tvlibraryfolder = plugin.get_setting(settings.SETTING_TV_LIBRARY_FOLDER, unicode)
    try:
        lib_movies.auto_movie_setup(movielibraryfolder)
        lib_tvshows.auto_tvshows_setup(tvlibraryfolder)
    except: pass
    xbmc.executebuiltin('ClearProperty(running,home)')

@plugin.route('/setup/players')
def players_setup():
    properties.set_property('running','totalmeta')
    if updater.update_players('https://github.com/newf276/Player-Files/raw/master/players.zip'): dialogs.notify(title='Discover players setup', msg='Done', delay=3000, image=nav_base.get_icon_path('meta'))
    else: dialogs.notify(title='Discover players setup', msg='Failed', delay=3000)
    properties.clear_property('running')
    return True

@plugin.route('/setup/sources')
def sources_setup():
    movielibraryfolder = plugin.get_setting(settings.SETTING_MOVIES_LIBRARY_FOLDER, unicode)
    tvlibraryfolder = plugin.get_setting(settings.SETTING_TV_LIBRARY_FOLDER, unicode)
    try:
        lib_movies.auto_movie_setup(movielibraryfolder)
        lib_tvshows.auto_tvshows_setup(tvlibraryfolder)
        dialogs.notify(title='Discover sources setup', msg='Done', delay=3000, image=nav_base.get_icon_path('meta'))
    except: dialogs.notify(title='Discover sources setup', msg='Failed', delay=3000)
    return True

@plugin.route('/search')
def root_search():
    term = plugin.keyboard(heading='Enter search string')
    if term != None and term != '': return root_search_term(term)
    else: return

@plugin.route('/search/edit/<term>')
def root_search_edit(term):
    if term == ' ' or term == None or term == '': term = plugin.keyboard(heading='Enter search string')
    else: term = plugin.keyboard(default=term, heading='Enter search string')
    if term != None and term != '': return root_search_term(term)
    else: return

@plugin.route('/search_term/<term>', options = {'term': 'None'})
def root_search_term(term):
    items = [
        {'label': 'Movies (TMDb) search - %s' % term,
         'path': plugin.url_for('tmdb_movies_search_term', term=term, page='1'),
         'icon': nav_base.get_icon_path('movies'),
         'thumbnail': nav_base.get_icon_path('movies')
        },
        {'label': 'Movies (Trakt) search - %s' % term, 
         'path': plugin.url_for('trakt_movies_search_term', term=term, page='1'),
         'icon': nav_base.get_icon_path('movies'),
         'thumbnail': nav_base.get_icon_path('movies')
        },
        {'label': 'TV Shows (TVDb) search - %s' % term,
         'path': plugin.url_for('tvdb_tv_search_term', term=term, page='1'),
         'icon': nav_base.get_icon_path('tv'),
         'thumbnail': nav_base.get_icon_path('tv')
        },
        {'label': 'TV Shows (TMDb) search - %s' % term,
         'path': plugin.url_for('tmdb_tv_search_term', term=term, page='1'),
         'icon': nav_base.get_icon_path('tv'),
         'thumbnail': nav_base.get_icon_path('tv')
        },
        {'label': 'TV Shows (Trakt) search - %s' % term,
         'path': plugin.url_for('trakt_tv_search_term', term=term, page='1'),
         'icon': nav_base.get_icon_path('tv'),
         'thumbnail': nav_base.get_icon_path('tv')
        },
        {'label': 'Edit search string',
         'path': plugin.url_for('root_search_edit', term=term),
         'icon': nav_base.get_icon_path('search'),
         'thumbnail': nav_base.get_icon_path('search')}]
    for item in items: item['properties'] = {'fanart_image': nav_base.get_background_path()}
    return items

@plugin.route('/play/<label>')
def play_by_label(label):
    types = ['Movies', 'TV Shows']
    selection = dialogs.select('Search for "%s"' % label, [item for item in types])
    if selection   == 0: xbmc.executebuiltin('RunPlugin(plugin://plugin.video.discover/movies/play_by_name/%s/en)' % label)
    elif selection == 1: xbmc.executebuiltin('RunPlugin(plugin://plugin.video.discover/tv/play_by_name/%s/%s/%s/%s/en)' % (xbmc.getInfoLabel('ListItem.TVShowTitle'), xbmc.getInfoLabel('ListItem.Season'), xbmc.getInfoLabel('ListItem.Episode'), label))

@plugin.route('/authenticate_trakt')
def trakt_authentication():
    Trakt.trakt_authenticate()

@plugin.route('/cleartrakt')
def clear_trakt():
    if dialogs.yesno('Discover: Clear Trakt account settings', msg='Reauthorizing Trakt will be required to access Trakt collections.\n\nAre you sure?'):
        plugin.set_setting(settings.SETTING_TRAKT_ACCESS_TOKEN, '')
        plugin.set_setting(settings.SETTING_TRAKT_REFRESH_TOKEN, '')
        plugin.set_setting(settings.SETTING_TRAKT_EXPIRES_AT, '')

def main():
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    plugin.run()
    plugin.set_view_mode(55)

if __name__ == '__main__': main()
