# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import os
from sys import argv
try: from urllib import unquote
except ImportError: from urllib.parse import unquote
from apis import simplejson as json
from apis import tmdb_api as TMDb
from modules.nav_utils import build_url, add_dir, setView, notification
from modules.utils import local_string as ls
from modules import settings
# from modules.utils import logger

dialog = xbmcgui.Dialog()
addon_dir = xbmc.translatePath('special://home/addons/plugin.video.fen')

icon = os.path.join(addon_dir, "icon.png")
fanart = os.path.join(addon_dir, "fanart.png")

icon_directory = settings.get_theme()

class People():
	def __init__(self, actor_info=None):
		self.image_base = 'https://image.tmdb.org/t/p/%s%s'
		if actor_info:
			self.actor_id = actor_info[0]
			self.choose_id = True if self.actor_id == 'None' else False
			self.actor_name = actor_info[1]
			self.actor_image = actor_info[2]
			try: self.page_no = actor_info[3]
			except: self.page_no = 1
			try: self.count = actor_info[4]
			except: self.count = 0
			self.__handle__ = int(argv[1])

	def main(self):
		params = {'actor_id': self.actor_id, 'actor_name': self.actor_name, 'actor_image': self.actor_image, 'page_no': self.page_no}
		menus = [(ls(32028), 'people_searche.media_results'), 
		(ls(32029), 'people_search.media_results'),
		('%s %s' % (ls(32028), ls(32796)), 'people_search.media_results'),
		(ls(32797), 'people_search.biography_results'),
		(ls(32798), 'people_search.image_results'),
		('%s %s' % (ls(33045), ls(32798)), 'people_search.tagged_image_results'),
		('%ss' % ls(32491), 'people_search.video_results')]
		if settings.addon_installed('script.extendedinfo'):
			menus.append((ls(32610), 'people_search.extended_info'))
		for menu_item in menus:
			if menu_item[0] in (ls(32797), ls(32610)): isFolder = False
			else: isFolder = True
			if menu_item[0] == ls(32028): params['media_type'] = 'movies'
			elif menu_item[0] == ls(32029): params['media_type'] = 'tvshows'
			if menu_item[0] == '%s %s' % (ls(32028), ls(32796)): params['media_type'] = 'movies_directed'
			self._add_dir(menu_item[0], menu_item[1], params, isFolder=isFolder)
		xbmcplugin.setContent(self.__handle__, 'files')
		xbmcplugin.endOfDirectory(self.__handle__)
		setView('view.main')

	def search(self):
		if self.choose_id:
			self.query = self._get_query()
			if not self.query: return
			self.actor_id, self.actor_name, self.actor_image = self._get_actor_details()
			if not self.actor_id: return notification(ls(32760))
		self.main()

	def extended_info(self):
		xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedactorinfo,id=%s)' % self.actor_id)

	def biography_results(self):
		from modules.utils import calculate_age
		def _make_biography():
			age = None
			name = bio_info.get('name')
			place_of_birth = bio_info.get('place_of_birth')
			biography = bio_info.get('biography')
			birthday = bio_info.get('birthday')
			deathday = bio_info.get('deathday')
			if deathday: age = calculate_age(birthday, '%Y-%m-%d', deathday)
			elif birthday: age = calculate_age(birthday, '%Y-%m-%d')
			text = '\n[COLOR dodgerblue]%s[/COLOR] %s' % (ls(32823), name)
			if place_of_birth: text += '\n\n[COLOR dodgerblue]%s[/COLOR] %s' % (ls(32824), place_of_birth)
			if birthday: text += '\n\n[COLOR dodgerblue]%s[/COLOR] %s' % (ls(32825), birthday)
			if deathday: text += '\n\n[COLOR dodgerblue]%s[/COLOR] %s, aged %s' % (ls(32826), deathday, age)
			elif age: text += '\n\n[COLOR dodgerblue]%s[/COLOR] %s' % (ls(32827), age)
			if biography: text += '\n\n[COLOR dodgerblue]%s[/COLOR]\n%s' % (ls(32828), biography)
			return text
		dialog = xbmcgui.Dialog()
		bio_info = TMDb.tmdb_people_biography(self.actor_id)
		if bio_info.get('biography', None) in ('', None):
			bio_info = TMDb.tmdb_people_biography(self.actor_id, 'en')
		if not bio_info: return notification(ls(32490))
		text = _make_biography()
		return dialog.textviewer('Fen', text)

	def image_results(self):
		from indexers.images import people_image_results
		people_image_results(self.actor_name, self.actor_id, self.actor_image, self.page_no, self.count)

	def tagged_image_results(self):
		from indexers.images import people_tagged_image_results
		people_tagged_image_results(self.actor_name, self.actor_id, self.actor_image, self.page_no, self.count)

	def video_results(self):
		from apis.imdb_api import imdb_people_id, imdb_videos
		imdb_id = people_get_imdb_id(self.actor_name, self.actor_id)
		try: videos_list = imdb_videos(imdb_id)
		except: return
		for item in videos_list:
			title = item['title']
			poster = item['poster']
			url_params = {'mode': 'imdb_videos_choice', 'videos': json.dumps(item['videos'])}
			url = build_url(url_params)
			listitem = xbmcgui.ListItem(title)
			listitem.setArt({'icon': poster, 'poster': poster, 'thumb': poster, 'fanart': fanart})
			xbmcplugin.addDirectoryItem(self.__handle__, url, listitem, isFolder=False)
		xbmcplugin.setContent(self.__handle__, 'images')
		xbmcplugin.endOfDirectory(self.__handle__)
		setView('view.images', 'images')

	def media_results(self, media_type, page_no, letter):
		from indexers.movies import Movies
		from indexers.tvshows import TVShows
		from modules.nav_utils import paginate_list
		from modules.utils import title_key
		def _add_misc_dir(url_params, list_name=ls(32799), info=ls(32800), iconImage='item_next.png'):
			listitem = xbmcgui.ListItem(list_name, iconImage=os.path.join(icon_directory, iconImage))
			listitem.setArt({'fanart': fanart})
			listitem.setInfo('video', {'title': list_name, 'plot': info})
			if url_params['mode'] == 'build_navigate_to_page': listitem.addContextMenuItems([(ls(32784),"RunPlugin(%s)" % build_url({'mode': 'toggle_jump_to'}))])
			xbmcplugin.addDirectoryItem(handle=self.__handle__, url=build_url(url_params), listitem=listitem, isFolder=True)
		not_widget = xbmc.getInfoLabel('Container.PluginName')
		cache_page_string = 'people_search_%s_%s' % (media_type, self.actor_id)
		limit = 20
		ignore_articles = settings.ignore_articles()
		try:
			builder = Movies if media_type in ('movies', 'movies_directed') else TVShows
			function = TMDb.tmdb_movies_actor_roles if media_type == 'movies' else TMDb.tmdb_tv_actor_roles if media_type == 'tvshows' else TMDb.tmdb_movies_crew
			content = 'movies' if media_type in ('movies', 'movies_directed') else 'tvshows'
			key = 'title' if media_type in ('movies', 'movies_directed') else 'name'
			result = function(self.actor_id)
			data = sorted(result, key=lambda k: title_key(k[key], ignore_articles))
			data = result
			original_list = [{'media_id': i['id'], 'title': i[key]} for i in data]
			paginated_list, total_pages = paginate_list(original_list, page_no, letter, limit)
			media_list = [i['media_id'] for i in paginated_list]
			params = {'list': media_list, 'action': 'people_search_%s' % media_type}
			builder(params).worker()
			if total_pages > page_no: _add_misc_dir({'mode': 'people_search.media_results', 'media_type': media_type, 'actor_id': self.actor_id, 'actor_name': self.actor_name, 'actor_image': self.actor_image, 'new_page': str(page_no + 1), 'new_letter': letter})
			xbmcplugin.setContent(self.__handle__, content)
			xbmcplugin.endOfDirectory(self.__handle__)
			setView('view.%s' % content, content)
		except: notification(ls(32760), 3000)

	def _get_query(self):
		if self.actor_name in ('None', '', None): actor_name = dialog.input('Fen', type=xbmcgui.INPUT_ALPHANUM)
		else: actor_name = self.actor_name
		return unquote(actor_name)

	def _get_actor_details(self):
		from modules.history import add_to_search_history
		try: actors = TMDb.tmdb_people_info(self.query)
		except: actors = None
		if not actors: return None, None, None
		actor_list = []
		if len(actors) == 1:
			actors = actors[0]
			actor_id = actors['id']
			actor_name = actors['name']
			try: image_id = actors['profile_path']
			except: image_id = None
			if not image_id: actor_image = os.path.join(icon_directory, 'genre_family.png')
			else: actor_image = 'https://image.tmdb.org/t/p/h632/%s' % image_id
		else:
			for item in actors:
				known_for_list = [i.get('title', 'NA') for i in item['known_for']]
				known_for_list = [i for i in known_for_list if not i == 'NA']
				known_for = '[I]%s[/I]' % ', '.join(known_for_list) if known_for_list else '[I]..........[/I]'
				listitem = xbmcgui.ListItem(item['name'], known_for)
				image = 'https://image.tmdb.org/t/p/w185/%s' % item['profile_path'] if item['profile_path'] else os.path.join(icon_directory, 'genre_family.png')
				listitem.setArt({'icon': image})
				listitem.setProperty('id', str(item['id']))
				listitem.setProperty('name', str(item['name']))
				listitem.setProperty('image', str(image.replace('w185', 'h632')))
				actor_list.append(listitem)
			selection = dialog.select('Fen', actor_list, useDetails=True)
			if selection >= 0:
				actor_id = int(actor_list[selection].getProperty('id'))
				actor_name = actor_list[selection].getProperty('name')
				actor_image = actor_list[selection].getProperty('image')
			else: return None, None, None
		add_to_search_history(actor_name, 'people_queries')
		return actor_id, actor_name, actor_image

	def extras_person_data(self, person_name, tmdb_api):
		if not tmdb_api: tmdb_api = settings.tmdb_api_check()
		from apis.tmdb_api import get_tmdb
		from caches.fen_cache import cache_object
		if person_name:
			self.actor_name = person_name
			self.actor_image = None
		try: self.actor_name = self.actor_name.decode('utf-8')
		except: pass
		string = "%s_%s" % ('tmdb_movies_people_search_actor_data', self.actor_name)
		url = 'https://api.themoviedb.org/3/search/person?api_key=%s&language=en-US&query=%s' % (tmdb_api, self.actor_name)
		result = cache_object(get_tmdb, string, url, 4)
		result = result['results']
		self.actor_id = [item['id'] for item in result][0]
		if not self.actor_image: self.actor_image = [self.image_base % ('original', item['profile_path']) for item in result][0]
		self.main()

	def _add_dir(self, list_name, mode, url_params, isFolder=True):
		url_params['mode'] = mode
		actor_id = url_params['actor_id']
		actor_name = url_params['actor_name']
		actor_image = url_params['actor_image']
		list_name = '[B]%s :[/B] %s' % (actor_name.upper(), list_name)
		info = url_params.get('info', '')
		url = build_url(url_params)
		listitem = xbmcgui.ListItem(list_name)
		listitem.setArt({'icon': actor_image, 'poster': actor_image, 'thumb': actor_image, 'fanart': fanart, 'banner': actor_image, 'landscape': actor_image})
		listitem.setInfo('video', {'title': list_name, 'plot': info})
		xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=listitem, isFolder=isFolder)
		
def popular_people(page_no):
	from apis.tmdb_api import tmdb_popular_people
	from modules.nav_utils import add_dir
	try: page_no = int(page_no)
	except: page_no = 1
	__handle__ = int(argv[1])
	data = tmdb_popular_people(page_no)
	content_type = 'addons'
	extended_info_installed = settings.addon_installed('script.extendedinfo')
	for item in data['results']:
		actor_poster = "https://image.tmdb.org/t/p/w185%s" % item['profile_path'] if item['profile_path'] else os.path.join(icon_directory, 'genre_family.png')
		url_params = {'mode': 'people_search.main', 'actor_id': item['id'], 'actor_name': item['name'], 'actor_image': actor_poster.replace('w185', 'h632')}
		url = build_url(url_params)
		listitem = xbmcgui.ListItem(item['name'])
		listitem.setArt({'icon': actor_poster, 'poster': actor_poster, 'thumb': actor_poster, 'fanart': fanart, 'banner': actor_poster})
		if extended_info_installed:
			cm = [("[B]%s[/B]" % ls(32610), 'RunScript(script.extendedinfo,info=extendedactorinfo,id=%s)' % item['id'])]
			listitem.addContextMenuItems(cm)
		xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
	if data['page'] < data['total_pages']:
		params = {'mode': 'build_popular_people', 'new_page': str(int(data['page']) + 1), 'foldername': 'popular_people'}
		add_dir(params, ls(32799), iconImage='item_next.png', fanartImage=fanart, isFolder=True)
	xbmcplugin.setContent(__handle__, 'images')
	xbmcplugin.endOfDirectory(__handle__)
	setView('view.images', 'images')
