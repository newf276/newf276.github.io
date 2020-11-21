# -*- coding: utf-8 -*-
from xbmcaddon import Addon

__addon__ = Addon(id='plugin.video.fen')

def local_string(string):
	try: string = int(string)
	except: return string
	try: string = str(__addon__.getLocalizedString(string))
	except: return __addon__.getLocalizedString(string)
	return string

def pool_converter(items):
	"""
	takes tuple, converts it to a list, and turns first item
	into the function and following items into the arguments
	"""
	items = list(items)
	func = items.pop(0)
	return func(*items)

def chunks(l, n):
	"""
	Yield successive n-sized chunks from l.
	"""
	for i in range(0, len(l), n):
		yield l[i:i + n]

def natural_sort(_list, key=lambda s:s):
	"""
	Sort a list into natural alphanumeric order.
	"""
	import re
	def get_alphanum_key_func(key):
		convert = lambda text: int(text) if text.isdigit() else text 
		return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
	sort_key = get_alphanum_key_func(key)
	_list.sort(key=sort_key)

def merge_dicts(*dict_args):
	"""
	Given any number of dicts, shallow copy and merge into a new dict,
	precedence goes to key value pairs in latter dicts.
	"""
	result = {}
	for dictionary in dict_args:
		result.update(dictionary)
	return result

def string_to_float(string, default_return):
	"""
	Remove all alpha from string and return a float.
	Returns float of "default_return" upon ValueError.
	"""
	try:
		return float(''.join(c for c in string if (c.isdigit() or c =='.')))
	except ValueError:
		return float(default_return)

def string_alphanum_to_num(string):
	"""
	Remove all alpha from string and return remaining string.
	Returns original string upon ValueError.
	"""
	try:
		return ''.join(c for c in string if c.isdigit())
	except ValueError:
		return string

def jsondate_to_datetime(jsondate_object, resformat, remove_time=False):
	import _strptime  # fix bug in python import
	from datetime import datetime
	import time
	if remove_time:
		try: datetime_object = datetime.strptime(jsondate_object, resformat).date()
		except TypeError: datetime_object = datetime(*(time.strptime(jsondate_object, resformat)[0:6])).date()
	else:
		try: datetime_object = datetime.strptime(jsondate_object, resformat)
		except TypeError: datetime_object = datetime(*(time.strptime(jsondate_object, resformat)[0:6]))
	return datetime_object
	
def adjust_premiered_date(orig_date, adjust_hours):
	from datetime import timedelta
	if not orig_date: return None, None
	orig_date += ' 23:59:59'
	datetime_object = jsondate_to_datetime(orig_date, "%Y-%m-%d %H:%M:%S")
	adjusted_datetime = datetime_object + timedelta(hours=adjust_hours)
	adjusted_string = adjusted_datetime.strftime('%Y-%m-%d')
	return adjusted_datetime, adjusted_string

def make_day(date, use_words=True):
	from datetime import timedelta
	import time
	from modules.settings import nextep_airdate_format
	from datetime import datetime
	ls = local_string
	today = datetime.utcnow()
	day_diff = (date - today).days
	date_format = nextep_airdate_format()
	try: day = date.strftime(date_format)
	except ValueError: day = date.strftime('%Y-%m-%d')
	if use_words:
		if day_diff == -1:
			day = ls(32848).upper()
		elif day_diff == 0:
			day = ls(32849).upper()
		elif day_diff == 1:
			day = ls(32850).upper()
		elif 1 < day_diff < 7:
			day = date.strftime('%A').upper()
			day = ls(translate_day(day))
	return day

def translate_day(day):
	days = {'MONDAY': 32971, 'TUESDAY': 32972, 'WEDNESDAY': 32973, 'THURSDAY': 32974, 'FRIDAY': 32975, 'SATURDAY': 32976, 'SUNDAY': 32977}
	return days[day]

def calculate_age(born, str_format, died=None):
	''' born and died are str objects e.g. "1972-05-28" '''
	from datetime import date, datetime
	import time
	try: born = datetime.strptime(born, str_format)
	except TypeError: born = datetime(*(time.strptime(born, str_format)[0:6]))
	if not died:
		today = date.today()
	else:
		try: died = datetime.strptime(died, str_format)
		except TypeError: died = datetime(*(time.strptime(died, str_format)[0:6]))
		today = died
	return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def batch_replace(s, replace_info):
	for r in replace_info:
		s = str(s).replace(r[0], r[1])
	return s

def clean_file_name(s, use_encoding=False, use_blanks=True):
	try:
		hex_entities = [['&#x26;', '&'], ['&#x27;', '\''], ['&#xC6;', 'AE'], ['&#xC7;', 'C'],
					['&#xF4;', 'o'], ['&#xE9;', 'e'], ['&#xEB;', 'e'], ['&#xED;', 'i'],
					['&#xEE;', 'i'], ['&#xA2;', 'c'], ['&#xE2;', 'a'], ['&#xEF;', 'i'],
					['&#xE1;', 'a'], ['&#xE8;', 'e'], ['%2E', '.'], ['&frac12;', '%BD'],
					['&#xBD;', '%BD'], ['&#xB3;', '%B3'], ['&#xB0;', '%B0'], ['&amp;', '&'],
					['&#xB7;', '.'], ['&#xE4;', 'A'], ['\xe2\x80\x99', '']]
		special_encoded = [['"', '%22'], ['*', '%2A'], ['/', '%2F'], [':', ','], ['<', '%3C'],
							['>', '%3E'], ['?', '%3F'], ['\\', '%5C'], ['|', '%7C']]
		
		special_blanks = [['"', ' '], ['*', ' '], ['/', ' '], [':', ''], ['<', ' '],
							['>', ' '], ['?', ' '], ['\\', ' '], ['|', ' '], ['%BD;', ' '],
							['%B3;', ' '], ['%B0;', ' '], ["'", ""], [' - ', ' '], ['.', ' '],
							['!', ''], [';', ''], [',', '']]
		s = batch_replace(s, hex_entities)
		if use_encoding:
			s = batch_replace(s, special_encoded)
		if use_blanks:
			s = batch_replace(s, special_blanks)
		s = s.strip()
	except: pass
	return s

def clean_title(title):
	import re
	if title == None: return
	title = title.lower()
	title = re.sub('&#(\d+);', '', title)
	title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
	title = title.replace('&quot;', '\"').replace('&amp;', '&')
	title = re.sub(r'\<[^>]*\>','', title)
	title = re.sub('\n|([[].+?[]])|([(].+?[)])|\s(vs|v[.])\s|(:|;|-|"|,|\'|\_|\.|\?)|\(|\)|\[|\]|\{|\}|\s', '', title)
	title = re.sub('[^A-z0-9]', '', title)
	return title

def to_bytes(text):
	try:
		if isinstance(text, text_type):
			text = text.encode("utf-8")
	except:
		pass
	return text

def to_utf8(obj):
	try:
		import copy
		if isinstance(obj, unicode):
			obj = obj.encode('utf-8', 'ignore')
		elif isinstance(obj, dict):
			obj = copy.deepcopy(obj)
			for key, val in obj.items():
				obj[key] = to_utf8(val)
		elif obj is not None and hasattr(obj, "__iter__"):
			obj = obj.__class__([to_utf8(x) for x in obj])
		else: pass
	except: pass
	return obj

def byteify(data, ignore_dicts=False):
	try:
		if isinstance(data, unicode):
			return data.encode('utf-8')
		if isinstance(data, list):
			return [byteify(item, ignore_dicts=True) for item in data]
		if isinstance(data, dict) and not ignore_dicts:
			return dict([(byteify(key, ignore_dicts=True), byteify(value, ignore_dicts=True)) for key, value in data.iteritems()])
	except:
		pass
	return data

def normalize(txt):
	import re
	txt = re.sub(r'[^\x00-\x7f]',r'', txt)
	return txt

def safe_string(obj):
	try:
		try:
			return str(obj)
		except UnicodeEncodeError:
			return obj.encode('utf-8', 'ignore').decode('ascii', 'ignore')
		except:
			return ""
	except:
		return obj

def remove_accents(obj):
	import unicodedata
	try:
		obj = u'%s' % obj
		obj = ''.join(c for c in unicodedata.normalize('NFD', obj) if unicodedata.category(c) != 'Mn')
	except:
		pass
	return obj

def read_from_file(path, silent=False):
	import xbmcvfs
	try:
		f = xbmcvfs.File(path)
		r = f.read()
		f.close()
		return str(r)
	except:
		if not silent:
			pass
		return None

def regex_from_to(text, from_string, to_string, excluding=True):
	import re
	if excluding:
		r = re.search("(?i)" + from_string + "([\S\s]+?)" + to_string, text).group(1)
	else:
		r = re.search("(?i)(" + from_string + "[\S\s]+?" + to_string + ")", text).group(1)
	return r

def regex_get_all(text, start_with, end_with):
	import re
	r = re.findall("(?i)(" + start_with + "[\S\s]+?" + end_with + ")", text)
	return r

def remove_all(elements, list):
	return filter(lambda x: x not in elements, list)

def replace_html_codes(txt):
	try:
		from HTMLParser import HTMLParser
	except ImportError:
		from html.parser import HTMLParser
	import re
	txt = to_utf8(txt)
	txt = re.sub("(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", txt)
	txt = HTMLParser().unescape(txt)
	txt = txt.replace("&quot;", "\"")
	txt = txt.replace("&amp;", "&")
	return txt

def gen_file_hash(file):
	try:
		import hashlib
		md5_hash = hashlib.md5()
		with open(file, 'rb') as afile:
			buf = afile.read()
			md5_hash.update(buf)
			return md5_hash.hexdigest()
	except:
		import traceback
		traceback.print_exc()

def logger(heading, function):
	import xbmc
	xbmc.log('###%s###: %s' % (heading, function), 2)

def int_with_commas(number):
	'''helper to pretty format a number'''
	try:
		number = int(number)
		if number < 0:
			return '-' + int_with_commas(-number)
		result = ''
		while number >= 1000:
			number, number2 = divmod(number, 1000)
			result = ",%03d%s" % (number2, result)
		return "%d%s" % (number, result)
	except Exception:
		return ""

def try_parse_int(string):
	'''helper to parse int from string without erroring on empty or misformed string'''
	try:
		return int(string)
	except Exception:
		return 0

def writeDict(dict, filename, sep):
	with open(filename, "a") as f:
		for i in dict.keys():            
			f.write(i + " " + sep.join([str(x) for x in dict[i]]) + "\n")

def readDict(filename, sep):
	with open(filename, "r") as f:
		dict = {}
		for line in f:
			values = line.split(sep)
			dict[values[0]] = {int(x) for x in values[1:len(values)]}
		return(dict)

def sec2time(sec, n_msec=3):
	''' Convert seconds to 'D days, HH:MM:SS.FFF' '''
	if hasattr(sec,'__len__'):
		return [sec2time(s) for s in sec]
	m, s = divmod(sec, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	if n_msec > 0:
		pattern = '%%02d:%%02d:%%0%d.%df' % (n_msec+3, n_msec)
	else:
		pattern = r'%02d:%02d:%02d'
	if d == 0:
		return pattern % (h, m, s)
	return ('%d days, ' + pattern) % (d, h, m, s)
	
def sort_list(sort_key, sort_direction, list_data, ignore_articles=None):
	reverse = False if sort_direction == 'asc' else True
	if sort_key == 'rank':
		return sorted(list_data, key=lambda x: x['rank'], reverse=reverse)
	elif sort_key == 'added':
		return sorted(list_data, key=lambda x: x['listed_at'], reverse=reverse)
	elif sort_key == 'title':
		if ignore_articles is None:
			from modules.settings import ignore_articles as ignore
			ignore_articles = ignore()
		return sorted(list_data, key=lambda x: title_key(x[x['type']].get('title'), ignore_articles), reverse=reverse)
	elif sort_key == 'released':
		return sorted(list_data, key=lambda x: released_key(x[x['type']]), reverse=reverse)
	elif sort_key == 'runtime':
		return sorted(list_data, key=lambda x: x[x['type']].get('runtime', 0), reverse=reverse)
	elif sort_key == 'popularity':
		return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
	elif sort_key == 'percentage':
		return sorted(list_data, key=lambda x: x[x['type']].get('rating', 0), reverse=reverse)
	elif sort_key == 'votes':
		return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
	elif sort_key == 'random':
		import random
		return sorted(list_data, key=lambda k: random.random())
	else:
		return list_data

def imdb_sort_list():
	# From Exodus Codebase
	from modules.settings_reader import get_setting
	sort = int(get_setting('imdb_lists.sort_type'))
	sort_order = int(get_setting('imdb_lists.sort_direction'))
	if sort == 0: # Default
		imdb_sort = 'list_order'
	elif sort == 1: # Alphabetical
		imdb_sort = 'alpha'
	elif sort == 2: # IMDb Rating
		imdb_sort = 'user_rating'
	elif sort == 3: # Popularity
		imdb_sort = 'moviemeter'
	elif sort == 4: # Your Rating
		imdb_sort = 'your_rating'
	elif sort == 5: # Number Of Ratings
		imdb_sort = 'num_votes'
	elif sort == 6: # Release Date
		imdb_sort = 'release_date'
	elif sort == 7: # Runtime 
		imdb_sort = 'runtime'
	elif sort == 8: # Date Added
		imdb_sort = 'date_added'
	imdb_sort_order = ',asc' if sort_order == 0 else ',desc'
	sort_string = imdb_sort + imdb_sort_order
	return sort_string

def released_key(item):
	if 'released' in item:
		return item['released']
	elif 'first_aired' in item:
		return item['first_aired']
	else:
		return 0

def title_key(title, ignore_articles=None):
	if ignore_articles is None:
		from modules.settings import ignore_articles as ignore
		ignore_articles = ignore()
	if not ignore_articles: return title
	import re
	try:
		if title is None: title = ''
		articles = ['the', 'a', 'an']
		match = re.match('^((\w+)\s+)', title.lower())
		if match and match.group(2) in articles: offset = len(match.group(1))
		else: offset = 0
		return title[offset:]
	except: return title

def selection_dialog(dialog_list, function_list, string='Fen'):
	import xbmcgui
	dialog = xbmcgui.Dialog()
	list_choice = dialog.select(string, dialog_list)
	if list_choice >= 0: return function_list[list_choice]
	else: return None

def confirm_dialog():
	import xbmcgui
	if xbmcgui.Dialog().yesno('Fen', local_string(32580)): return True
	return False

def multiselect_dialog(string, dialog_list, function_list=None, preselect= []):
	import xbmcgui
	dialog = xbmcgui.Dialog()
	if not function_list: function_list = dialog_list
	list_choice = dialog.multiselect(string, dialog_list, preselect=preselect)
	return [function_list[i] for i in list_choice] if list_choice is not None else list_choice

def toggle_jump_to():
	from modules.nav_utils import toggle_setting, notification
	from modules.settings import nav_jump_use_alphabet
	ls = local_string
	use_alphabet = nav_jump_use_alphabet()
	(setting, new_action) = ('0', ls(32022)) if use_alphabet == True else ('1', ls(32023))
	toggle_setting(setting_id='nav_jump', setting_value=setting, refresh=True)
	notification(ls(32851) % new_action)
