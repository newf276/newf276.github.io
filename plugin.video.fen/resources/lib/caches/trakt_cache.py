# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import datetime
from modules.utils import to_utf8
from caches.base_cache import BaseCache
from modules import settings
# from modules.utils import logger

dbfile = xbmc.translatePath("special://profile/addon_data/plugin.video.fen/fen_trakt2.db")

window = xbmcgui.Window(10000)

class TraktCache(BaseCache):
	def __init__(self):
		BaseCache.__init__(self, dbfile, 'fentrakt')

def cache_trakt_object(function, string, url, expiration=24):
	expires = expiration if expiration else settings.trakt_cache_duration()
	_cache = TraktCache()
	cache = _cache.get(string)
	if cache: return to_utf8(cache)
	result = function(url)
	_cache.set(string, result, expiration=datetime.timedelta(hours=expires))
	return to_utf8(result)

def clear_trakt_watched_data(db_type):
	settings.check_database(dbfile)
	dbcon = TraktCache().connect_database()
	dbcur = dbcon.cursor()
	if db_type == 'tvshow':
		dbcur.execute("DELETE FROM fentrakt WHERE id=?", ('trakt_tv_watched_raw',))
		window.clearProperty('trakt_tv_watched_raw')
	action = 'trakt_indicators_movies' if db_type in ('movie', 'movies') else 'trakt_indicators_tv'
	dbcur.execute("DELETE FROM fentrakt WHERE id=?", (action,))
	dbcon.commit()
	window.clearProperty(action)

def clear_trakt_hidden_data(list_type):
    settings.check_database(dbfile)
    action = 'trakt_hidden_items_%s' % list_type
    try:
        dbcon = TraktCache().connect_database()
        dbcur = dbcon.cursor()
        dbcur.execute("DELETE FROM fentrakt WHERE id=?", (action,))
        dbcon.commit()
        window.clearProperty(action)
    except: pass

def clear_trakt_collection_watchlist_data(list_type, db_type):
	settings.check_database(dbfile)
	if db_type == 'movies': db_type = 'movie' 
	if db_type in ('tvshows', 'shows'): db_type = 'tvshow' 
	action = 'trakt_%s_%s' % (list_type, db_type)
	try:
		dbcon = TraktCache().connect_database()
		dbcur = dbcon.cursor()
		dbcur.execute("DELETE FROM fentrakt WHERE id=?", (action,))
		dbcon.commit()
		window.clearProperty(action)
		window.clearProperty('fen_trakt_%s_%s' % (list_type, db_type))
	except: pass

def clear_trakt_list_contents_data(clear_all=False, user=None, list_slug=None):
    settings.check_database(dbfile)
    if clear_all:
        from indexers.trakt_lists import get_trakt_lists
        my_lists = [(item["user"]["ids"]["slug"], item["ids"]["slug"]) for item in get_trakt_lists(list_type='my_lists', build_list=False)]
        liked_lists = [(item["list"]["user"]["ids"]["slug"], item["list"]["ids"]["slug"]) for item in get_trakt_lists(list_type='liked_lists', build_list=False)]
        my_lists.extend(liked_lists)
        try:
            dbcon = TraktCache().connect_database()
            dbcur = dbcon.cursor()
            dbcur.execute("DELETE FROM fentrakt WHERE id LIKE 'trakt_list_contents_%'")
            dbcon.commit()
        except: pass
        for i in my_lists: window.clearProperty('trakt_list_contents_%s_%s' % (i[0], i[1]))
    else:
        action = 'trakt_list_contents_%s_%s' % (user, list_slug)
        try:
            dbcon = TraktCache().connect_database()
            dbcur = dbcon.cursor()
            dbcur.execute("DELETE FROM fentrakt WHERE id=?", (action,))
            dbcon.commit()
            window.clearProperty(action)
        except: pass

def clear_trakt_list_data(list_type):
    settings.check_database(dbfile)
    action = 'trakt_my_lists' if list_type == 'my_lists' else 'trakt_liked_lists'
    try:
        dbcon = TraktCache().connect_database()
        dbcur = dbcon.cursor()
        dbcur.execute("DELETE FROM fentrakt WHERE id=?", (action,))
        dbcon.commit()
        window.clearProperty(action)
    except: pass

def clear_trakt_calendar():
    settings.check_database(dbfile)
    try:
        dbcon = TraktCache().connect_database()
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT id FROM fentrakt WHERE id LIKE 'get_trakt_my_calendar%'")
        c_days = dbcur.fetchall()
        c_days = [str(i[0]) for i in c_days]
        dbcur.execute("DELETE FROM fentrakt WHERE id LIKE 'get_trakt_my_calendar%'")
        dbcon.commit()
        for i in c_days: window.clearProperty(i)
    except: return

def clear_all_trakt_cache_data(silent=False, confirm=True):
	from modules.nav_utils import notification, close_all_dialog
	from modules.utils import confirm_dialog
	from modules.utils import local_string as ls
	def _process():
		try:
			dbcon = TraktCache().connect_database()
			dbcur = dbcon.cursor()
			dbcur.execute("SELECT id FROM fentrakt")
			all_entries = [str(i[0]) for i in dbcur.fetchall()]
			dbcur.execute("DELETE FROM fentrakt")
			dbcon.commit()
			dbcur.execute("VACUUM")
			dbcon.close()
			for string in all_entries:
				window.clearProperty(string)
			return True
		except: return False
	if silent:
		return _process()
	else:
		if confirm:
			if not confirm_dialog(): return False
		close_all_dialog()
		xbmc.sleep(200)
		result = _process()
		return result

def clear_cache_on_startup():
	from modules.nav_utils import notification
	from modules.utils import local_string as ls
	success = clear_all_trakt_cache_data(silent=True)
	return

	