# -*- coding: utf-8 -*-

from apis import simplejson as json
from windows.base_dialog import BaseDialog
from modules.nav_utils import build_url
from modules.utils import local_string as ls
# from modules.utils import logger

class SourceResults(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(SourceResults, self).__init__(self, args)
		self.window_id = 2000
		self.results = kwargs.get('results')
		self.meta = kwargs.get('meta')
		self.scraper_settings = kwargs.get('scraper_settings')
		self.file_scrapers = kwargs.get('file_scrapers')
		self.prescrape = kwargs.get('prescrape')
		self.failed_results = []

	def onInit(self):
		super(SourceResults, self).onInit()
		self.make_items()
		self.set_properties(self.meta, self.total_results)
		win = self.getControl(self.window_id)
		win.addItems(self.item_list)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		return self.selected

	def onAction(self, action):
		action_id = action.getId()
		if action_id in self.selection_actions:
			if self.prescrape:
				chosen_listitem = self.item_list[self.get_position(self.window_id)]
				if chosen_listitem.getProperty('fen.perform_full_search') == 'true':
					self.selected = ('perform_full_search', '')
					return self.close()
			self.selected = ('play', self.results[self.get_position(self.window_id)])
			return self.close()
		elif action_id in self.context_actions:
			item = self.results[self.get_position(self.window_id)]
			cache_provider = item.get('cache_provider', '')
			scrape_provider = item['scrape_provider']
			uncached_torrent = True if 'Uncached' in cache_provider else False
			if not uncached_torrent and scrape_provider not in self.file_scrapers:
				self.context_menu(item, cache_provider, scrape_provider)
				if self.contextmenu_action:
					self.execute_code(self.contextmenu_action)
		elif action_id in self.closing_actions:
			self.selected = (None, '')
			return self.close()

	def make_items(self):
		def builder():
			for count, item in enumerate(self.results, 1):
				try:
					listitem = self.make_listitem()
					scrape_provider = item['scrape_provider']
					source = item.get('source').upper()
					try: name = item.get('URLName', 'N/A').upper()
					except: name = 'N/A'
					if item.get('package', 'false') in ('true', 'show', 'season'): extraInfo = '[B]PACK[/B] | %s' % item.get('extraInfo', '')
					else: extraInfo = item.get('extraInfo', '')
					if scrape_provider == 'external':
						source_site = item.get('name_rank').upper()
						provider = item.get('debrid', source_site).replace('.me', '').upper()
						if 'cache_provider' in item:
							if 'Uncached' in item['cache_provider']:
								listitem.setProperty('fen.source_type', 'UNCACHED')
								listitem.setProperty('fen.highlight', 'white')
							else:
								listitem.setProperty('fen.source_type', 'CACHED')
								listitem.setProperty('fen.highlight', torrent_highlight)
						else:
							listitem.setProperty('fen.source_type', source)
							listitem.setProperty('fen.highlight', hoster_highlight)
						listitem.setProperty('fen.name', name)
						listitem.setProperty('fen.provider', provider)
						listitem.setProperty('fen.source_site', source_site)
					else:
						highlight = '%s_highlight' % scrape_provider
						if 'folder' in scrape_provider: listitem.setProperty('fen.highlight', self.scraper_settings['folders_highlight'])
						else: listitem.setProperty('fen.highlight', self.scraper_settings[highlight])
						listitem.setProperty('fen.name', name)
						listitem.setProperty('fen.source_type', source)
						listitem.setProperty('fen.provider', source)
						listitem.setProperty('fen.source_site', 'DIRECT')
					listitem.setProperty('fen.size_label', item.get('size_label', 'N/A'))
					listitem.setProperty('fen.extra_info', extraInfo)
					listitem.setProperty('fen.quality', item.get('quality', 'SD').upper())
					listitem.setProperty('fen.count', '%02d.' % count)
					yield listitem
				except:
					self.failed_results.append(item)
					pass
		hoster_highlight = self.scraper_settings['hoster_highlight']
		torrent_highlight = self.scraper_settings['torrent_highlight']
		self.item_list = list(builder())
		if self.prescrape:
			prescrape_listitem = self.make_listitem()
			prescrape_listitem.setProperty('fen.perform_full_search', 'true')
			prescrape_listitem.setProperty('fen.start_full_scrape', '[B]***%s***[/B]' % ls(33023).upper())
		self.results = [i for i in self.results if not i in self.failed_results]
		self.total_results = str(len(self.item_list))
		if self.prescrape: self.item_list.append(prescrape_listitem)

	def context_menu(self, item, cache_provider, scrape_provider):
		down_str, browse_str, browse_debrid_str, addto_str, down_archive_str = ls(32747), ls(32811), ls(33004), ls(32769), ls(32982)
		contextmenu_items = []
		meta_json = json.dumps(self.meta)
		title = item.get('title')
		item_id = item.get('id', None)
		name = item.get('name')
		url_dl = item.get('url_dl')
		source = json.dumps([item])
		down_file_params = {'mode': 'downloader',
							'action': 'meta.single',
							'name': self.meta.get('rootname', ''),
							'source': source,
							'url': None,
							'provider': scrape_provider,
							'meta': meta_json}
		contextmenu_items.append((down_str, 'RunPlugin(%s)' % build_url(down_file_params)))
		if 'package' in item and not scrape_provider == 'furk':
			browse_debrid_pack_params = {'mode': 'browse_debrid_pack',
										'provider': cache_provider,
										'name': name,
										'magnet_url': item['url'],
										'info_hash': item['hash']}
			down_arch_params = {'mode': 'downloader',
							'action': 'meta.pack',
							'name': self.meta.get('rootname', ''),
							'source': source,
							'url': None,
							'provider': scrape_provider,
							'meta': meta_json}
			# contextmenu_items.append((down_archive_str, 'RunPlugin(%s)' % build_url(down_arch_params)))
			contextmenu_items.append((browse_debrid_str, 'RunPlugin(%s)'  % build_url(browse_debrid_pack_params)))
		elif scrape_provider == 'furk':
			add_files_params = {'mode': 'furk.add_to_files',
								'name': name,
								'item_id': item_id}
			if item.get('package', 'false') == 'true':
				import os
				from modules.settings import get_theme
				default_furk_icon = os.path.join(get_theme(), 'furk.png')
				browse_pack_params = {'mode': 'furk.browse_packs',
									'file_name': name,
									'file_id': item_id}
				down_arch_params = {'mode': 'downloader',
								'db_type': 'furk.pack',
								'action': 'furk.pack',
								'name': self.meta.get('rootname', ''),
								'source': source,
								'url': url_dl,
								'provider': scrape_provider,
								'image': default_furk_icon}
				# contextmenu_items.append((down_archive_str,'RunPlugin(%s)' % build_url(down_arch_params)))
				contextmenu_items.append((browse_str, 'RunPlugin(%s)'  % build_url(browse_pack_params)))
			contextmenu_items.append((addto_str, 'RunPlugin(%s)'  % build_url(add_files_params)))
		self.contextmenu_action = self.contextmenu(contextmenu_items)

	def set_properties(self, meta, total_results):
		self.setProperty('fen.fanart', self.meta['fanart'])
		self.setProperty('fen.poster', self.meta['poster'])
		self.setProperty('fen.plot', self.meta['plot'])
		self.setProperty('fen.total_results', self.total_results)

