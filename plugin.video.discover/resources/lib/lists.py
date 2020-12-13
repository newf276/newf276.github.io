import xbmcplugin
from resources.lib import text
from resources.lib import Trakt
from resources.lib import nav_base
from resources.lib import meta_info
from resources.lib import playrandom
from resources.lib import nav_movies
from resources.lib import nav_tvshows
from resources.lib.xswift2 import plugin

SORT = [
    xbmcplugin.SORT_METHOD_UNSORTED,
    xbmcplugin.SORT_METHOD_LABEL,
    xbmcplugin.SORT_METHOD_VIDEO_YEAR]

@plugin.route('/lists')
def lists():
    items = [
        {'label': 'Movies', 'path': plugin.url_for('lists_trakt_movies_collection'), 'icon': nav_base.get_icon_path('traktcollection'),
         'context_menu': [('Play (random)', 'RunPlugin(%s)' % plugin.url_for('lists_trakt_movies_play_random_collection')),
                          ('Add to library', 'RunPlugin(%s)' % plugin.url_for('lists_trakt_movies_collection_to_library'))]
        },
        {'label': 'TV shows', 'path': plugin.url_for('lists_trakt_tv_collection'), 'icon': nav_base.get_icon_path('traktcollection')
        },
        {'label': 'Search playlists', 'path': plugin.url_for('lists_trakt_search_for_lists'), 'icon': nav_base.get_icon_path('search')}]
    for item in items: item['properties'] = {'fanart_image': nav_base.get_background_path()}
    return items

@plugin.route('/lists/trakt_movies_collection')
def lists_trakt_movies_collection(raw=False):
    results = sorted(Trakt.trakt_get_collection('movies'), key=lambda k: k['collected_at'], reverse=True)
    if raw: return results
    movies = [meta_info.get_trakt_movie_metadata(item['movie']) for item in results]
    items = [nav_movies.make_movie_item(movie) for movie in movies]
    return plugin.finish(items=items)

@plugin.route('/lists/trakt_movies_collection_to_library')
def lists_trakt_movies_collection_to_library():
    nav_movies.movies_add_all_to_library(Trakt.trakt_get_collection('movies'))

@plugin.route('/lists/trakt_movies_play_random_collection')
def lists_trakt_movies_play_random_collection():
    movies = lists_trakt_movies_collection(raw=True)
    for movie in movies: movie['type'] = 'movie'
    playrandom.trakt_play_random(movies)

@plugin.route('/lists/trakt_tv_collection')
def lists_trakt_tv_collection(raw=False):
    results = sorted(Trakt.trakt_get_collection('shows'), key=lambda k: k['last_collected_at'], reverse=True)
    if raw: return results
    shows = [meta_info.get_tvshow_metadata_trakt(item['show']) for item in results]
    items = [nav_tvshows.make_tvshow_item(show) for show in shows if show.get('tvdb_id')]
    return plugin.finish(items=items)

@plugin.route('/lists/trakt_tv_collection_to_library')
def lists_trakt_tv_collection_to_library():
    nav_tvshows.tv_add_all_to_library(Trakt.trakt_get_collection('shows'))

@plugin.route('/lists/show_list/<user>/<slug>')
def lists_trakt_show_list(user, slug, raw=False):
    list_items = Trakt.get_list(user, slug)
    if raw: return list_items
    return _lists_trakt_show_list(list_items)

@plugin.route('/lists/play_random/<user>/<slug>')
def lists_trakt_play_random(user, slug):
    items = lists_trakt_show_list(user, slug, raw=True)
    playrandom.trakt_play_random(items)

@plugin.route('/lists/trakt_search_for_lists')
def lists_trakt_search_for_lists():
    term = plugin.keyboard(heading='Enter search string')
    if term != None and term != '': return lists_search_for_lists_term(term, 1)
    else: return

@plugin.route('/lists/search_for_lists_term/<term>/<page>')
def lists_search_for_lists_term(term, page):
    lists, pages = Trakt.search_for_list(term, page)
    page = int(page)
    pages = int(pages)
    items = []
    for list in lists:
        if 'list' in list: list_info = list['list']
        else: continue
        name = list_info['name']
        user = list_info['username']
        slug = list_info['ids']['slug']
        total = list_info['item_count']
        info = {}
        info['title'] = name
        if 'description' in list_info: info['plot'] = list_info['description']
        else: info['plot'] = 'No description available'
        if user != None and total != None and total != 0:
            items.append({'label': '%s - %s (%s)' % (text.to_utf8(name), text.to_utf8(user), total),
                          'path': plugin.url_for('lists_trakt_show_list', user=user, slug=slug),
                          'context_menu': [('Play (random)', 'RunPlugin(%s)' % plugin.url_for('lists_trakt_play_random', user=user, slug=slug))],
                          'info': info,
                          'icon': nav_base.get_icon_path('traktlikedlists')})
            fanart = plugin.addon.getAddonInfo('fanart')
            for item in items: item['properties'] = {'fanart_image': nav_base.get_background_path()}
    if pages > page: items.append({'label': '%s/%s  [I]Next page[/I]  >>' % (page, pages + 1),
                                   'path': plugin.url_for('lists_search_for_lists_term', term = term, page=page + 1),
                                   'icon': nav_base.get_icon_path('item_next'),
                                   'properties': {'fanart_image': nav_base.get_background_path()}})
    return plugin.finish(items=items, sort_methods=SORT)

@plugin.route('/lists/_show_list/<list_items>')
def _lists_trakt_show_list(list_items):
    from resources.lib.TheMovieDB import People
    genres_dict = Trakt.trakt_get_genres('tv')
    items = []
    for list_item in list_items:
        item = None
        item_type = list_item['type']
        if item_type == 'show':
            tvdb_id = list_item['show']['ids']['tvdb']
            if tvdb_id != '' and tvdb_id != None:
                show = list_item['show']
                info = meta_info.get_tvshow_metadata_trakt(show, genres_dict)
                item = nav_tvshows.make_tvshow_item(info)
            else: item = None
        elif item_type == 'season':
            tvdb_id = list_item['show']['ids']['tvdb']
            season = list_item['season']
            show = list_item['show']
            show_info = meta_info.get_tvshow_metadata_trakt(show, genres_dict)
            season_info = meta_info.get_season_metadata_trakt(show_info,season, genres_dict)
            label = '%s - Season %s' % (show['title'], season['number'])
            item = ({'label': label,
                     'path': plugin.url_for('tv_season', id=tvdb_id, season_num=list_item['season']['number']),
                     'info': season_info,
                     'thumbnail': season_info['poster'],
                     'icon': nav_base.get_icon_path('tv'),
                     'poster': season_info['poster'],
                     'properties': {'fanart_image': season_info['fanart']}})
        elif item_type == 'episode':
            tvdb_id = list_item['show']['ids']['tvdb']
            episode = list_item['episode']
            show = list_item['show']
            season_number = episode['season']
            episode_number = episode['number']
            show_info = meta_info.get_tvshow_metadata_trakt(show, genres_dict)
            episode_info = meta_info.get_episode_metadata_trakt(show_info, episode)
            label = '%s - S%sE%s - %s' % (show_info['title'], season_number, episode_number, episode_info['title'])
            item = ({'label': label,
                     'path': plugin.url_for('tv_play', id=tvdb_id, season=season_number, episode=episode_number),
                     'info': episode_info,
                     'is_playable': True,
                     'info_type': 'video',
                     'stream_info': {'video': {}},
                     'thumbnail': episode_info['poster'],
                     'poster': episode_info['poster'],
                     'icon': nav_base.get_icon_path('tv'),
                     'properties': {'fanart_image': episode_info['fanart']}})
        elif item_type == 'movie':
            movie = list_item['movie']
            movie_info = meta_info.get_trakt_movie_metadata(movie)
            try: tmdb_id = movie_info['tmdb']
            except: tmdb_id = ''
            try: imdb_id = movie_info['imdb']
            except: imdb_id = ''
            if tmdb_id != None and tmdb_id != '':
                src = 'tmdb'
                id = tmdb_id
            elif imdb_id != None and mdb_id != '':
                src = 'imdb'
                id = imdb_id
            else:
                src = ''
                id = ''
            if src == '': item = None
            item = nav_movies.make_movie_item(movie_info)
        elif item_type == 'person':
            person_id = list_item['person']['ids']['trakt']
            person_tmdb_id = list_item['person']['ids']['tmdb']
            try:
                person_images = People(person_tmdb_id).images()['profiles']
                person_image = 'https://image.tmdb.org/t/p/w640' + person_images[0]['file_path']
            except: person_image = ''
            person_name = text.to_utf8(list_item['person']['name'])
            item = ({'label': person_name,
                     'path': plugin.url_for('trakt_movies_person', person_id=person_id),
                     'thumbnail': person_image,
                     'icon': nav_base.get_icon_path('movies'),
                     'poster': person_image,
                     'properties': {'fanart_image': person_image}})
        if item is not None: items.append(item)
    for item in items: item['properties'] = {'fanart_image': nav_base.get_background_path()}
    return items