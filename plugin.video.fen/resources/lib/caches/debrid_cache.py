import xbmc, xbmcvfs
import time
import datetime
import sqlite3 as database
# from modules.utils import logger


class DebridCache:
	def __init__(self):
		self.datapath = xbmc.translatePath("special://profile/addon_data/plugin.video.fen/")
		self.dbfile = xbmc.translatePath("special://profile/addon_data/plugin.video.fen/debridcache.db")

	def get_many(self, hash_list):
		result = None
		try:
			current_time = self._get_timestamp(datetime.datetime.now())
			dbcon = database.connect(self.dbfile, timeout=40.0)
			dbcur = self._set_PRAGMAS(dbcon)
			dbcur.execute('SELECT * FROM debrid_data WHERE hash in ({0})'.format(', '.join('?' for _ in hash_list)), hash_list)
			cache_data = dbcur.fetchall()
			if cache_data:
				if cache_data[0][3] > current_time:
					result = cache_data
				else:
					self.remove_many(cache_data)
		except: pass
		return result

	def remove_many(self, old_cached_data):
		try:
			old_cached_data = [(str(i[0]),) for i in old_cached_data]
			dbcon = database.connect(self.dbfile, timeout=40.0)
			dbcur = self._set_PRAGMAS(dbcon)
			dbcur.executemany("DELETE FROM debrid_data WHERE hash=?", old_cached_data)
			dbcon.commit()
		except: pass

	def set_many(self, hash_list, debrid, expiration=datetime.timedelta(hours=24)):
		try:
			expires = self._get_timestamp(datetime.datetime.now() + expiration)
			insert_list = [(i[0], debrid, i[1], expires) for i in hash_list]
			dbcon = database.connect(self.dbfile, timeout=40.0)
			dbcur = self._set_PRAGMAS(dbcon)
			dbcur.executemany("INSERT INTO debrid_data VALUES (?, ?, ?, ?)", insert_list)
			dbcon.commit()
		except: pass

	def _set_PRAGMAS(self, dbcon):
		dbcur = dbcon.cursor()
		dbcur.execute('''PRAGMA synchronous = OFF''')
		dbcur.execute('''PRAGMA journal_mode = OFF''')
		return dbcur

	def check_database(self):
		if not xbmcvfs.exists(self.datapath):
			xbmcvfs.mkdirs(self.datapath)
		dbcon = database.connect(self.dbfile)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS debrid_data
					  (hash text not null, debrid text not null, cached text, expires integer, unique (hash, debrid))
						""")
		dbcon.close()

	def clear_database(self):
		try:
			dbcon = database.connect(self.dbfile)
			dbcur = dbcon.cursor()
			dbcur.execute("DELETE FROM debrid_data")
			dbcur.execute("VACUUM")
			dbcon.commit()
			dbcon.close()
			return 'success'
		except: return 'failure'

	def _get_timestamp(self, date_time):
		return int(time.mktime(date_time.timetuple()))






