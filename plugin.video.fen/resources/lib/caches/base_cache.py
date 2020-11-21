# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcvfs
import datetime
import time
try: import sqlite3 as database
except ImportError: import pysqlite2 as database
# from modules.utils import logger

window = xbmcgui.Window(10000)

class BaseCache(object):
	def __init__(self, dbfile, row):
		self.datapath = xbmc.translatePath("special://profile/addon_data/plugin.video.fen/")
		self.dbfile = dbfile
		self.row = row
		self.time = datetime.datetime.now()
		self.timeout = 240
		self.check_database()

	def get(self, string):
		result = None
		try:
			current_time = self._get_timestamp(self.time)
			result = self.get_memory_cache(string, current_time)
			if result is None:
				dbcon = self.connect_database()
				dbcur = self.set_PRAGMAS(dbcon)
				dbcur.execute("SELECT expires, data FROM %s WHERE id = ?" % self.row, (string,))
				cache_data = dbcur.fetchone()
				if cache_data:
					if cache_data[0] > current_time:
						result = eval(cache_data[1])
						self.set_memory_cache(result, string, cache_data[1])
					else:
						self.delete(string, dbcon)
		except Exception:
			pass
		return result

	def set(self, string, data, expiration=datetime.timedelta(days=30)):
		try:
			expires = self._get_timestamp(self.time + expiration)
			dbcon = self.connect_database()
			dbcur = self.set_PRAGMAS(dbcon)
			dbcur.execute("INSERT OR REPLACE INTO %s(id, data, expires) VALUES (?, ?, ?)" % self.row, (string, repr(data), int(expires)))
			dbcon.commit()
			self.set_memory_cache(data, string, int(expires))
		except Exception:
			return None

	def get_memory_cache(self, string, current_time):
		result = None
		try:
			try: cachedata = window.getProperty(string.encode("utf-8"))
			except: cachedata = window.getProperty(string)
			if cachedata:
				cachedata = eval(cachedata)
				if cachedata[0] > current_time:
					result = cachedata[1]
		except Exception: pass
		return result

	def set_memory_cache(self, data, string, expires):
		try:
			cachedata = (expires, data)
			try: cachedata_repr = repr(cachedata).encode("utf-8")
			except: cachedata_repr = repr(cachedata)
			window.setProperty(string, cachedata_repr)
		except Exception: pass

	def delete(self, string, dbcon=None):
		try:
			if not dbcon: self.connect_database()
			dbcur = dbcon.cursor()
			dbcur.execute("DELETE FROM %s WHERE id = ?" % self.row, (string,))
			self.delete_memory_cache(string)
			dbcon.commit()
		except Exception: return

	def delete_memory_cache(self, string):
		window.clearProperty(string)

	def connect_database(self):
		return database.connect(self.dbfile, timeout=self.timeout)

	def set_PRAGMAS(self, dbcon):
		dbcur = dbcon.cursor()
		dbcur.execute('''PRAGMA synchronous = OFF''')
		dbcur.execute('''PRAGMA journal_mode = OFF''')
		return dbcur

	def check_database(self):
		if not xbmcvfs.exists(self.datapath):
			xbmcvfs.mkdirs(self.datapath)
		if not xbmcvfs.exists(self.dbfile):
			dbcon = database.connect(self.dbfile)
			self._check_cache_table(dbcon)

	def _check_cache_table(self, dbcon=None):
		if not dbcon: dbcon = database.connect(self.dbfile)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS %s(
					id TEXT UNIQUE, data TEXT, expires INTEGER)
					   """ % self.row)

	def _get_timestamp(self, date_time):
		return int(time.mktime(date_time.timetuple()))
