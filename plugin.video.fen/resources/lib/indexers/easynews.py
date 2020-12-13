import xbmc, xbmcplugin, xbmcgui
import os
from sys import argv
try: from urllib import unquote, urlencode, quote
except ImportError: from urllib.parse import unquote, urlencode, quote
from apis.easynews_api import import_easynews
from modules.nav_utils import build_url, setView
from modules.utils import clean_file_name, to_utf8
from modules.utils import local_string as ls
from modules.settings import get_theme
# from modules.utils import logger

addon_dir = xbmc.translatePath('special://home/addons/plugin.video.fen')
dialog = xbmcgui.Dialog()
icon_directory = get_theme()
default_easynews_icon = os.path.join(icon_directory, 'easynews.png')
fanart = os.path.join(addon_dir, 'fanart.png')

EasyNews = import_easynews()

def search_easynews(params):
	from modules.history import add_to_search_history
	__handle__ = int(argv[1])
	default = params.get('suggestion', '')
	search_title = clean_file_name(params.get('query')) if ('query' in params and params.get('query') != 'NA') else None
	if not search_title: search_title = dialog.input('Enter search Term', type=xbmcgui.INPUT_ALPHANUM, defaultt=default)
	if not search_title: return
	try:
		search_name = clean_file_name(unquote(search_title))
		add_to_search_history(search_name, 'easynews_video_queries')
		files = EasyNews.search(search_name)
		if not files: return dialog.ok('Fen', ls(32760))
		easynews_file_browser(files, __handle__)
	except: pass
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.premium')

def easynews_file_browser(files, __handle__):
	down_str = ls(32747)
	files = sorted(files, key=lambda k: k['name'])
	for count, item in enumerate(files, 1):
		try:
			cm = []
			name = clean_file_name(item['name']).upper()
			url_dl = item['url_dl']
			size = str(round(float(int(item['rawSize']))/1048576000, 1))
			display = '%02d | [B]%s GB[/B] | [I]%s [/I]' % (count, size, name)
			url_params = {'mode': 'easynews.resolve_easynews', 'url_dl': url_dl, 'play': 'true'}
			url = build_url(url_params)
			down_file_params = {'mode': 'download_file', 'name': item['name'], 'url_dl': url_dl, 'db_type': 'easynews_file', 'image': default_easynews_icon}
			cm.append((down_str,'RunPlugin(%s)' % build_url(down_file_params)))
			listitem = xbmcgui.ListItem(display)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': default_easynews_icon, 'poster': default_easynews_icon, 'thumb': default_easynews_icon, 'fanart': fanart, 'banner': default_easynews_icon})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
		except: pass

def resolve_easynews(params):
	url_dl = params['url_dl']
	resolved_link = EasyNews.resolve_easynews(url_dl)
	if params.get('play', 'false') != 'true' : return resolved_link
	from modules.player import FenPlayer
	FenPlayer().play(resolved_link)

def account_info(params):
	from datetime import datetime
	from modules.utils import jsondate_to_datetime
	try:
		account_html, usage_html = EasyNews.account()
		if not account_html or not usage_html:
			return dialog.ok('Fen', ls(32574))
		account_info = {
					'account_username': to_utf8(account_html[0].find_all('td', recursive = False)[1].getText()),
					'account_type': to_utf8(account_html[1].find_all('td', recursive = False)[2].getText()),
					'account_status': to_utf8(account_html[3].find_all('td', recursive = False)[2].getText()),
					'account_expiration': to_utf8(account_html[2].find_all('td', recursive = False)[2].getText()),
					'usage_total': to_utf8(usage_html[0].find_all('td', recursive = False)[1].getText()),
					'usage_remaining': to_utf8(usage_html[1].find_all('td', recursive = False)[2].getText()),
					'usage_loyalty': to_utf8(usage_html[2].find_all('td', recursive = False)[2].getText())
						}
		expires = jsondate_to_datetime(account_info['account_expiration'], "%Y-%m-%d")
		days_remaining = (expires - datetime.today()).days
		heading = 'EASYNEWS'
		body = []
		body.append(ls(32757) % account_info['account_type'])
		body.append(ls(32755) % account_info['account_username'])
		body.append('[B]%s:[/B] %s' % (ls(32630), account_info['account_status']))
		body.append(ls(32750) % expires)
		body.append(ls(32751) % days_remaining)
		body.append('%s %s' % (ls(32772), account_info['usage_loyalty'].replace('years', ls(32472))))
		body.append(ls(32761) % account_info['usage_total'].replace('Gigs', 'GB'))
		body.append(ls(32762) % account_info['usage_remaining'].replace('Gigs', 'GB'))
		return dialog.select(heading, body)
	except Exception as e:
		return dialog.ok('Fen', ls(32574), str(e))