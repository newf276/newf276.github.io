# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import json
from modules.nav_utils import show_busy_dialog, hide_busy_dialog, build_url, toggle_setting
from modules.utils import selection_dialog, multiselect_dialog
from modules.utils import local_string as ls
from modules import settings
from modules.settings_reader import get_setting, set_setting
# from modules.utils import logger

def similar_recommendations_choice(params):
	from modules.utils import selection_dialog
	from tikimeta import retrieve_user_info
	db_type = params['db_type']
	meta_type = 'movie' if db_type  =='movies' else 'tvshow'
	try: meta_user_info = json.loads(params['meta_user_info'])
	except: meta_user_info = retrieve_user_info()
	dl = [ls(32592), ls(32593)]
	fl = ['trakt_%s_related' % db_type, 'tmdb_%s_recommendations' % db_type]
	mode = 'build_%s_list' % meta_type
	choice = selection_dialog(dl, fl)
	if not choice: return
	try:
		sim_recom_params = {'mode': mode, 'action': choice, 'sim_recom_tmdb': params.get('sim_recom_tmdb'), 'sim_recom_imdb': params.get('sim_recom_imdb'), 'sim_recom_name': params.get('sim_recom_name'), 'from_search': params.get('from_search')}
		xbmc.executebuiltin('Container.Update(%s)' % build_url(sim_recom_params))
	except: return

def show_all_actors_choice(media_rootname, full_cast):
	import os
	import json
	dialog = xbmcgui.Dialog()
	tmdb_api = settings.tmdb_api_check()
	icon_directory = settings.get_theme()
	actor_list = []
	image_base = 'https://image.tmdb.org/t/p/%s%s'
	for item in json.loads(full_cast):
		name = item['name']
		role = '[I]%s[/I]' % item['role']
		thumbnail = item['thumbnail']
		if thumbnail:
			raw_image_path = '/' + thumbnail.split('/')[-1]
			image = image_base % ('h632', raw_image_path)
		else:
			image = thumbnail =  os.path.join(icon_directory, 'genre_family.png')
		listitem = xbmcgui.ListItem(name, role)
		listitem.setArt({'icon': thumbnail})
		listitem.setProperty('name', name)
		actor_list.append(listitem)
	selection = dialog.select('Fen', actor_list, useDetails=True)
	if selection < 0: return
	actor_name = actor_list[selection].getProperty('name')
	extras_person_params = {'mode': 'people_search.extras_person_data', 'person_name': actor_name, 'tmdb_api': tmdb_api}
	xbmc.executebuiltin('Container.Update(%s)' % build_url(extras_person_params))

def imdb_reviews_choice(imdb_id, rootname, poster):
	from apis.imdb_api import imdb_reviews
	show_busy_dialog()
	reviews_info = imdb_reviews(imdb_id)
	total_results = len(reviews_info)
	hide_busy_dialog()
	if total_results == 0:
		from modules.nav_utils import notification
		return notification(ls(32760), 3500)
	dialog = xbmcgui.Dialog()
	review_list = []
	for count, item in enumerate(reviews_info, 1):
		if item['spoiler']: line1 = '%02d. [COLOR red][%s][/COLOR]  %s %s' % (count, ls(32985), item['rating'], item['title'])
		else: line1 = '%02d.  %s %s' % (count, item['rating'], item['title'])
		line2 = '[I]%s...[/I]' % item['content'][:100]
		listitem = xbmcgui.ListItem(line1, line2)
		listitem.setArt({'icon': poster})
		review_list.append(listitem)
	selection = dialog.select('Fen', review_list, useDetails=True)
	if selection >= 0:
		chosen_review = reviews_info[selection]
	else: return
	content = '[B][I]%s - %s - %s[/I][/B]\n\n%s' % (chosen_review['rating'], chosen_review['date'], chosen_review['title'], chosen_review['content'])
	dialog.textviewer(rootname, content)
	if total_results > 1: return imdb_reviews_choice(imdb_id, rootname, poster)

def imdb_trivia_choice(imdb_id, rootname, poster, content):
	from apis.imdb_api import imdb_trivia
	show_busy_dialog()
	trivia_info = imdb_trivia(imdb_id, content)
	total_results = len(trivia_info)
	hide_busy_dialog()
	if total_results == 0:
		from modules.nav_utils import notification
		return notification(ls(32760), 3500)
	dialog = xbmcgui.Dialog()
	trivia_list = []
	for count, item in enumerate(trivia_info, 1):
		if xbmc.getSkinDir() in ('skin.aeon.nox.silvo', 'skin.atlas'):
			line1 = '%s %02d:   [I]%s...[/I]' % (content.upper(), count, item[:55])
			line2 = ''
		else:
			line1 = '%s %02d.' % (content.upper(), count)
			line2 = '[I]%s...[/I]' % item[:100]
		listitem = xbmcgui.ListItem(line1, line2)
		listitem.setArt({'icon': poster})
		trivia_list.append(listitem)
	selection = dialog.select('Fen', trivia_list, useDetails=True)
	if selection >= 0:
		chosen_trivia = trivia_info[selection]
	else: return
	dialog.textviewer(rootname, chosen_trivia)
	if total_results > 1: return imdb_trivia_choice(imdb_id, rootname, poster, content)

def imdb_parentsguide_choice(imdb_id, rootname):
	import os
	from apis.imdb_api import imdb_parentsguide
	show_busy_dialog()
	icon_directory = settings.get_theme()
	parentsguide_info = imdb_parentsguide(imdb_id)
	total_results = len(parentsguide_info)
	hide_busy_dialog()
	if total_results == 0:
		from modules.nav_utils import notification
		return notification(ls(32760), 3500)
	levels = {'mild': ls(32996), 'moderate': ls(32997), 'severe': ls(32998)}
	inputs = {'Sex & Nudity': (ls(32990), 'porn.png'), 'Violence & Gore': (ls(32991), 'genre_war.png'), 'Profanity': (ls(32992), 'bad_language.png'),
			 'Alcohol, Drugs & Smoking': (ls(32993), 'drugs_alcohol.png'), 'Frightening & Intense Scenes': (ls(32994), 'genre_horror.png')}
	dialog = xbmcgui.Dialog()
	parentsguide_list = []
	for item in parentsguide_info:
		if xbmc.getSkinDir() in ('skin.aeon.nox.silvo', 'skin.atlas'):
			line1 = inputs[item['title']][0]
			if item['listings']: line1 += ' (x%02d)' % len(item['listings'])
			line1 += ':  [B]%s[/B]' % levels[item['ranking'].lower()].upper()
			line2 = ''
		else:
			line1 = inputs[item['title']][0]
			if item['listings']: line1 += ' (x%02d)' % len(item['listings'])
			line2 = '[B]%s[/B]' % levels[item['ranking'].lower()].upper()
		icon = os.path.join(icon_directory, inputs[item['title']][1])
		listitem = xbmcgui.ListItem(line1, line2)
		listitem.setArt({'icon': icon})
		parentsguide_list.append(listitem)
	selection = dialog.select(rootname, parentsguide_list, useDetails=True)
	if selection >= 0:
		chosen_parentsguide = parentsguide_info[selection]
	else: return
	if not chosen_parentsguide['listings']: return imdb_parentsguide_choice(imdb_id, rootname)
	text = '\n\n'.join(['%02d. %s' % (count, i) for count, i in enumerate(chosen_parentsguide['listings'], 1)])
	dialog.textviewer('%s - %s' % (inputs[chosen_parentsguide['title']][0], levels[chosen_parentsguide['ranking'].lower()].upper()), text)
	if total_results > 1: return imdb_parentsguide_choice(imdb_id, rootname)

def imdb_videos_choice(videos):
	videos = json.loads(videos)
	videos = sorted(videos, key=lambda x: x['quality_rank'])
	dl = [i['quality'] for i in videos]
	fl = [i['url'] for i in videos]
	choice = selection_dialog(dl, fl)
	if not choice: return
	from modules.player import FenPlayer
	FenPlayer().run(choice, 'video')

def display_plot(heading, plot_text):
	xbmcgui.Dialog().textviewer(heading, plot_text)

def set_quality(quality_setting):
	include = ls(32188)
	setting = 'autoplay_quality' if quality_setting == 'autoplay' else 'results_quality'
	dl = ['%s SD' % include, '%s 720p' % include, '%s 1080p' % include, '%s 4K' % include]
	fl = ['SD', '720p', '1080p', '4K']
	try: preselect = [fl.index(i) for i in get_setting(setting).split(', ')]
	except: preselect = []
	filters = multiselect_dialog('Fen', dl, fl, preselect)
	if filters is None: return
	if filters == []:
		xbmcgui.Dialog().ok('Fen', '', ls(32574))
		return set_quality(quality_setting)
	from modules.nav_utils import toggle_setting
	toggle_setting(setting, ', '.join(filters))

def enable_scrapers():
	from modules.nav_utils import toggle_setting
	scrapers = ['external', 'furk', 'easynews', 'rd-cloud', 'pm-cloud', 'ad-cloud', 'local', 'downloads', 'folders']
	scraper_names = [ls(32118).upper(), ls(32069).upper(), ls(32070).upper(), ls(32098).upper(), ls(32097).upper(), ls(32099).upper(), ls(32100).upper(), ls(32107).upper(), ls(32108).upper()]
	preselect = [scrapers.index(i) for i in settings.active_scrapers(group_folders=True)]
	scraper_choice = multiselect_dialog('Fen', scraper_names, scrapers, preselect=preselect)
	if scraper_choice is None: return
	return [toggle_setting('provider.%s' % i, ('true' if i in scraper_choice else 'false')) for i in scrapers]

def set_subtitle_action():
	from modules.nav_utils import toggle_setting
	choices = ((ls(32192), '0'), (ls(32193), '1'), (ls(32027), '2'))
	choice = selection_dialog([i[0] for i in choices], [i[1] for i in choices])
	if choice: return toggle_setting('subtitles.subs_action', choice)

def set_media_action():
	def _set():
		toggle_setting('default_open_action', choice1)
		toggle_setting('default_open_db_type', choice2)
	actions = [(ls(33013), '0'), (ls(33012), '1'), (ls(33011), '2'), (ls(33033), '3')]
	included_media = [(ls(32028), '0'), (ls(32029), '1'), (ls(32030), '2')]
	choice1 = selection_dialog([i[0] for i in actions], [i[1] for i in actions])
	if choice1 is None: return
	if choice1 is '0':
		choice2 = '2'
		return _set()
	choice2 = selection_dialog([i[0] for i in included_media], [i[1] for i in included_media])
	if choice2 is None: choice2 = get_setting('default_open_db_type')
	return _set()

def results_sorting_choice():
	from modules.nav_utils import toggle_setting
	quality = ls(32241)
	provider = ls(32583)
	size = ls(32584)
	choices = [('%s, %s, %s' % (quality, provider, size), '0'), ('%s, %s, %s' % (quality, size, provider), '1'), ('%s, %s, %s' % (provider, quality, size), '2'),
			   ('%s, %s, %s' % (provider, size, quality), '3'), ('%s, %s, %s' % (size, quality, provider), '4'), ('%s, %s, %s' % (size, provider, quality), '5')]
	choice = selection_dialog([i[0] for i in choices], choices, 'Fen')
	if choice:
		toggle_setting('results.sort_order_display', choice[0])
		toggle_setting('results.sort_order', choice[1])

def subscriptions_update_interval(update_type):
	from modules.nav_utils import toggle_setting
	import time
	import _strptime  # fix bug in python import
	from datetime import datetime, timedelta
	from modules.nav_utils import open_settings
	subscription_timer = get_setting('subscription_timer')
	if update_type == 'interval':
		subscriptions_update_label = 'subscriptions_update_label1'
		hours = ls(32594)
		intervals = [('2 %s' % hours, 2), ('4 %s' % hours, 4), ('8 %s' % hours, 8), ('12 %s' % hours, 12), ('16 %s' % hours, 16), ('24 %s' % hours, 24)]
		try: last_run_time = datetime.strptime(get_setting('service_time'), "%Y-%m-%d %H:%M:%S") - timedelta(hours=int(subscription_timer))
		except TypeError: last_run_time = datetime(*(time.strptime(get_setting('service_time'), "%Y-%m-%d %H:%M:%S")[0:6])) - timedelta(hours=int(subscription_timer))
		choice = selection_dialog([i[0] for i in intervals], intervals)
		if not choice: choice = ('24 Hours', 24)
		interval = str(choice[1])
		interval_display = choice[0]
		new_run_time = last_run_time + timedelta(hours=int(interval))
		new_run_time = new_run_time.strftime("%Y-%m-%d %H:%M:%S")
	else:
		subscriptions_update_label = 'subscriptions_update_label2'
		intervals = []
		for i in range(24): intervals.append(('%02d:00' % i, i))
		choice = selection_dialog([i[0] for i in intervals], intervals, 'Fen')
		if not choice: choice = ('06:00', 6)
		sub_hour = choice[1]
		interval_display = choice[0]
		interval = subscription_timer
		now = datetime.today()
		sub_day = now.day + 1 if sub_hour == 0 else now.day
		new_run_time = now.replace(day=sub_day, hour=sub_hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
		difference = new_run_time - now
		if '1 day' in str(difference): new_run_time = now.replace(day=sub_day, hour=sub_hour, minute=0, second=0, microsecond=0)
		new_run_time = new_run_time.strftime("%Y-%m-%d %H:%M:%S")
	toggle_setting('subscription_timer', interval)
	toggle_setting(subscriptions_update_label, interval_display)
	toggle_setting('service_time', new_run_time)

def unaired_episode_color_choice():
	from modules.nav_utils import toggle_setting
	chosen_color = color_chooser('Fen', no_color=True)
	if chosen_color: toggle_setting('unaired_episode_colour', chosen_color)

def scraper_dialog_color_choice(setting):
	from modules.nav_utils import toggle_setting
	setting ='int_dialog_highlight' if setting == 'internal' else 'ext_dialog_highlight'
	chosen_color = color_chooser('Fen')
	if chosen_color: toggle_setting(setting, chosen_color)

def next_episode_color_choice(setting):
	from modules.nav_utils import open_settings
	choices = [(ls(32078), 'nextep.airdate_colour', 'Airdate'),
				(ls(32079), 'nextep.unaired_colour', 'Unaired'),
				(ls(32080), 'nextep.unwatched_colour', 'Unwatched')]
	prelim_setting = setting
	title, setting = [(i[0], i[1]) for i in choices if i[2] == prelim_setting][0]
	chosen_color = color_chooser('Fen - %s' % title, no_color=True)
	if chosen_color: set_setting(setting, chosen_color)

def next_episode_options_choice(setting):
	from modules.nav_utils import notification
	from modules.utils import selection_dialog
	off = ls(32027).upper()
	on = ls(32090).upper()
	choices = [
			('Sort Type', 'nextep.sort_type', [(ls(32226).upper(), '0'), (ls(32227).upper(), '1'), (ls(32228).upper(), '2')]),
			('Sort Order', 'nextep.sort_order', [(ls(32225).upper(), '0'), (ls(32224).upper(), '1')]),
			('Include Unaired', 'nextep.include_unaired', [(off, 'false'), (on, 'true')]),
			('Include Trakt or Fen Unwatched', 'nextep.include_unwatched', [(off, 'false'), (on, 'true')]),
			('Cache To Disk', 'nextep.cache_to_disk', [(off, 'false'), (on, 'true')]),
			('Include Airdate in Title', 'nextep.include_airdate', [(off, 'false'), (on, 'true')]),
			('Airdate Format', 'nextep.airdate_format', [(ls(32229).upper(), '0'), (ls(32230).upper(), '1'), (ls(32231).upper(), '2')])
				]
	prelim_setting = setting
	title, setting = [(i[0], i[1]) for i in choices if i[0] == prelim_setting][0]
	full_list = [i[2] for i in choices if i[0] == prelim_setting][0]
	dialog_list = [i[0] for i in full_list]
	function_list = [i[1] for i in full_list]
	selection = selection_dialog(dialog_list, function_list, 'Fen - %s' % title)
	if not selection: return
	setting_name = [i[0] for i in full_list if i[1] == selection][0]
	set_setting(setting, selection)
	notification(ls(32576), 6000)

def next_episode_context_choice():
	from modules.utils import selection_dialog
	from modules.nav_utils import toggle_setting
	content_settings = settings.nextep_content_settings()
	display_settings = settings.nextep_display_settings()
	airdate_replacement = [('%d-%m-%Y', ls(32229)), ('%Y-%m-%d', ls(32230)), ('%m-%d-%Y', ls(32231))]
	sort_type_status = (ls(32226), ls(32227), ls(32228))[content_settings['sort_type']]
	sort_order_status = (ls(32225), ls(32224))[content_settings['sort_order']]
	toggle_sort_order_SETTING = ('nextep.sort_order', ('0' if sort_order_status == ls(32224) else '1'))
	cache_to_disk_status = str(content_settings['cache_to_disk'])
	toggle_cache_to_disk_SETTING = ('nextep.cache_to_disk', ('true' if cache_to_disk_status == 'False' else 'false'))
	unaired_status = str(content_settings['include_unaired'])
	toggle_unaired_SETTING = ('nextep.include_unaired', ('true' if unaired_status == 'False' else 'false'))
	unwatched_status = str(content_settings['include_unwatched'])
	toggle_unwatched_SETTING = ('nextep.include_unwatched', ('true' if unwatched_status == 'False' else 'false'))
	airdate_status = str(display_settings['include_airdate'])
	toggle_airdate_SETTING = ('nextep.include_airdate', ('true' if airdate_status == 'False' else 'false'))
	airdate_format = settings.nextep_airdate_format()
	airdate_format_status = [airdate_format.replace(i[0], i[1]) for i in airdate_replacement if i[0] == airdate_format][0]
	airdate_highlight = display_settings['airdate_colour'].capitalize()
	unaired_highlight = display_settings['unaired_colour'].capitalize()
	unwatched_highlight = display_settings['unwatched_colour'].capitalize()
	base_string = '%s: [I]%s [B]%s[/B][/I]' % ('%s', ls(32598), '%s')
	choices = [
			(ls(32596).upper(), 'manage_in_progress'),
			(base_string % (ls(32066).upper(), sort_type_status), 'Sort Type'),
			(base_string % (ls(32067), sort_order_status), 'toggle_sort_order'),
			(base_string % (ls(32075), cache_to_disk_status), 'toggle_cache_to_disk'),
			(base_string % (ls(32073), unaired_status), 'toggle_unaired'),
			(base_string % (ls(32074), unwatched_status), 'toggle_unwatched'),
			(base_string % (ls(32076), airdate_status), 'toggle_airdate'),
			(base_string % (ls(32077), airdate_format_status), 'Airdate Format'),
			(base_string % (ls(32078), airdate_highlight), 'Airdate'),
			(base_string % (ls(32079), unaired_highlight), 'Unaired'),
			(base_string % (ls(32080), unwatched_highlight), 'Unwatched')]
	if settings.watched_indicators() == 0: choices.append((ls(32597), 'manage_unwatched'))
	if settings.watched_indicators() in (1,2): choices.append((ls(32497) % ls(32037), 'clear_cache'))
	string = 'Fen - %s' % ls(32599)
	dialog_list = [i[0] for i in choices]
	function_list = [i[1] for i in choices]
	choice = selection_dialog(dialog_list, function_list, string)
	if not choice: return
	if choice in ('toggle_sort_order', 'toggle_cache_to_disk', 'toggle_unaired', 'toggle_unwatched', 'toggle_airdate'):
		setting = eval(choice + '_SETTING')
		toggle_setting(setting[0], setting[1])
	elif choice == 'clear_cache':
		from modules.nav_utils import clear_cache
		clear_cache('trakt')
	else:
		if choice in ('manage_in_progress', 'manage_unwatched'):
			xbmc.executebuiltin('Container.Update(%s)' % build_url({'mode': 'build_next_episode_manager', 'action': choice})); return
		elif choice in ('Airdate','Unaired', 'Unwatched'): function = next_episode_color_choice
		else: function = next_episode_options_choice
		function(choice)
	xbmc.executebuiltin("Container.Refresh")
	xbmc.executebuiltin('RunPlugin(%s)' % build_url({'mode': 'next_episode_context_choice'}))

def scraper_quality_color_choice(setting):
	from modules.nav_utils import toggle_setting
	chosen_color = color_chooser('Fen')
	if chosen_color: toggle_setting(setting, chosen_color)

def external_scrapers_manager():
	dialog = xbmcgui.Dialog()
	icon = settings.ext_addon('script.module.fenomscrapers').getAddonInfo('icon')
	fail_color = 'crimson'
	all_color = 'mediumvioletred'
	hosters_color = get_setting('hoster.identify')
	torrent_color = get_setting('torrent.identify')
	enable_string, disable_string, specific_string, all_string, failing_string, ext_scrapers_string, reset_string, stats_string, scrapers_string, hosters_string, torrent_string = ls(32055), ls(32024), ls(32536), ls(32525), ls(32529), ls(32118), ls(32531), ls(32532), ls(32533), ls(33031), ls(32535)
	failing_scrapers_string, all_scrapers_string, hosters_scrapers_string = '%s %s' % (failing_string, scrapers_string), '%s %s' % (all_string, scrapers_string), '%s %s' % (hosters_string, scrapers_string)
	torrent_scrapers_string, fail1_string, fail2_string = '%s %s' % (torrent_string, scrapers_string), '%s %s %s' % (disable_string, failing_string, ext_scrapers_string), '%s %s %s %s' % (reset_string, failing_string, ext_scrapers_string, stats_string)
	enable_string_base, disable_string_base, enable_disable_string_base = '%s %s %s %s' % (enable_string, all_string, '%s', scrapers_string), '%s %s %s %s' % (disable_string, all_string, '%s', scrapers_string), '%s/%s %s %s %s' % (enable_string, disable_string, specific_string, '%s', scrapers_string)
	failure_base = '[COLOR %s][B]%s : [/B][/COLOR]' % (fail_color, failing_scrapers_string.upper())
	all_scrapers_base = '[COLOR %s][B]%s : [/B][/COLOR]' % (all_color, all_scrapers_string.upper())
	debrid_scrapers_base = '[COLOR %s][B]%s : [/B][/COLOR]' % (hosters_color, hosters_scrapers_string.upper())
	torrent_scrapers_base = '[COLOR %s][B]%s : [/B][/COLOR]' % (torrent_color, torrent_scrapers_string.upper())
	tools_menu = \
		[(failure_base, fail1_string, {'mode': 'external_scrapers_disable'}),
		(failure_base, fail2_string, {'mode': 'external_scrapers_reset_stats'}),
		(all_scrapers_base, enable_string_base % '', {'mode': 'toggle_all', 'folder': 'all', 'setting': 'true'}),
		(all_scrapers_base, disable_string_base % '', {'mode': 'toggle_all', 'folder': 'all', 'setting': 'false'}),
		(all_scrapers_base, enable_disable_string_base % '',{'mode': 'enable_disable_specific_all', 'folder': 'all'}),
		(debrid_scrapers_base, enable_string_base % hosters_string, {'mode': 'toggle_all', 'folder': 'hosters', 'setting': 'true'}),
		(debrid_scrapers_base, disable_string_base % hosters_string, {'mode': 'toggle_all', 'folder': 'hosters', 'setting': 'false'}),
		(debrid_scrapers_base, enable_disable_string_base % hosters_string, {'mode': 'enable_disable_specific_all', 'folder': 'hosters'}),
		(torrent_scrapers_base, enable_string_base % torrent_string, {'mode': 'toggle_all', 'folder': 'torrents', 'setting': 'true'}),
		(torrent_scrapers_base, disable_string_base % torrent_string, {'mode': 'toggle_all', 'folder': 'torrents', 'setting': 'false'}),
		(torrent_scrapers_base, enable_disable_string_base % torrent_string, {'mode': 'enable_disable_specific_all', 'folder': 'torrents'})]
	choice_list = []
	for item in tools_menu:
		if xbmc.getSkinDir() in ('skin.aeon.nox.silvo', 'skin.atlas'):
			line1 = '%s %s' % (item[0], item[1])
			line2 = ''
		else:
			line1 = item[0]
			line2 = '[B][I]%s[/I][/B]' % item[1]
		listitem = xbmcgui.ListItem(line1, line2)
		listitem.setArt({'icon': icon})
		choice_list.append(listitem)
	chosen_tool = dialog.select("Fen", choice_list, useDetails=True)
	if chosen_tool < 0: return
	from modules import source_utils
	params = tools_menu[chosen_tool][2]
	mode = params['mode']
	if mode == 'external_scrapers_disable':
		source_utils.external_scrapers_disable()
	elif mode == 'external_scrapers_reset_stats':
		source_utils.external_scrapers_reset_stats()
	elif mode == 'toggle_all':
		source_utils.toggle_all(params['folder'], params['setting'])
	elif mode == 'enable_disable_specific_all':
		source_utils.enable_disable_specific_all(params['folder'])
	return external_scrapers_manager()

def scraper_color_choice(setting):
	from modules.nav_utils import toggle_setting
	choices = [('furk', 'provider.furk_colour'),
				('easynews', 'provider.easynews_colour'),
				('pm-cloud', 'provider.pm-cloud_colour'),
				('rd-cloud', 'provider.rd-cloud_colour'),
				('ad-cloud', 'provider.ad-cloud_colour'),
				('local', 'provider.local_colour'),
				('downloads', 'provider.downloads_colour'),
				('folders', 'provider.folders_colour'),
				('hoster', 'hoster.identify'),
				('torrent', 'torrent.identify'),
				('second_line', 'secondline.identify')]
	setting = [i[1] for i in choices if i[0] == setting][0]
	dialog = 'Fen'
	chosen_color = color_chooser(dialog)
	if chosen_color: toggle_setting(setting, chosen_color)

def folder_sources_choice(setting):
	from modules.nav_utils import toggle_setting
	folder = xbmcgui.Dialog().browse(0, 'Fen', '')
	if not folder: folder = 'None'
	set_setting(setting, folder)

def folder_clear_choice():
	from modules.nav_utils import toggle_setting
	folders = ['folder1', 'folder2', 'folder3', 'folder4', 'folder5']
	folder_info = [(ls(33036) % (i.upper(), (get_setting('%s.display_name' % i).upper())), i) for i in folders]
	selection = selection_dialog([i[0] for i in folder_info], [i[1] for i in folder_info])
	if not selection: return
	set_setting('%s.display_name' % selection, 'Folder %s' % selection[-1:])
	set_setting('%s.movies_directory' % selection, 'None')
	set_setting('%s.tv_shows_directory' % selection, 'None')

def internal_scrapers_order_choice():
	from modules.nav_utils import toggle_setting
	window = xbmcgui.Window(10000)
	display = []
	label_list = [('files', ls(32493), '$ADDON[plugin.video.fen 32493]'), ('furk', ls(32069), '$ADDON[plugin.video.fen 32069]'), 
				  ('easyews', ls(32070), '$ADDON[plugin.video.fen 32070]'), ('cloud', ls(32586), '$ADDON[plugin.video.fen 32586]')]
	try: current_setting = window.getProperty('FEN_internal_scrapers_order').split(', ')
	except: current_setting = ['']
	try: current_display_setting = window.getProperty('FEN_internal_scrapers_order_display').split(', ')
	except: current_display_setting = ['']
	if len(current_setting) != 4 or len(current_display_setting) != 4:
		current_setting = settings.internal_scraper_order()
		current_display_setting = settings.internal_scrapers_order_display()
	for i in current_display_setting:
		for x in label_list:
			if i == x[2]: display.append(x[1])
	adjust_scraper = selection_dialog(display, [(i, current_display_setting[current_setting.index(i)]) for i in current_setting], 'Fen')
	if not adjust_scraper:
		window.clearProperty('FEN_internal_scrapers_order')
		window.clearProperty('FEN_internal_scrapers_order_display')
		return
	str_insert = [i[1] for i in label_list if i[2] == adjust_scraper[1]][0]
	choices = [(ls(32588) % str_insert, (0, current_setting.index(adjust_scraper[0]))),
			   (ls(32589) % str_insert, (1, current_setting.index(adjust_scraper[0]))),
			   (ls(32590) % str_insert, (2, current_setting.index(adjust_scraper[0]))),
			   (ls(32591) % str_insert, (3, current_setting.index(adjust_scraper[0])))]
	positioning_info = selection_dialog([i[0] for i in choices], [i[1] for i in choices], 'Fen - %s' % (ls(32587) % adjust_scraper[1]))
	if not positioning_info: return internal_scrapers_order_choice()
	new_position = positioning_info[0]
	current_position = positioning_info[1]
	current_setting.insert(new_position, current_setting.pop(current_position))
	current_display_setting.insert(new_position, current_display_setting.pop(current_position))
	new_order_setting = (', ').join(current_setting)
	new_order_setting_display = (', ').join(current_display_setting)
	toggle_setting('results.internal_scrapers_order', new_order_setting)
	xbmc.sleep(100)
	toggle_setting('results.internal_scrapers_order_display', new_order_setting_display)
	window.setProperty('FEN_internal_scrapers_order', new_order_setting)
	window.setProperty('FEN_internal_scrapers_order_display', new_order_setting_display)
	xbmc.sleep(200)
	return internal_scrapers_order_choice()

def build_add_to_remove_from_list(meta, media_type, orig_mode, from_search):
	try: meta = json.loads(meta)
	except: pass
	add_to_str = ls(32602)
	remove_from_str = ls(32603)
	main_listing = [('%s...' % add_to_str, 'add'), ('%s...' % remove_from_str, 'remove')]
	mlc = selection_dialog([i[0] for i in main_listing], [i[1] for i in main_listing], 'Fen')
	if mlc == None: return
	heading = '%s ' % add_to_str if mlc == 'add' else '%s ' % remove_from_str
	listing = [(heading + ls(32205), 'trakt'), (heading + ls(32453), 'favourites')]
	if settings.show_subscriptions(): listing.append((heading + ls(32194), 'subscriptions'))
	if media_type == 'tvshow' and settings.watched_indicators() == 0: listing.append((heading + ls(32483), 'unwatched_next_episode'))
	if mlc == 'remove': listing.append((heading + ls(32604) % (ls(32028) if media_type == 'movie' else ls(32029)), 'refresh'))
	choice = selection_dialog([i[0] for i in listing], [i[1] for i in listing], 'Fen')
	if choice == None: return
	elif choice == 'trakt': url = {'mode': ('trakt.trakt_add_to_list' if mlc == 'add' else 'trakt.trakt_remove_from_list'), 'tmdb_id': meta["tmdb_id"], 'imdb_id': meta["imdb_id"], 'tvdb_id': meta["tvdb_id"], 'db_type': media_type}
	elif choice == 'favourites': url = {'mode': ('add_to_favourites' if mlc == 'add' else 'remove_from_favourites'), 'db_type': media_type, 'tmdb_id': meta["tmdb_id"], 'title': meta['title']}
	elif choice == 'subscriptions': url = {'mode': 'subscriptions_add_remove', 'action': mlc, 'db_type': media_type, 'tmdb_id': meta["tmdb_id"], 'orig_mode': orig_mode}
	elif choice == 'unwatched_next_episode': url = {'mode': 'add_next_episode_unwatched', 'action': mlc, 'title': meta["title"], 'tmdb_id': meta["tmdb_id"], 'imdb_id': meta["imdb_id"]}
	elif choice == 'refresh': url = {'mode': 'refresh_cached_data', 'db_type': media_type, 'id_type': 'tmdb_id', 'media_id': meta['tmdb_id']}
	xbmc.executebuiltin('RunPlugin(%s)' % build_url(url))

def options_menu(params):
	from modules.nav_utils import toggle_setting, open_settings, clear_cache, clear_scrapers_cache, clear_and_rescrape
	content = xbmc.getInfoLabel('Container.Content')
	if not content: content = params.get('content', None)
	from_results = params.get('from_results')
	suggestion = params.get('suggestion', '')
	vid_type = params.get('vid_type', '')
	try: meta = json.loads(params.get('meta'))
	except: meta = None
	is_widget = False if 'plugin' in xbmc.getInfoLabel('Container.PluginName') else True
	on_str, off_str, currently_str, open_str, settings_str = ls(32090), ls(32027), ls(32598), ls(32641).upper(), ls(32247).upper()
	furk_easy_search_str = '%s/%s %s: [B][I]%s[/I][/B]' % (ls(32069).upper(), ls(32070).upper(), ls(32450).upper(), '%s')
	media_action_str_lst = [(ls(33013), '0'), (ls(33012), '1'), (ls(33011), '2'), (ls(33033), '3')]
	media_included_str_lst = [(ls(32028), '0'), (ls(32029), '1'), (ls(32030), '2')]
	base_str = '%s%s: [I]%s [B]%s[/B][/I]' % ('%s', '%s', currently_str, '%s')
	autoplay_status, autoplay_toggle, filter_setting = (on_str, 'false', 'autoplay_quality') if settings.auto_play() else (off_str, 'true', 'results_quality')
	media_action_setting = [i[0] for i in media_action_str_lst if i[1] == get_setting('default_open_action')][0]
	media_included_setting = [i[0] for i in media_included_str_lst if i[1] == get_setting('default_open_db_type')][0]
	media_action_status = ls(33034) % (media_action_setting, media_included_setting)
	quality_filter_setting = 'autoplay' if autoplay_status == on_str else 'results'
	autoplay_next_status, autoplay_next_toggle = (on_str, 'false') if settings.autoplay_next_episode() else (off_str, 'true')
	results_sorting_status = get_setting('results.sort_order_display')
	current_subs_action = get_setting('subtitles.subs_action')
	current_subs_action_status = 'Auto' if current_subs_action == '0' else ls(32193) if current_subs_action == '1' else off_str
	active_scrapers = [i.replace('-', '') for i in settings.active_scrapers(group_folders=True)]
	current_scrapers_status = ', '.join([i.upper()[:3] for i in active_scrapers]) if len(active_scrapers) > 0 else 'N/A'
	current_filter_status =  ', '.join(settings.quality_filter(filter_setting))
	enable_yearcheck_status, enable_yearcheck_toggle = (on_str, 'false') if get_setting('search.enable.yearcheck') =='true' else (off_str, 'true')
	uncached_torrents_status, uncached_torrents_toggle = (on_str, 'false') if get_setting('torrent.display.uncached') =='true' else (off_str, 'true')
	listing = []
	if content in ('movies', 'episodes', 'movie', 'episode'): listing += [(ls(32014).upper(), 'rescrape_select')]
	listing += [(base_str % ('', ls(32175).upper(), autoplay_status), 'toggle_autoplay')]
	if autoplay_status == on_str: listing += [(base_str % (' - ', ls(32178).upper(), autoplay_next_status), 'toggle_autoplay_next')]
	listing += [(base_str % ('', ls(33010).upper(), media_action_status), 'set_media_action')]
	listing += [(base_str % ('', '%s %s' % (ls(32055).upper(), ls(32533).upper()), current_scrapers_status), 'enable_scrapers')]
	if autoplay_status == off_str: listing += [(base_str % ('', ls(32151).upper(), results_sorting_status), 'set_results_sorting')]
	listing += [(base_str % ('', ls(32105).upper(), current_filter_status), 'set_filters')]
	listing += [(base_str % ('', ls(32183).upper(), current_subs_action_status), 'set_subs_action')]
	if 'external' in active_scrapers:
		listing += [(base_str % ('', ls(33006).upper(), enable_yearcheck_status), 'toggle_enable_yearcheck')]
		listing += [(base_str % ('', ls(32160).upper(), uncached_torrents_status), 'toggle_torrents_display_uncached')]
	if content in ('movies', 'episodes', 'movie', 'episode'): listing += [(furk_easy_search_str % suggestion, 'search_directly')]
	if settings.watched_indicators() in (1,2): listing += [((ls(32497) % ls(32037)).upper(), 'clear_trakt_cache')]
	listing += [(ls(32637).upper(), 'clear_scrapers_cache')]
	listing += [('%s %s' % (ls(32118).upper(), ls(32513).upper()), 'open_external_scrapers_manager')]
	listing += [('%s %s %s' % (open_str, ls(32523).upper(), settings_str), 'open_meta_settings')]
	listing += [('%s %s %s' % (open_str, ls(32522).upper(), settings_str), 'open_scraper_settings')]
	listing += [('%s %s %s' % (open_str, ls(32036).upper(), settings_str), 'open_fen_settings')]
	listing += [('[B]%s[/B]' % ls(32640).upper(), 'save_and_exit')]
	choice = selection_dialog([i[0] for i in listing], [i[1] for i in listing])
	if choice == 'rescrape_select': return clear_and_rescrape(content, suggestion, meta, is_widget)
	if choice == 'toggle_autoplay': toggle_setting('auto_play', autoplay_toggle)
	elif choice == 'set_media_action': set_media_action()
	elif choice == 'toggle_autoplay_next': toggle_setting('autoplay_next_episode', autoplay_next_toggle)
	elif choice == 'enable_scrapers': enable_scrapers()
	elif choice == 'set_results_sorting': results_sorting_choice()
	elif choice == 'set_filters': set_quality(quality_filter_setting)
	elif choice == 'set_subs_action': set_subtitle_action()
	elif choice == 'toggle_enable_yearcheck': toggle_setting('search.enable.yearcheck', enable_yearcheck_toggle)
	elif choice == 'toggle_torrents_display_uncached': toggle_setting('torrent.display.uncached', uncached_torrents_toggle)
	elif choice == 'search_directly': furk_easynews_direct_search_choice(suggestion, from_results)
	elif choice == 'clear_trakt_cache': clear_cache('trakt')
	elif choice == 'clear_scrapers_cache': clear_scrapers_cache()
	elif choice == 'open_external_scrapers_manager': external_scrapers_manager()
	elif choice == 'open_meta_settings': xbmc.executebuiltin('Addon.OpenSettings(script.module.tikimeta)')
	elif choice == 'open_scraper_settings': xbmc.executebuiltin('Addon.OpenSettings(script.module.fenomscrapers)')
	elif choice == 'open_fen_settings': open_settings('0.0')
	if choice in ('clear_cache_page', 'clear_trakt_cache') and content in ('movies', 'tvshows', 'seasons', 'episodes'): xbmc.executebuiltin('Container.Refresh')
	if choice in (None, 'save_and_exit', 'clear_cache_page', 'clear_trakt_cache', 'clear_scrapers_cache', 'search_directly', 'open_meta_settings', 'open_scraper_settings', 'open_fen_settings', 'open_external_scrapers_manager'): return
	xbmc.sleep(350)
	xbmc.executebuiltin('RunPlugin(%s)' % build_url(params))

def extras_menu(media_type, meta_json, action=None, play_params=None, default_season=0):
	from sys import argv
	import xbmcplugin
	from modules.nav_utils import movie_genres, tvshow_genres, networks, extended_info_open, remove_unwanted_info_keys, setView
	from modules.utils import merge_dicts
	def _process_dicts(_key, _dict):
		new_dict = {}
		for key, value in _dict.items():
			if key in _key: new_dict[key] = value
		return new_dict
	def process_list_dicts(_key, _value, _return_value, dict_list):
		for item in dict_list:
			if _key in item and item[_key] == _value:
				return item[_return_value]
	__handle__ = int(argv[1])
	path = xbmc.getInfoLabel('Container.FolderPath')
	try: action = int(action)
	except: pass
	meta = json.loads(meta_json)
	autoplay = settings.auto_play()
	title = meta['title']
	rootname = meta['rootname']
	poster, fanart, banner, clearart = meta['poster'], meta['fanart'], meta['banner'], meta['clearart']
	clearlogo, landscape, discart = meta['clearlogo'], meta['landscape'], meta['discart']
	tmdb_id = meta['tmdb_id']
	imdb_id = meta['imdb_id']
	trailer = meta['trailer']
	cast = meta['cast']
	director = meta.get('director', None)
	year = meta.get('year', None)
	genre = meta.get('genre', None)
	plot = meta.get('plot', None)
	network = meta.get('studio', None)
	extra_info = meta.get('extra_info', None)
	collection_name, collection_id = None, None
	if extra_info:
		extra_info['alternative_titles'] = meta.get('alternative_titles', [])
		if media_type == 'movies':
			collection_name, collection_id = extra_info.get('collection_name', None), extra_info.get('collection_id', None)
	if play_params: play_runner = build_url(json.loads(play_params))
	if media_type in ('tv', 'season', 'episode'): base_media = 'tv'
	else: base_media = 'movies'
	if network:
		if base_media == 'tv': network_id = process_list_dicts('name', network, 'id', networks())
		else: network_id = network
	else: network_id = None
	if genre: genre_dict = _process_dicts(genre, merge_dicts(movie_genres(), tvshow_genres()))
	else: genre_dict = None
	sim_recom_runner = build_url({"mode": "similar_recommendations_choice", "db_type": base_media, 'sim_recom_name': rootname, "sim_recom_tmdb": tmdb_id, "sim_recom_imdb": imdb_id})
	if plot: plot_runner = build_url({"mode": "plot_choice", "heading": rootname, 'plot_text': plot})
	if meta.get('all_trailers', False): trailer_runner = build_url({'mode': 'play_trailer', 'url': trailer, 'all_trailers': json.dumps(meta['all_trailers'])})
	else: trailer_runner = build_url({'mode': 'play_trailer', 'url': trailer})
	if cast: actors_runner = build_url({'mode': 'show_all_actors_choice', 'media_rootname': rootname, 'full_cast': json.dumps(cast)})
	director_runner = build_url({'mode': 'people_search.extras_person_data', 'person_name': director})
	year_runner = build_url({'mode': 'build_%s_list' % ('movie' if base_media == 'movies' else 'tvshow'), 'action': 'tmdb_%s_year' % base_media, 'year': year})
	genre_runner = build_url({'mode': 'build_%s_list' % ('movie' if base_media == 'movies' else 'tvshow'), 'action': 'tmdb_%s_genres' % base_media, 'genre_list': json.dumps(genre_dict)})
	network_runner = build_url({'mode': 'build_%s_list' % ('movie' if base_media == 'movies' else 'tvshow'), 'action': 'tmdb_%s_networks' % base_media, 'network_id': network_id, 'network_name': network})
	collection_runner = build_url({'mode': 'build_movie_list', 'action': 'tmdb_movies_collection', 'collection_id': collection_id})
	extra_info_runner = build_url({'mode': 'media_extra_info_choice', 'media_type': media_type, 'meta': meta_json, 'extra_info': json.dumps(extra_info)})
	images_posters_runner = build_url({'mode': 'tmdb_artwork_image_results', 'db_type': base_media, 'tmdb_id': tmdb_id, 'image_type': 'posters'})
	images_backdrops_runner = build_url({'mode': 'tmdb_artwork_image_results', 'db_type': base_media, 'tmdb_id': tmdb_id, 'image_type': 'backdrops'})
	play_random_params = {'mode': 'play_fetch_random', 'db_type': 'episode', 'meta': meta_json, 'default_season': default_season}
	images_runner = build_url({'mode': 'imdb_image_results', 'imdb_id': imdb_id, 'page_no': 1, 'rolling_count': 0})
	videos_runner = build_url({'mode': 'imdb_build_videos_list', 'imdb_id': imdb_id})
	reviews_runner = build_url({'mode': 'imdb_reviews_choice', 'rootname': rootname, 'imdb_id': imdb_id, 'poster': poster})
	trivia_runner = build_url({'mode': 'imdb_trivia_choice', 'rootname': rootname, 'content': 'trivia', 'imdb_id': imdb_id, 'poster': poster})
	blunders_runner = build_url({'mode': 'imdb_trivia_choice', 'rootname': rootname, 'content': 'blunders', 'imdb_id': imdb_id, 'poster': poster})
	parentsguide_runner = build_url({'mode': 'imdb_parentsguide_choice', 'rootname': rootname, 'imdb_id': imdb_id})
	play_random_runner = build_url(play_random_params)
	extended_info_runner = build_url({'mode': 'extended_info_open', 'db_type': base_media, 'tmdb_id': tmdb_id})
	items = []
	if play_params:
		if media_type in ('movies', 'episode'): items += [('[B]%s...[/B]' % ls(32764), play_runner, False)]
		else: items += [(ls(32652), play_runner, True)]
	if action not in (2, 3):
		if media_type != 'movies': items += [("%s%s" % (ls(32618), ' [B][I]%s %s[/I][/B]' % (ls(32537), default_season) if media_type in ('season', 'episode') else ''), play_random_runner, False)]
		items += [("%s/%s" % (ls(32592), ls(32593)), sim_recom_runner, False)]
		if extra_info: items += [(ls(32605), extra_info_runner, False)]
		if plot: items += [(ls(32987), plot_runner, False)]
		if cast: items += [(ls(32608), actors_runner, False)]
		if trailer: items += [(ls(32606), trailer_runner, False)]
		if imdb_id:
			items += [(ls(32988), images_runner, True)]
			items += [(ls(33032), videos_runner, True)]
			items += [('%s (%s)' % (ls(32607), ls(32985)), reviews_runner, False)]
			items += [('%s (%s)' % (ls(32984), ls(32985)), trivia_runner, False)]
			items += [('%s (%s)' % (ls(32986), ls(32985)), blunders_runner, False)]
			items += [('%s (%s)' % (ls(32989), ls(32985)), parentsguide_runner, False)]
		if media_type == 'movies' and director: items += [(ls(32609), director_runner, True)]
		if settings.addon_installed('script.extendedinfo'): items += [(ls(32610), extended_info_runner, False)]
		if collection_id: items += [(ls(32611) % collection_name, collection_runner, True)]
		if year: items += [(ls(32612) % year, year_runner, True)]
		if genre_dict: items += [(ls(32613) % genre, genre_runner, True)]
		if network_id: items += [(ls(32614) % (ls(32615) if base_media == 'movies' else ls(32480), network), network_runner, True)]
		items += [(ls(32616), images_posters_runner, True)]
		items += [(ls(32617), images_backdrops_runner, True)]
	for i in items:
		try:
			isFolder = i[2]
			if action in (2, 3): name = i[0]
			else: name = ls(33037) % i[0]
			try: listitem = xbmcgui.ListItem(offscreen=True)
			except: listitem = xbmcgui.ListItem()
			listitem.setLabel(name)
			listitem.setArt({'poster': poster, 'fanart': fanart, 'icon': poster, 'banner': banner, 'clearart': clearart, 'clearlogo': clearlogo, 'landscape': landscape, 'discart': discart})
			if action in (2, 3):
				listitem.setCast(cast)
				listitem.setInfo('Video', remove_unwanted_info_keys(meta))
			else:
				listitem.setInfo('Video', {})
			xbmcplugin.addDirectoryItem(__handle__, i[1], listitem, isFolder=isFolder)
		except: pass
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=False)
	xbmc.sleep(50)
	if action in (2,3) and not any(i in path for i in ['play_media', 'build_season_list', 'build_episode_list']):
		if action == 2: extended_info_open(base_media, tmdb_id)
		else: xbmc.executebuiltin('Action(Info)')
	setView('view.main', 'files')

def media_extra_info(media_type, meta, extra_info):
	extra_info = json.loads(extra_info)
	meta = json.loads(meta)
	body = []
	tagline_str, premiered_str, rating_str, votes_str, runtime_str, genres_str, budget_str, revenue_str, director_str, writer_str = ls(32619), ls(32620), ls(32621), ls(32623), ls(32622), ls(32624), ls(32625), ls(32626), ls(32627), ls(32628)
	studio_str, collection_str, homepage_str, status_str, type_str, classification_str, network_str, created_by_str, last_aired_str, next_aired_str, seasons_str, episodes_str = ls(32615), ls(32499), ls(32629), ls(32630), ls(32631), ls(32632), ls(32480), ls(32633), ls(32634), ls(32635), ls(32636), ls(32506)
	try:
		if media_type == 'movies':
			body.append('[B]%s:[/B] %s' % (tagline_str, meta['tagline']))
			if 'alternative_titles' in extra_info and extra_info['alternative_titles']: body.append('[B]%s:[/B] %s' % ('Aliases', ', '.join(extra_info['alternative_titles'])))
			if 'status' in extra_info: body.append('[B]%s:[/B] %s' % (status_str, extra_info['status']))
			body.append('[B]%s:[/B] %s' % (premiered_str, meta['premiered']))
			body.append('[B]%s:[/B] %s (%s %s)' % (rating_str, meta['rating'], meta['votes'], votes_str))
			body.append('[B]%s:[/B] %s mins' % (runtime_str, str(meta['duration']/60)))
			body.append('[B]%s:[/B] %s' % (genres_str, meta['genre']))
			if 'budget' in extra_info: body.append('[B]%s:[/B] %s' % (budget_str, extra_info['budget']))
			if 'revenue' in extra_info: body.append('[B]%s:[/B] %s' % (revenue_str, extra_info['revenue']))
			body.append('[B]%s:[/B] %s' % (director_str, meta['director']))
			body.append('[B]%s:[/B] %s' % (writer_str, meta['writer']))
			body.append('[B]%s:[/B] %s' % (studio_str, meta['studio']))
			if 'collection_name' in extra_info: body.append('[B]%s:[/B] %s' % (collection_str, extra_info['collection_name']))
			if 'homepage' in extra_info: body.append('[B]%s:[/B] %s' % (homepage_str, extra_info['homepage']))
		else:
			if 'type' in extra_info: body.append('[B]%s:[/B] %s' % (type_str, extra_info['type']))
			if 'alternative_titles' in extra_info and extra_info['alternative_titles']: body.append('[B]%s:[/B] %s' % ('Aliases', ', '.join(extra_info['alternative_titles'])))
			if 'status' in extra_info: body.append('[B]%s:[/B] %s' % (status_str, extra_info['status']))
			body.append('[B]%s:[/B] %s' % (premiered_str, meta['premiered']))
			body.append('[B]%s:[/B] %s (%s %s)' % (rating_str, meta['rating'], meta['votes'], votes_str))
			body.append('[B]%s:[/B] %s mins' % (runtime_str, str(meta['duration']/60)))
			body.append('[B]%s:[/B] %s' % (classification_str, meta['mpaa']))
			body.append('[B]%s:[/B] %s' % (genres_str, meta['genre']))
			body.append('[B]%s:[/B] %s' % (network_str, meta['studio']))
			if 'created_by' in extra_info: body.append('[B]%s:[/B] %s' % (created_by_str, extra_info['created_by']))
			if 'last_episode_to_air' in extra_info: body.append('[B]%s:[/B] %s' % (last_aired_str, extra_info['last_episode_to_air']))
			if 'next_episode_to_air' in extra_info: body.append('[B]%s:[/B] %s' % (next_aired_str, extra_info['next_episode_to_air']))
			body.append('[B]%s:[/B] %s' % (seasons_str, meta['total_seasons']))
			body.append('[B]%s:[/B] %s' % (episodes_str, meta['total_episodes']))
			if 'homepage' in extra_info: body.append('[B]%s:[/B] %s' % (homepage_str, extra_info['homepage']))
	except:
		from modules.nav_utils import notification
		return notification(ls(32574), 2000)
	xbmcgui.Dialog().select(meta['title'], body)

def furk_easynews_direct_search_choice(suggestion, from_results):
	search = ls(32450).upper()
	direct_search_furk_params = {'mode': 'furk.search_furk', 'db_type': 'video', 'suggestion': suggestion}
	direct_search_easynews_params = {'mode': 'easynews.search_easynews', 'suggestion': suggestion}
	choices = [('%s %s' % (search, ls(32069).upper()), direct_search_furk_params), ('%s %s' % (search, ls(32070).upper()), direct_search_easynews_params)]
	choice = selection_dialog([i[0] for i in choices], [i[1] for i in choices])
	if not choice: xbmc.executebuiltin('RunPlugin(%s)' % build_url({'mode': 'playback_menu', 'from_results': from_results, 'suggestion': suggestion}))
	else: xbmc.executebuiltin('Container.Update(%s)' % build_url(choice))

def color_chooser(msg_dialog, no_color=False):
	color_chart = [
		  'black', 'white', 'whitesmoke', 'gainsboro', 'lightgray', 'silver', 'darkgray', 'gray', 'dimgray',
		  'snow', 'floralwhite', 'ivory', 'beige', 'cornsilk', 'antiquewhite', 'bisque', 'blanchedalmond',
		  'burlywood', 'darkgoldenrod', 'ghostwhite', 'azure', 'lightsaltegray', 'lightsteelblue',
		  'powderblue', 'lightblue', 'skyblue', 'lightskyblue', 'deepskyblue', 'dodgerblue', 'royalblue',
		  'blue', 'mediumblue', 'midnightblue', 'navy', 'darkblue', 'cornflowerblue', 'slateblue', 'slategray',
		  'yellowgreen', 'springgreen', 'seagreen', 'steelblue', 'teal', 'fuchsia', 'deeppink', 'darkmagenta',
		  'blueviolet', 'darkviolet', 'darkorchid', 'darkslateblue', 'darkslategray', 'indigo', 'cadetblue',
		  'darkcyan', 'darkturquoise', 'turquoise', 'cyan', 'paleturquoise', 'lightcyan', 'mintcream', 'honeydew',
		  'aqua', 'aquamarine', 'chartreuse', 'greenyellow', 'palegreen', 'lawngreen', 'lightgreen', 'lime',
		  'mediumspringgreen', 'mediumturquoise', 'lightseagreen', 'mediumaquamarine', 'mediumseagreen',
		  'limegreen', 'darkseagreen', 'forestgreen', 'green', 'darkgreen', 'darkolivegreen', 'olive', 'olivedab',
		  'darkkhaki', 'khaki', 'gold', 'goldenrod', 'lightyellow', 'lightgoldenrodyellow', 'lemonchiffon',
		  'yellow', 'seashell', 'lavenderblush', 'lavender', 'lightcoral', 'indianred', 'darksalmon',
		  'lightsalmon', 'pink', 'lightpink', 'hotpink', 'magenta', 'plum', 'violet', 'orchid', 'palevioletred',
		  'mediumvioletred', 'purple', 'maroon', 'mediumorchid', 'mediumpurple', 'mediumslateblue', 'thistle',
		  'linen', 'mistyrose', 'palegoldenrod', 'oldlace', 'papayawhip', 'moccasin', 'navajowhite', 'peachpuff',
		  'sandybrown', 'peru', 'chocolate', 'orange', 'darkorange', 'tomato', 'orangered', 'red', 'crimson',
		  'salmon', 'coral', 'firebrick', 'brown', 'darkred', 'tan', 'rosybrown', 'sienna', 'saddlebrown'
		  ]
	color_display = ['[COLOR=%s]%s[/COLOR]' % (i, i.capitalize()) for i in color_chart]
	if no_color:
		color_chart.insert(0, 'No Color')
		color_display.insert(0, 'No Color')
	choice = selection_dialog(color_display, color_chart, msg_dialog)
	if not choice: return
	return choice
