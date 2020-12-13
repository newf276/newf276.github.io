# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import requests
import re
from modules.dom_parser import parseDOM
from caches.fen_cache import cache_object
from modules.utils import imdb_sort_list, to_utf8, remove_accents, replace_html_codes, string_alphanum_to_num
from modules.settings_reader import get_setting, set_setting
# from modules.utils import logger

base_url = 'https://www.imdb.com/'
watchlist_url = 'user/ur%s/watchlist'
user_list_movies_url = 'list/%s/?view=detail&sort=%s&title_type=movie,short,video,tvShort,tvMovie,tvSpecial&start=1&page=%s'
user_list_tvshows_url = 'list/%s/?view=detail&sort=%s&title_type=tvSeries,tvMiniSeries&start=1&page=%s'
lists_link = 'user/ur%s/lists?tab=all&sort=mdfd&order=desc&filter=titles'
reviews_url = 'title/%s/reviews?sort=helpfulness'
trivia_url = 'title/%s/trivia'
blunders_url = 'title/%s/goofs'
parentsguide_url = 'title/%s/parentalguide'
images_url = 'title/%s/mediaindex?page=%s'
videos_url = '_json/video/%s'
people_images_url = 'name/%s/mediaindex?page=%s'
people_search_url_backup = 'search/name/?name=%s'
people_search_url = 'https://sg.media-imdb.com/suggests/%s/%s.json'
movie_year_check_url = 'https://v2.sg.media-imdb.com/suggestion/t/%s.json'

def people_get_imdb_id(actor_name, actor_tmdbID=None):
	from apis.tmdb_api import tmdb_people_externalIDs
	if actor_tmdbID:
		tmdb_ids = tmdb_people_externalIDs(actor_tmdbID)
		if tmdb_ids.get('imdb_id', None) is not None:
			imdb_id = tmdb_ids['imdb_id']
		else:
			imdb_id = imdb_people_id(actor_name)
	else:
		imdb_id = imdb_people_id(actor_name)
	return imdb_id

def imdb_user_lists(db_type):
	imdb_user = string_alphanum_to_num(get_setting('imdb_user'))
	string = "%s_%s_%s" % ('imdb_user_lists', db_type, imdb_user)
	url = base_url + lists_link % imdb_user
	params = {'url': url, 'action': 'imdb_user_lists', 'db_type': db_type}
	return cache_object(get_imdb, string, params, False, 0.5)[0]

def imdb_watchlist(db_type, foo_var, page_no):
	imdb_user = string_alphanum_to_num(get_setting('imdb_user'))
	sort = imdb_sort_list()
	string = "%s_%s_%s_%s_%s" % ('imdb_watchlist', db_type, imdb_user, sort, page_no)
	url = base_url + watchlist_url % imdb_user
	params = {'url': url, 'action': 'imdb_watchlist', 'db_type': db_type, 'sort': sort, 'page_no': page_no}
	return cache_object(get_imdb, string, params, False, 0.5)

def imdb_user_list_contents(db_type, list_id, page_no):
	imdb_user = string_alphanum_to_num(get_setting('imdb_user'))
	sort = imdb_sort_list()
	string = "%s_%s_%s_%s_%s_%s" % ('imdb_user_list_contents', db_type, imdb_user, list_id, sort, page_no)
	params = {'url': list_id, 'action': 'imdb_user_list_contents', 'db_type': db_type, 'sort': sort, 'page_no': page_no}
	return cache_object(get_imdb, string, params, False, 0.5)

def imdb_reviews(imdb_id):
	url = base_url + reviews_url % imdb_id
	string = "%s_%s" % ('imdb_reviews', imdb_id)
	params = {'url': url, 'action': 'imdb_reviews'}
	return cache_object(get_imdb, string, params, False, 168)[0]

def imdb_parentsguide(imdb_id):
	url = base_url + parentsguide_url % imdb_id
	string = "%s_%s" % ('imdb_parentsguide', imdb_id)
	params = {'url': url, 'action': 'imdb_parentsguide'}
	return cache_object(get_imdb, string, params, False, 168)[0]

def imdb_trivia(imdb_id, content):
	url_add = trivia_url if content == 'trivia' else blunders_url
	url = base_url + url_add % imdb_id
	string = "%s_%s_%s" % ('imdb_trivia', content, imdb_id)
	params = {'url': url, 'action': 'imdb_trivia'}
	return cache_object(get_imdb, string, params, False, 168)[0]

def imdb_images(imdb_id, page_no):
	url = base_url + images_url % (imdb_id, page_no)
	string = "%s_%s_%s" % ('imdb_images', imdb_id, str(page_no))
	params = {'url': url, 'action': 'imdb_images', 'next_page': int(page_no)+1}
	return cache_object(get_imdb, string, params, False, 168)

def imdb_videos(imdb_id):
	url = base_url + videos_url % imdb_id
	string = "%s_%s" % ('imdb_videos', imdb_id)
	params = {'url': url, 'imdb_id': imdb_id, 'action': 'imdb_videos'}
	return cache_object(get_imdb, string, params, False, 168)[0]

def imdb_people_images(imdb_id, page_no):
	url = base_url + people_images_url % (imdb_id, page_no)
	string = "%s_%s_%s" % ('imdb_people_images', imdb_id, str(page_no))
	params = {'url': url, 'action': 'imdb_images', 'next_page': 1}
	return cache_object(get_imdb, string, params, False, 168)

def imdb_people_id(name):
	name = name.lower()
	string = "%s_%s" % ('imdb_people_id', name)
	url = 'https://sg.media-imdb.com/suggests/%s/%s.json' % (name[0], name.replace(' ', '%20'))
	url_backup = base_url + people_search_url_backup % name
	params = {'url': url, 'action': 'imdb_people_id', 'name': name, 'url_backup': url_backup}
	return cache_object(get_imdb, string, params, False, 720)[0]

def imdb_movie_year(imdb_id):
	url = movie_year_check_url % imdb_id
	string = "%s_%s" % ('imdb_movie_year', imdb_id)
	params = {'url': url, 'action': 'imdb_movie_year'}
	return cache_object(get_imdb, string, params, False, 720)[0]

def get_imdb(params):
	imdb_list = []
	action = params['action']
	url = params['url']
	next_page = None
	if 'date' in params:
		from datetime import datetime, timedelta
		date_time = (datetime.utcnow() - timedelta(hours=5))
		for i in re.findall('date\[(\d+)\]', url):
			url = url.replace('date[%s]' % i, (date_time - timedelta(days = int(i))).strftime('%Y-%m-%d'))
	if action in ('imdb_watchlist', 'imdb_user_list_contents'):
		list_url_type = user_list_movies_url if params['db_type'] == 'movies' else user_list_tvshows_url
		if action == 'imdb_watchlist':
			url = parseDOM(to_utf8(remove_accents(requests.get(url).text)), 'meta', ret='content', attrs = {'property': 'pageId'})[0]
		url = base_url + list_url_type % (url, params['sort'], params['page_no'])
		result = requests.get(url)
		result = to_utf8(remove_accents(result.text))
		result = result.replace('\n', ' ')
		items = parseDOM(result, 'div', attrs={'class': '.+? lister-item'})
		items += parseDOM(result, 'div', attrs={'class': 'lister-item .+?'})
		items += parseDOM(result, 'div', attrs={'class': 'list_item.+?'})
		for item in to_utf8(items):
			try:
				title = parseDOM(item, 'a')[1]
				year = parseDOM(item, 'span', attrs={'class': 'lister-item-year.+?'})
				year = re.findall('(\d{4})', year[0])[0]
				imdb_id = parseDOM(item, 'a', ret='href')[0]
				imdb_id = re.findall('(tt\d*)', imdb_id)[0]
				imdb_list.append({'title': str(title), 'year': str(year), 'imdb_id': str(imdb_id)})
			except: pass
		try:
			result = result.replace('"class="lister-page-next', '" class="lister-page-next')
			next_page = parseDOM(result, 'a', ret='href', attrs={'class': '.*?lister-page-next.*?'})
			if len(next_page) == 0:
				next_page = parseDOM(result, 'div', attrs = {'class': 'pagination'})[0]
				next_page = zip(parseDOM(next_page, 'a', ret='href'), parseDOM(next_page, 'a'))
				next_page = [i[0] for i in next_page if 'Next' in i[1]]
		except: pass
	elif action == 'imdb_user_lists':
		result = requests.get(url)
		result = to_utf8(remove_accents(result.text))
		items = parseDOM(result, 'li', attrs={'class': 'ipl-zebra-list__item user-list'})    
		for item in to_utf8(items):
			try:
				title = parseDOM(item, 'a')[0]
				title = replace_html_codes(title)
				url = parseDOM(item, 'a', ret='href')[0]
				list_id = url.split('/list/', 1)[-1].strip('/')
				imdb_list.append({'title': title, 'list_id': list_id})
			except: pass
	elif action == 'imdb_trivia':
		result = requests.get(url)
		result = to_utf8(remove_accents(result.text))
		result = result.replace('\n', ' ')
		items = parseDOM(result, 'div', attrs={'class': 'sodatext'})
		for item in to_utf8(items):
			try:
				trivia = re.sub(r'<a href="\S+">', '', item).replace('</a>', '')
				trivia = replace_html_codes(trivia)
				trivia = trivia.replace('<br/><br/>', '\n')
				imdb_list.append(trivia)
			except: pass
	elif action == 'imdb_reviews':
		result = requests.get(url)
		result = to_utf8(remove_accents(result.text))
		result = result.replace('\n', ' ')
		non_spoilers = parseDOM(result, 'div', attrs={'class': 'lister-item mode-detail imdb-user-review  collapsable'})
		spoilers = parseDOM(result, 'div', attrs={'class': 'lister-item mode-detail imdb-user-review  with-spoiler'})
		non_spoilers = [{'spoiler': False, 'content': i} for i in non_spoilers]
		spoilers = [{'spoiler': True, 'content': i} for i in spoilers]
		all_reviews = non_spoilers + spoilers
		for listing in to_utf8(all_reviews):
			try: spoiler = listing['spoiler']
			except: spoiler = False
			try: listing = listing['content']
			except: continue
			try:
				try:
					title = parseDOM(listing, 'a', attrs={'class': 'title'})[0]
					title = to_utf8(remove_accents(title))
				except: title = ''
				try:
					date = parseDOM(listing, 'span', attrs={'class': 'review-date'})[0]
					date = to_utf8(remove_accents(date))
				except: date = ''
				try:
					rating = parseDOM(listing, 'span', attrs={'class': 'rating-other-user-rating'})
					rating = parseDOM(rating, 'span')
					rating = rating[0] + rating[1]
					rating = to_utf8(remove_accents(rating))
				except: rating = ''			
				try:
					content = parseDOM(listing, 'div', attrs={'class': 'text show-more__control'})[0]
					content = replace_html_codes(content)
					content = to_utf8(remove_accents(content))
					content = content.replace('<br/><br/>', '\n')
				except: continue
				review = {'spoiler': spoiler, 'title': title, 'date': date, 'rating': rating, 'content': content}
				imdb_list.append(review)
			except: pass
	elif action == 'imdb_images':
		image_results = []
		result = requests.get(url)
		result = to_utf8(remove_accents(result.text))
		result = result.replace('\n', ' ')
		try:
			pages = parseDOM(result, 'span', attrs={'class': 'page_list'})[0]
			pages = [int(i) for i in parseDOM(pages, 'a')]
		except: pages = [1]
		if params['next_page'] in pages:
			next_page = params['next_page']
		try:
			image_results = parseDOM(result, 'div', attrs={'class': 'media_index_thumb_list'})[0]
			image_results = parseDOM(image_results, 'a')
		except: pass
		if image_results:
			for item in to_utf8(image_results):
				try:
					try: title = re.findall('alt="(.+?)"', item, re.DOTALL)[0]
					except: title = ''
					try:
						thumb = re.findall('src="(.+?)"', item, re.DOTALL)[0]
						thumb = thumb.split('_V1_')[0] + '_V1_UY300_CR26,0,300,300_AL_.jpg'
						image = thumb.split('_V1_')[0] + '_V1_.jpg'
						images = {'title': title, 'thumb': thumb, 'image': image}
					except: continue
					imdb_list.append(images)
				except: pass
	elif action == 'imdb_videos':
		quality_ranks_dict = {'360p': 3, '480p': 2, '720p': 1, '1080p': 0}
		result = requests.get(url).json()
		playlists = result['playlists'][params['imdb_id']]['listItems']
		videoMetadata = result['videoMetadata']
		for item in playlists:
			videos = []
			vid_id = item['videoId']
			metadata = videoMetadata[vid_id]
			title = metadata['title']
			poster = metadata['slate']['url']
			for i in metadata['encodings']:
				quality = i['definition']
				if quality == 'auto': continue
				if quality == 'SD': quality = '360p'
				quality_rank = quality_ranks_dict[quality]
				videos.append({'quality': quality, 'quality_rank': quality_rank, 'url': i['videoUrl']})
			imdb_list.append({'title': title, 'poster': poster, 'videos': videos})
	elif action == 'imdb_people_id':
		try:
			import json
			name = params['name']
			result = requests.get(url).content
			result = to_utf8(json.loads(result.replace('imdb$%s(' % name.replace(' ', '_'), '')[:-1]))['d']
			imdb_list = [i['id'] for i in results if i['id'].startswith('nm') and i['l'].lower() == name][0]
		except: pass
		if not imdb_list:
			result = requests.get(params['url_backup'])
			result = to_utf8(remove_accents(result.text))
			result = result.replace('\n', ' ')
			try:
				result = parseDOM(result, 'div', attrs={'class': 'lister-item-image'})[0]
				imdb_list = re.findall('href="/name/(.+?)"', result, re.DOTALL)[0]
			except: pass
	elif action == 'imdb_movie_year':
		result = requests.get(url).json()
		try:
			result = result['d'][0]
			imdb_list = int(result['y'])
		except: pass
	elif action == 'imdb_parentsguide':
		spoiler_results = None
		spoiler_list = []
		result = requests.get(url)
		result = to_utf8(remove_accents(result.text))
		result = result.replace('\n', ' ')
		results = parseDOM(result, 'section', attrs={'id': 'advisory-(.+?)'})
		try: spoiler_results = parseDOM(result, 'section', attrs={'id': 'advisory-spoilers'})[0]
		except: pass
		if spoiler_results:
			results = [i for i in results if not i in spoiler_results]
			spoiler_results = spoiler_results.split('<h4 class="ipl-list-title">')[1:]
			for item in spoiler_results:
				item_dict = {}
				try:
					title = replace_html_codes(re.findall('(.+?)</h4>', item, re.DOTALL)[0])
					title = to_utf8(remove_accents(title))
					item_dict['title'] = title
				except: continue
				try:
					listings = parseDOM(item, 'li', attrs={'class': 'ipl-zebra-list__item'})
					item_dict['listings'] = []
				except: continue
				for item in listings:
					try:
						listing = replace_html_codes(re.findall('(.+?)     <div class="', item, re.DOTALL)[0])
						listing = to_utf8(remove_accents(listing))
						if not listing in item_dict['listings']: item_dict['listings'].append(listing)
					except: pass
				if not item_dict in spoiler_list: spoiler_list.append(item_dict)
		for item in to_utf8(results):
			item_dict = {}
			try:
				title = replace_html_codes(parseDOM(item, 'h4', attrs={'class': 'ipl-list-title'})[0])
				title = to_utf8(remove_accents(title))
				item_dict['title'] = title
			except: continue
			try:
				ranking = replace_html_codes(parseDOM(item, 'span', attrs={'class': 'ipl-status-pill ipl-status-pill--(.+?)'})[0])
				ranking = to_utf8(remove_accents(ranking))
				item_dict['ranking'] = ranking
			except: continue
			try:
				listings = parseDOM(item, 'li', attrs={'class': 'ipl-zebra-list__item'})
				item_dict['listings'] = []
			except: continue
			for item in listings:
				try:
					listing = replace_html_codes(re.findall('(.+?)     <div class="', item, re.DOTALL)[0])
					listing = to_utf8(remove_accents(listing))
					if not listing in item_dict['listings']: item_dict['listings'].append(listing)
				except: pass
			if item_dict: imdb_list.append(item_dict)
		if spoiler_list:
			for imdb in imdb_list:
				for spo in spoiler_list:
					if spo['title'] == imdb['title']:
						imdb['listings'].extend(spo['listings'])
		for item in imdb_list:
			item['listings'] = list(set(item['listings']))
	return (imdb_list, next_page)

def clear_imdb_cache(silent=False):
	import xbmcvfs
	try: from sqlite3 import dbapi2 as database
	except ImportError: from pysqlite2 import dbapi2 as database
	try:
		window = xbmcgui.Window(10000)
		IMDB_DATABASE = xbmc.translatePath('special://profile/addon_data/plugin.video.fen/fen_cache2.db')
		if not xbmcvfs.exists(IMDB_DATABASE): return True
		dbcon = database.connect(IMDB_DATABASE)
		dbcur = dbcon.cursor()
		dbcur.execute("SELECT id FROM fencache WHERE id LIKE 'imdb_%'")
		imdb_results = [str(i[0]) for i in dbcur.fetchall()]
		if not imdb_results: return True
		dbcur.execute("DELETE FROM fencache WHERE id LIKE 'imdb_%'")
		dbcon.commit()
		dbcon.close()
		for i in imdb_results: window.clearProperty(i)
		return True
	except: return False






