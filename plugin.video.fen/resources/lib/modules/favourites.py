import xbmc, xbmcgui
from sys import argv
from modules.nav_utils import notification
from modules.text import to_unicode
from modules.utils import to_utf8
from modules.utils import local_string as ls
from modules import settings
try: from sqlite3 import dbapi2 as database
except ImportError: from pysqlite2 import dbapi2 as database
# from modules.utils import logger

class Favourites:
	def __init__(self, params):
		self.dialog = xbmcgui.Dialog()
		self.fav_database = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/favourites.db')
		self.params = params
		self.db_type = self.params.get('db_type')
		self.tmdb_id = self.params.get('tmdb_id')
		self.title = self.params.get('title')
		self.name = self.params.get('name')
		self.id = self.params.get('_id')
		self.url_dl = self.params.get('url_dl')
		self.size = self.params.get('size')
		settings.check_database(self.fav_database)

	def add_to_favourites(self):
		try:
			dbcon = database.connect(self.fav_database)
			dbcon.execute("INSERT INTO favourites VALUES (?, ?, ?)", (self.db_type, str(self.tmdb_id), to_unicode(self.title)))
			dbcon.commit()
			dbcon.close()
			notification(ls(32576), 3500)
		except: notification(ls(32574), 3500)

	def remove_from_favourites(self):
		dbcon = database.connect(self.fav_database)
		dbcon.execute("DELETE FROM favourites where db_type=? and tmdb_id=?", (self.db_type, str(self.tmdb_id)))
		dbcon.commit()
		dbcon.close()
		xbmc.executebuiltin("Container.Refresh")
		notification(ls(32576), 3500)

	def get_favourites(self, db_type):
		dbcon = database.connect(self.fav_database)
		dbcur = dbcon.cursor()
		dbcur.execute('''SELECT tmdb_id, title FROM favourites WHERE db_type=?''', (db_type,))
		result = dbcur.fetchall()
		dbcon.close()
		result = [{'tmdb_id': str(i[0]), 'title': str(to_utf8(i[1]))} for i in result]
		return result

	def clear_favourites(self):
		from modules.utils import confirm_dialog
		favorites = ls(32453)
		fl = [('%s %s' % (ls(32028), ls(32453)), 'movie'), ('%s %s' % (ls(32029), ls(32453)), 'tvshow')]
		fl_choose = self.dialog.select("Fen", [i[0] for i in fl])
		if fl_choose < 0: return
		selection = fl[fl_choose]
		self.db_type = selection[1]
		if not confirm_dialog(): return
		dbcon = database.connect(self.fav_database)
		dbcon.execute("DELETE FROM favourites WHERE db_type=?", (self.db_type,))
		dbcon.execute("VACUUM")
		dbcon.commit()
		dbcon.close()
		notification(ls(32576), 3000)

def retrieve_favourites(db_type, page_no, letter):
	from modules.nav_utils import paginate_list
	from modules.utils import title_key
	ignore_articles = settings.ignore_articles()
	paginate = settings.paginate()
	limit = settings.page_limit()
	data = Favourites({}).get_favourites(db_type)
	data = sorted(data, key=lambda k: title_key(k['title'], ignore_articles))
	original_list = [{'media_id': i['tmdb_id'], 'title': i['title']} for i in data]
	if paginate: final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	else: final_list, total_pages = original_list, 1
	return final_list, total_pages


