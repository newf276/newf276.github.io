# -*- coding: utf-8 -*-
import xbmc, xbmcplugin, xbmcgui, xbmcvfs
import os
from sys import argv
try: from urllib import unquote
except ImportError: from urllib.parse import unquote
import json
import re
try: from urlparse import parse_qsl
except ImportError: from urllib.parse import parse_qsl
from apis.opensubtitles_api import OpenSubtitlesAPI
from apis.trakt_api import make_trakt_slug
from modules.indicators_bookmarks import detect_bookmark, erase_bookmark
from modules.nav_utils import hide_busy_dialog, close_all_dialog, notification, volume_checker
from modules.settings_reader import get_setting
from modules.utils import sec2time
from modules.utils import local_string as ls
from modules import settings
# from modules.utils import logger

window = xbmcgui.Window(10000)

class FenPlayer(xbmc.Player):
	def __init__ (self):
		xbmc.Player.__init__(self)
		self.set_resume = settings.set_resume()
		self.set_watched = settings.set_watched()
		self.autoplay_nextep = settings.autoplay_next_episode()
		self.nextep_threshold = settings.nextep_threshold()
		self.delete_nextep_playcount = True
		self.cancel_autoplay_count = True
		self.kodi_library_resumed = True
		self.media_marked = False
		self.subs_searched = False
		self.nextep_info = None
		self.random_info = None

	def run(self, url=None, rootname=None):
		if not url: return
		# try:
		if rootname in ('video', 'music'):
			p_list = xbmc.PLAYLIST_VIDEO if rootname == 'video' else xbmc.PLAYLIST_MUSIC
			playlist = xbmc.PlayList(p_list)
			playlist.clear()
			listitem = xbmcgui.ListItem()
			listitem.setInfo(type=rootname, infoLabels={})
			playlist.add(url, listitem)
			close_all_dialog()
			return self.play(playlist)
		self.meta = json.loads(window.getProperty('fen_media_meta'))
		rootname = self.meta['rootname'] if 'rootname' in self.meta else ''
		background = self.meta.get('background', False) == True
		library_item = True if 'from_library' in self.meta else False
		if library_item: bookmark = self.bookmarkLibrary()
		else: bookmark = self.bookmarkFen()
		if bookmark == -1: return
		self.meta.update({'url': url, 'bookmark': bookmark})
		listitem = xbmcgui.ListItem(path=url)
		try:
			if not library_item: listitem.setProperty('StartPercent', str(self.meta.get('bookmark')))
			listitem.setArt({'poster': self.meta.get('poster'), 'fanart': self.meta.get('fanart'), 'banner': self.meta.get('banner'),
							'clearart': self.meta.get('clearart'), 'clearlogo': self.meta.get('clearlogo'),
							'landscape': self.meta.get('landscape'), 'discart': self.meta.get('discart')})
			listitem.setCast(self.meta['cast'])
			if self.meta['vid_type'] == 'movie':
				listitem.setUniqueIDs({'imdb': str(self.meta['imdb_id']), 'tmdb': str(self.meta['tmdb_id'])})
				listitem.setInfo(
					'video', {'mediatype': 'movie', 'trailer': str(self.meta['trailer']),
					'title': self.meta['title'], 'size': '0', 'duration': self.meta['duration'],
					'plot': self.meta['plot'], 'rating': self.meta['rating'], 'premiered': self.meta['premiered'],
					'studio': self.meta['studio'],'year': self.meta['year'], 'genre': self.meta['genre'],
					'tagline': self.meta['tagline'], 'code': self.meta['imdb_id'], 'imdbnumber': self.meta['imdb_id'],
					'director': self.meta['director'], 'writer': self.meta['writer'], 'votes': self.meta['votes']})
			elif self.meta['vid_type'] == 'episode':
				listitem.setUniqueIDs({'imdb': str(self.meta['imdb_id']), 'tmdb': str(self.meta['tmdb_id']), 'tvdb': str(self.meta['tvdb_id'])})
				listitem.setInfo(
					'video', {'mediatype': 'episode', 'trailer': str(self.meta['trailer']), 'title': self.meta['ep_name'], 'imdbnumber': self.meta['imdb_id'],
					'tvshowtitle': self.meta['title'], 'size': '0', 'plot': self.meta['plot'], 'year': self.meta['year'], 'votes': self.meta['votes'],
					'premiered': self.meta['premiered'], 'studio': self.meta['studio'], 'genre': self.meta['genre'], 'season': int(self.meta['season']),
					'episode': int(self.meta['episode']), 'duration': str(self.meta['duration']), 'rating': self.meta['rating']})
			try:
				window.clearProperty('script.trakt.ids')
				trakt_ids = {'tmdb': self.meta['tmdb_id'], 'imdb': str(self.meta['imdb_id']), 'slug': make_trakt_slug(self.meta['title'])}
				if self.meta['vid_type'] == 'episode': trakt_ids['tvdb'] = self.meta['tvdb_id']
				window.setProperty('script.trakt.ids', json.dumps(trakt_ids))
			except: pass
			# except Exception: pass
			if library_item and not background: xbmcplugin.setResolvedUrl(int(argv[1]), True, listitem)
			else: self.play(url, listitem)
			self.monitor()
		except Exception: return

	def bookmarkFen(self):
		season = self.meta.get('season', '')
		episode = self.meta.get('episode', '')
		if season == 0: season = ''
		if episode == 0: episode = ''
		bookmark = 0
		try: resume_point, curr_time = detect_bookmark(self.meta['vid_type'], self.meta['media_id'], season, episode)
		except: resume_point = 0
		resume_check = float(resume_point)
		if resume_check > 0:
			percent = str(resume_point)
			raw_time = float(curr_time)
			_time = sec2time(raw_time, n_msec=0)
			bookmark = self.getResumeStatus(_time, percent, bookmark)
			if bookmark == 0: erase_bookmark(self.meta['vid_type'], self.meta['media_id'], season, episode)
		return bookmark

	def bookmarkLibrary(self):
		from modules.kodi_library import get_bookmark_kodi_library
		season = self.meta.get('season', '')
		episode = self.meta.get('episode', '')
		if season == 0: season = ''
		if episode == 0: episode = ''
		bookmark = 0
		try: curr_time = get_bookmark_kodi_library(self.meta['vid_type'], self.meta['media_id'], season, episode)
		except: curr_time = 0.0
		if curr_time > 0:
			self.kodi_library_resumed = False
			_time = sec2time(curr_time, n_msec=0)
			bookmark = self.getResumeStatus(_time, curr_time, bookmark)
			if bookmark == 0: erase_bookmark(self.meta['vid_type'], self.meta['media_id'], season, episode)
		return bookmark

	def getResumeStatus(self, _time, percent, bookmark):
		if settings.auto_resume(): return percent
		dialog = xbmcgui.Dialog()
		xbmc.sleep(600)
		choice = dialog.contextmenu([ls(32790) % _time, ls(32791)])
		return percent if choice == 0 else bookmark if choice == 1 else -1

	def monitor(self):
		self.library_setting = 'library' if 'from_library' in self.meta else None
		self.random_episodes = True if 'played_eps' in self.meta else False
		self.autoplay_next_episode = True if (self.meta['vid_type'] == 'episode' and self.autoplay_nextep and not 'random_play' in self.meta) else False
		while not self.isPlayingVideo():
			xbmc.sleep(100)
		close_all_dialog()
		volume_checker()
		while self.isPlayingVideo():
			try:
				xbmc.sleep(1000)
				self.total_time = self.getTotalTime()
				self.curr_time = self.getTime()
				self.current_point = round(float(self.curr_time/self.total_time*100),1)
				if self.current_point >= self.set_watched and not self.media_marked:
					self.mediaWatchedMarker()
				if self.random_episodes:
					if not self.random_info:
						if self.current_point >= self.nextep_threshold:
							self.randomPrep()
				elif self.autoplay_next_episode:
					if self.current_point >= self.nextep_threshold:
						if not self.nextep_info:
							self.nextEpPrep()
						else: pass
				if not self.kodi_library_resumed:
					if self.curr_time > 0.0:
						self.kodi_library_resumed = True
						self.seekTime(float(self.meta.get('bookmark', 0)))
			except: pass
			if not self.subs_searched: self.fetch_subtitles()
		if self.cancel_autoplay_count: window.clearProperty('fen_total_autoplays')
		if not self.media_marked: self.mediaWatchedMarker()

	def mediaWatchedMarker(self):
		try:
			if self.set_resume < self.current_point < self.set_watched:
				from modules.indicators_bookmarks import set_bookmark
				self.media_marked = True
				set_bookmark(self.meta['vid_type'], self.meta['media_id'], self.curr_time, self.total_time, self.meta.get('season', ''), self.meta.get('episode', ''))
			elif self.current_point > self.set_watched:
				self.media_marked = True
				if self.meta['vid_type'] == 'movie':
					from modules.indicators_bookmarks import mark_movie_as_watched_unwatched, get_watched_info_movie
					watched_function = mark_movie_as_watched_unwatched
					watched_update = get_watched_info_movie
					watched_params = {"mode": "mark_movie_as_watched_unwatched", "action": 'mark_as_watched',
					"media_id": self.meta['media_id'], "title": self.meta['title'], "year": self.meta['year'],
					"refresh": 'false', 'from_playback': 'true'}
				else:
					from modules.indicators_bookmarks import mark_episode_as_watched_unwatched, get_watched_info_tv
					watched_function = mark_episode_as_watched_unwatched
					watched_update = get_watched_info_tv
					watched_params = {"mode": "mark_episode_as_watched_unwatched", "action": "mark_as_watched",
					"season": self.meta['season'], "episode": self.meta['episode'], "media_id": self.meta['media_id'],
					"title": self.meta['title'], "year": self.meta['year'], "imdb_id": self.meta['imdb_id'],
					"tvdb_id": self.meta["tvdb_id"], "refresh": 'false', 'from_playback': 'true'}
				watched_function(watched_params)
				xbmc.sleep(1000)
				watched_info = watched_update()[0]
		except: pass

	def randomPrep(self):
		from modules.random_play import play_fetch_random, play_random
		self.random_info = play_fetch_random(self.meta['vid_type'], json.dumps(self.meta), default_season=self.meta.get('default_season', 0),
											 played_eps=self.meta['played_eps'], first_run=False)
		if not self.random_info.get('pass', False):
			play_random(self.random_info)

	def nextEpPrep(self):
		from indexers.next_episode import nextep_playback_info, nextep_execute
		self.nextep_info = nextep_playback_info(self.meta['tmdb_id'], int(self.meta['season']), int(self.meta['episode']), self.library_setting)
		if not self.nextep_info.get('pass', False):
			self.cancel_autoplay_count = False
			nextep_execute(self.nextep_info)

	def fetch_subtitles(self):
		self.subs_searched = True
		season = int(self.meta['season']) if self.meta['vid_type'] == 'episode' else None
		episode = int(self.meta['episode']) if self.meta['vid_type'] == 'episode' else None
		try: Subtitles().get(self.meta['title'], self.meta['imdb_id'], season, episode)
		except: pass

	def refresh_container(self):
		if self.media_marked:
			if not any([self.random_episodes, self.autoplay_next_episode]):
				xbmc.sleep(500)
				xbmc.executebuiltin("Container.Refresh")

	def onAVStarted(self):
		try: close_all_dialog()
		except: pass

	def onPlayBackStarted(self):
		try: close_all_dialog()
		except: pass

	# def onPlayBackEnded(self):
	#     try: self.playlist.clear()
	#     except: pass

	# def onPlayBackStopped(self):
	#     try: self.playlist.clear()
	#     except: pass

	def playAudioAlbum(self, t_files=None, name=None, from_seperate=False):
		import os
		from modules.utils import clean_file_name, batch_replace, to_utf8
		from modules.nav_utils import setView
		__handle__ = int(argv[1])
		icon_directory = settings.get_theme()
		default_furk_icon = os.path.join(icon_directory, 'furk.png')
		formats = ('.3gp', ''), ('.aac', ''), ('.flac', ''), ('.m4a', ''), ('.mp3', ''), \
		('.ogg', ''), ('.raw', ''), ('.wav', ''), ('.wma', ''), ('.webm', ''), ('.ra', ''), ('.rm', '')
		params = dict(parse_qsl(argv[2].replace('?','')))
		furk_files_list = []
		playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
		playlist.clear()
		if from_seperate: t_files = [i for i in t_files if clean_file_name(i['path']) == params.get('item_path')]
		for item in t_files:
			try:
				name = item['path'] if not name else name
				if not 'audio' in item['ct']: continue
				url = item['url_dl']
				track_name = clean_file_name(batch_replace(to_utf8(item['name']), formats))
				listitem = xbmcgui.ListItem(track_name)
				listitem.setThumbnailImage(default_furk_icon)
				listitem.setInfo(type='music',infoLabels={'title': track_name, 'size': int(item['size']), 'album': clean_file_name(batch_replace(to_utf8(name), formats)),'duration': item['length']})
				listitem.setProperty('mimetype', 'audio/mpeg')
				playlist.add(url, listitem)
				if from_seperate: furk_files_list.append((url, listitem, False))
			except: pass
		self.play(playlist)
		if from_seperate:
			xbmcplugin.addDirectoryItems(__handle__, furk_files_list, len(furk_files_list))
			setView('view.furk_files')
			xbmcplugin.endOfDirectory(__handle__)

class Subtitles(xbmc.Player):
	def __init__(self):
		self.opensubtitles = OpenSubtitlesAPI()
		self.auto_enable = get_setting('subtitles.auto_enable')
		self.subs_action = get_setting('subtitles.subs_action')
		self.settings_language1 = get_setting('subtitles.language')
		self.settings_language2 = get_setting('subtitles.language2')
		self.manual_selection = True
		self.show_notification = get_setting('subtitles.show_notification')
		self.quality = ['bluray', 'hdrip', 'brrip', 'bdrip', 'dvdrip', 'webdl', 'webrip', 'webcap', 'web', 'hdtv', 'hdrip']
		self.language_dict = {'None': None,
			'Afrikaans': 'afr', 'Albanian': 'alb', 'Arabic': 'ara', 'Armenian': 'arm',
			'Basque': 'baq', 'Bengali': 'ben', 'Bosnian': 'bos', 'Breton': 'bre',
			'Bulgarian': 'bul', 'Burmese': 'bur', 'Catalan': 'cat', 'Chinese': 'chi',
			'Croatian': 'hrv', 'Czech': 'cze', 'Danish': 'dan', 'Dutch': 'dut',
			'English': 'eng', 'Esperanto': 'epo', 'Estonian': 'est', 'Finnish': 'fin',
			'French': 'fre', 'Galician': 'glg', 'Georgian': 'geo', 'German': 'ger',
			'Greek': 'ell', 'Hebrew': 'heb', 'Hindi': 'hin', 'Hungarian': 'hun',
			'Icelandic': 'ice', 'Indonesian': 'ind', 'Italian': 'ita', 'Japanese': 'jpn',
			'Kazakh': 'kaz', 'Khmer': 'khm', 'Korean': 'kor', 'Latvian': 'lav',
			'Lithuanian': 'lit', 'Luxembourgish': 'ltz', 'Macedonian': 'mac', 'Malay': 'may',
			'Malayalam': 'mal', 'Manipuri': 'mni', 'Mongolian': 'mon', 'Montenegrin': 'mne',
			'Norwegian': 'nor', 'Occitan': 'oci', 'Persian': 'per', 'Polish': 'pol',
			'Portuguese': 'por', 'Portuguese(Brazil)': 'pob', 'Romanian': 'rum',
			'Russian': 'rus', 'Serbian': 'scc', 'Sinhalese': 'sin', 'Slovak': 'slo',
			'Slovenian': 'slv', 'Spanish': 'spa', 'Swahili': 'swa', 'Swedish': 'swe',
			'Syriac': 'syr', 'Tagalog': 'tgl', 'Tamil': 'tam', 'Telugu': 'tel',
			'Thai': 'tha', 'Turkish': 'tur', 'Ukrainian': 'ukr', 'Urdu': 'urd'}
		self.language1 = self.language_dict[self.settings_language1]
		self.language2 = self.language_dict[self.settings_language2]

	def get(self, query, imdb_id, season, episode):
		def _notification(line, _time=3500):
			if self.show_notification: return notification(line, _time)
			else: return
		def _video_file_subs():
			try: available_sub_language = xbmc.Player().getSubtitles()
			except: available_sub_language = ''
			if available_sub_language in (self.language1, self.language2):
				if self.auto_enable == 'true': xbmc.Player().showSubtitles(True)
				_notification(ls(32852))
				return True
			return False
		def _downloaded_subs():
			files = xbmcvfs.listdir(subtitle_path)[1]
			if len(files) > 0:
				match_lang1 = None
				match_lang2 = None
				files = [i for i in files if i.endswith('.srt')]
				for item in files:
					if item == search_filename:
						match_lang1 = item
						break
					if search_filename2:
						if item == search_filename2:
							match_lang2 = item
				final_match = match_lang1 if match_lang1 else match_lang2 if match_lang2 else None
				if final_match:
					subtitle = os.path.join(subtitle_path, final_match)
					_notification(ls(32792))
					return subtitle
			return False
		def _searched_subs():
			chosen_sub = None
			search_language = self.language1
			result = self.opensubtitles.search(query, imdb_id, search_language, season, episode)
			if not result or len(result) == 0:
				search_language = self.language2
				if self.language2 == None:
					_notification(ls(32793))
					return False
				_notification(ls(32794), _time=1500)
				result = self.opensubtitles.search(query, imdb_id, self.language2, season, episode)
				if not result or len(result) == 0:
					_notification(ls(32793))
					return False
			try: video_path = self.getPlayingFile()
			except: video_path = ''
			if '|' in video_path: video_path = video_path.split('|')[0]
			video_path = os.path.basename(video_path)
			if self.subs_action == '1':
				from modules.utils import selection_dialog
				xbmc.Player().pause()
				choices = [i for i in result if i['SubLanguageID'] == search_language and i['SubSumCD'] == '1']
				dialog_list = ['%02d | [B]%s[/B] |[I]%s[/I]' % (c, i['SubLanguageID'].upper(), i['MovieReleaseName']) for c, i in enumerate(choices, 1)]
				string = '%s - %s' % (ls(32246).upper(), video_path)
				chosen_sub = selection_dialog(dialog_list, choices, string)
				xbmc.Player().pause()
				if not chosen_sub:
					_notification(ls(32736), _time=1500)
					return False
			else:
				try: chosen_sub = [i for i in result if i['MovieReleaseName'].lower() in video_path.lower() and i['SubLanguageID'] == search_language and i['SubSumCD'] == '1'][0]
				except: pass
				if not chosen_sub:
					fmt = re.split('\.|\(|\)|\[|\]|\s|\-', video_path)
					fmt = [i.lower() for i in fmt]
					fmt = [i for i in fmt if i in self.quality]
					if season and fmt == '': fmt = 'hdtv'
					result = [i for i in result if i['SubSumCD'] == '1']
					filter = [i for i in result if i['SubLanguageID'] == search_language and any(x in i['MovieReleaseName'].lower() for x in fmt) and any(x in i['MovieReleaseName'].lower() for x in self.quality)]
					filter += [i for i in result if any(x in i['MovieReleaseName'].lower() for x in self.quality)]
					filter += [i for i in result if i['SubLanguageID'] == search_language]
					if len(filter) > 0: chosen_sub = filter[0]
					else: chosen_sub = result[0]
			try: lang = xbmc.convertLanguage(chosen_sub['SubLanguageID'], xbmc.ISO_639_2)
			except: lang = chosen_sub['SubLanguageID']
			insert_name = sub_filename + '_%s.srt' % lang
			subtitle = os.path.join(subtitle_path, insert_name)
			download_url = chosen_sub['SubDownloadLink']
			content = self.opensubtitles.download(download_url)
			file = xbmcvfs.File(subtitle, 'w')
			file.write(str(content))
			file.close()
			xbmc.sleep(1000)
			return subtitle
		if self.subs_action == '2': return
		xbmc.sleep(2500)
		imdb_id = re.sub('[^0-9]', '', imdb_id)
		subtitle_path = xbmc.translatePath('special://temp/')
		sub_filename = 'FENSubs_%s_%s_%s' % (imdb_id, season, episode) if season else 'FENSubs_%s' % imdb_id
		search_filename = sub_filename + '_%s.srt' % self.language1
		if self.language2: search_filename2 = sub_filename + '_%s.srt' % self.language2
		else: search_filename2 = None
		subtitle = _video_file_subs()
		if subtitle: return
		subtitle = _downloaded_subs()
		if subtitle: return xbmc.Player().setSubtitles(subtitle)
		subtitle = _searched_subs()
		if subtitle: return xbmc.Player().setSubtitles(subtitle)






