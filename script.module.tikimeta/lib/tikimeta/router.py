# -*- coding: utf-8 -*-

try: from urlparse import parse_qsl
except ImportError: from urllib.parse import parse_qsl
# from tikimeta.utils import logger

def routing(argv):
	params = dict(parse_qsl(argv.replace('?','')))
	mode = params.get('mode', 'navigator.main')
	if mode == 'clear_cache':
		import tikimeta
		tikimeta.delete_meta_cache()
	elif mode == 'set_language':
		import tikimeta
		tikimeta.choose_language()
	elif mode == 'clear_tvdb_token':
		from tikimeta.utils import clear_tvdb_token
		clear_tvdb_token()