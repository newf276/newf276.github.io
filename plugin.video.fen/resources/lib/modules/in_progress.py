import xbmc, xbmcgui, xbmcplugin
from sys import argv
from threading import Thread
from modules.nav_utils import setView
from indexers.tvshows import build_episode
from tikimeta import tvshow_meta, retrieve_user_info, check_meta_database
from modules.settings_reader import get_setting
from modules import settings
try:
	from sqlite3 import dbapi2 as database
except ImportError:
	from pysqlite2 import dbapi2 as database
# from modules.utils import logger

WATCHED_DB = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/watched_status.db')

window = xbmcgui.Window(10000)

def in_progress_movie(db_type, page_no, letter):
	from modules.nav_utils import paginate_list
	paginate = settings.paginate()
	limit = settings.page_limit()
	settings.check_database(WATCHED_DB)
	dbcon = database.connect(WATCHED_DB)
	dbcur = dbcon.cursor()
	dbcur.execute('''SELECT media_id FROM progress WHERE db_type=? ORDER BY rowid DESC''', ('movie',))
	rows = dbcur.fetchall()
	data = [i[0] for i in rows if not i[0] == '']
	original_list = [{'media_id': i} for i in data]
	if paginate: final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	else: final_list, total_pages = original_list, 1
	return final_list, total_pages

def in_progress_tvshow(db_type, page_no, letter):
	from modules.utils import title_key
	from modules.nav_utils import paginate_list
	ignore_articles = settings.ignore_articles()
	paginate = settings.paginate()
	limit = settings.page_limit()
	check_meta_database()
	if settings.watched_indicators() in (1, 2):
		from apis.trakt_api import trakt_indicators_tv
		items = trakt_indicators_tv()
		data = [(i[0], i[3]) for i in items if i[1] > len(i[2])]
	else:
		from modules.indicators_bookmarks import get_watched_status_tvshow, get_watched_info_tv
		def _process(item):
			meta = tvshow_meta('tmdb_id', item[0], meta_user_info)
			watched_status = get_watched_status_tvshow(watched_info, use_trakt, meta['tmdb_id'], meta.get('total_episodes'))
			if not watched_status[0] == 1: data.append(item)
		data = []
		threads = []
		settings.check_database(WATCHED_DB)
		dbcon = database.connect(WATCHED_DB)
		dbcur = dbcon.cursor()
		dbcur.execute('''SELECT media_id, title, last_played FROM watched_status WHERE db_type=? ORDER BY rowid DESC''', ('episode',))
		rows1 = dbcur.fetchall()
		in_progress_result = list(set(rows1))
		watched_info, use_trakt = get_watched_info_tv()
		meta_user_info = retrieve_user_info()
		for item in in_progress_result: threads.append(Thread(target=_process, args=(item,)))
		[i.start() for i in threads]
		[i.join() for i in threads]
		data = [(s,[i[1] for i in data if i[0] == s][0], [i[2] for i in data if i[0] == s][0]) for s in sorted(set([i[0] for i in data]))]
	data = sorted(data, key=lambda k: title_key(k[1], ignore_articles))
	original_list = [{'media_id': i[0]} for i in data]
	if paginate: final_list, total_pages = paginate_list(original_list, page_no, letter, limit)
	else: final_list, total_pages = original_list, 1
	return final_list, total_pages

def build_in_progress_episode():
	from apis import simplejson as json
	from modules.indicators_bookmarks import get_watched_info_tv
	def process_eps(item):
		episode_item = {"season": int(item[1]), "episode": int(item[2]), "meta": tvshow_meta('tmdb_id', item[0], meta_user_info),
						"adjust_hours": adjust_hours, "current_adjusted_date": current_adjusted_date, 'watched_indicators': watched_indicators}
		listitem = build_episode(episode_item, watched_info, use_trakt, meta_user_info, meta_user_info_json, is_widget)['listitem']
		xbmcplugin.addDirectoryItem(__handle__, listitem[0], listitem[1], isFolder=listitem[2])
	__handle__ = int(argv[1])
	check_meta_database()
	settings.check_database(WATCHED_DB)
	watched_info, use_trakt = get_watched_info_tv()
	meta_user_info = retrieve_user_info()
	meta_user_info_json = json.dumps(meta_user_info)
	adjust_hours = int(get_setting('datetime.offset'))
	current_adjusted_date = settings.adjusted_datetime(dt=True)
	is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
	watched_indicators = settings.watched_indicators()
	window.clearProperty('fen_fanart_error')
	threads = []
	dbcon = database.connect(WATCHED_DB)
	dbcur = dbcon.cursor()
	dbcur.execute('''SELECT media_id, season, episode FROM progress WHERE db_type=? ORDER BY rowid DESC''', ('episode',))
	rows = dbcur.fetchall()
	for item in rows: threads.append(Thread(target=process_eps, args=(item,)))
	[i.start() for i in threads]
	[i.join() for i in threads]
	xbmcplugin.setContent(__handle__, 'episodes')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.episode_lists', 'episodes')

	