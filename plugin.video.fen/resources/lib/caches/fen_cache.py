# -*- coding: utf-8 -*-
import xbmc
import datetime
from modules.utils import to_utf8
from caches.base_cache import BaseCache
# from modules.utils import logger

dbfile = xbmc.translatePath("special://profile/addon_data/plugin.video.fen/fen_cache2.db")

class FenCache(BaseCache):
	def __init__(self):
		BaseCache.__init__(self, dbfile, 'fencache')

	def delete_all_lists(self):
		from modules.nav_utils import media_lists
		media_lists = media_lists()
		dbcon = self.connect_database()
		dbcur = self.set_PRAGMAS(dbcon)
		sql = """SELECT id from fencache where id LIKE """
		for item in media_lists: sql = sql + "'" + item + "'" + ' OR id LIKE '
		sql = sql[:-12]
		dbcur.execute(sql)
		results = dbcur.fetchall()
		try:
			for item in results:
				try:
					dbcur.execute("""DELETE FROM fencache WHERE id=?""", (str(item[0]),))
					self.delete_memory_cache(str(item[0]))
				except Exception: pass
			dbcon.commit()
			dbcon.execute("VACUUM")
			dbcon.commit()
			dbcon.close()
		except Exception: pass

	def delete_all_folderscrapers(self):
		dbcon = self.connect_database()
		dbcur = self.set_PRAGMAS(dbcon)
		dbcur.execute("SELECT id FROM fencache WHERE id LIKE 'fen_FOLDERSCRAPER_%'")
		remove_list = [str(i[0]) for i in dbcur.fetchall()]
		if not remove_list: return 'success'
		try:
			dbcur.execute("DELETE FROM fencache WHERE id LIKE 'fen_FOLDERSCRAPER_%'")
			dbcon.commit()
			dbcon.execute("VACUUM")
			dbcon.commit()
			dbcon.close()
			for item in remove_list: self.delete_memory_cache(item)
		except Exception: pass

def cache_object(function, string, url, json=True, expiration=24):
	_cache = FenCache()
	cache = _cache.get(string)
	if cache: return to_utf8(cache)
	if isinstance(url, list): args = tuple(url)
	else: args = (url,)
	if json: result = function(*args).json()
	else: result = function(*args)
	_cache.set(string, result, expiration=datetime.timedelta(hours=expiration))
	return to_utf8(result)
