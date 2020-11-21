# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import json
# from modules.utils import logger

window = xbmcgui.Window(10000)

def internal_results(provider, sources):
	window.setProperty('%s.internal_results' % provider, json.dumps(sources))

def label_settings(scraper_settings, scrape_provider, scraper_name=None):
	from modules.settings import provider_color as prov_color
	scraper_settings = json.loads(scraper_settings)
	provider_color = prov_color(scrape_provider)
	second_line_color = scraper_settings['multiline_highlight']
	if scraper_name: scrape_provider = scraper_name
	if provider_color == '':
		single_leading = ''
		single_closing = ''
		multi1_leading = ''
		multi1_closing = ''
	else:
		single_leading = '[COLOR=%s]' % provider_color
		single_closing = '[/COLOR]'
		multi1_leading = '[COLOR=%s]' % provider_color
		multi1_closing = '[/COLOR]'
	if second_line_color == '':
		multi2_leading = multi1_leading
		multi2_closing = multi1_closing
	else:
		multi2_leading = '[COLOR=%s]' % second_line_color
		multi2_closing = '[/COLOR]'
	updates = {'scrape_provider':scrape_provider, 'single_leading': single_leading, 'single_closing': single_closing, 'multi1_leading': multi1_leading,
			   'multi1_closing': multi1_closing, 'multi2_leading': multi2_leading, 'multi2_closing': multi2_closing, 'provider_color': provider_color,
			   'second_line_color': second_line_color}
	scraper_settings.update(updates)
	return scraper_settings

def build_internal_scrapers_label(label_settings, file_name, details, size, video_quality, **kwargs):
	show_filenames = label_settings['show_filenames']
	show_extra_info = label_settings['extra_info']
	scraper_name = label_settings['scrape_provider']
	if show_filenames: filename = file_name.replace('.', ' ')
	else: filename = ''
	if not show_extra_info: details = ''
	if kwargs:
		result_type = ''
		if kwargs['uncached']:
			if kwargs['active_download']: result_type += ' | [B]ACTIVE[/B]'
			else: result_type += ' | [B]UNCACHED[/B]'
		if video_quality.upper() in ['4K', '1080P', '720P']:
			label = '[B]%s HOST[/B] | [B]%s[/B] | %.2f GB%s' % (scraper_name, video_quality, size, result_type)
			multiline_label1 = '[B]%s HOST[/B] | [B]%s[/B] | %.2f GB%s' % (scraper_name, video_quality, size, result_type)
		else:
			label = '[B]%s HOST[/B] | [I]%s[/I]  | %.2f GB%s' % (scraper_name, video_quality, size, result_type)
			multiline_label1 = '[B]%s HOST[/B] | [I]%s[/I]  | %.2f GB%s' % (scraper_name, video_quality, size, result_type)
		if kwargs['files_num_video'] > 3:
			label += ' | [B]PACK[/B]'
			multiline_label1 += ' | [B]PACK[/B]'
	else:
		if video_quality.upper() in ['4K', '1080P', '720P']:
			label = '[B]%s[/B] | [B]%s[/B] | %.2f GB' % (scraper_name, video_quality, size)
			multiline_label1 = '[B]%s[/B] | [B]%s[/B] | %.2f GB' % (scraper_name, video_quality, size)
		else:
			label = '[B]%s[/B] | [I]%s[/I]  | %.2f GB' % (scraper_name, video_quality, size)
			multiline_label1 = '[B]%s[/B] | [I]%s[/I]  | %.2f GB' % (scraper_name, video_quality, size)
	if show_extra_info: label += ' | %s' % details
	multiline_label2 = ''
	if show_filenames:
		label += ' | %s' % filename
		multiline_label1 += ' | %s' % details
		multiline_label2 += '\n         %s' % filename
	else:
		multiline_label2 += '\n         %s' % details
	label = label.replace('| 0 |', '|').replace(' | [I]0 [/I]', '').replace('[I] [/I] | ', '')
	label = label.upper()
	multiline_label1 = multiline_label1.replace('| 0 |', '|').replace(' | [I]0 [/I]', '').replace('[I] [/I] | ', '')
	multiline_label1 = multiline_label1.upper()
	if multiline_label2 != '':
		multiline_label2 = multiline_label2.replace('| 0 |', '|').replace(' | [I]0 [/I]', '').replace('[I] [/I] | ', '')
		multiline_label2 = multiline_label2.upper()
	return make_labels(label_settings, label, multiline_label1, multiline_label2, video_quality, **kwargs)

def make_labels(label_settings, label, multiline_label1, multiline_label2, video_quality, **kwargs):
	if kwargs and kwargs['uncached']:
		if label_settings['second_line_color'] == '': multiline_open = ''
		else: multiline_open = '[COLOR %s]' % label_settings['second_line_color']
		if multiline_open == '': multiline_close = ''
		else: multiline_close = '[/COLOR]'
		provider_color = label_settings['provider_color']
		files_num_video = str(kwargs['files_num_video'])
		label = '[I]' + label.replace('[B]FURK[/B]', '[COLOR %s][B]FURK[/B][/COLOR]' % provider_color).replace('[B]FURK PACK (X%s)[/B]' % files_num_video, '[COLOR %s][B]FURK PACK (X%s)[/B][/COLOR]' % (provider_color, files_num_video)).replace('[B]UNCACHED[/B]', '[COLOR %s][B]UNCACHED[/B][/COLOR]' % provider_color).replace('[B]ACTIVE[/B]', '[COLOR lawngreen][B]ACTIVE[/B][/COLOR]').replace('[/I]', '') + '[/I]'
		multiline_label = '[I]' + multiline_label1.replace('[B]FURK[/B]', '[COLOR %s][B]FURK[/B][/COLOR]' % provider_color).replace('[B]FURK PACK (X%s)[/B]' % files_num_video, '[COLOR %s][B]FURK PACK (X%s)[/B][/COLOR]' % (provider_color, files_num_video)).replace('[B]UNCACHED[/B]', '[COLOR %s][B]UNCACHED[/B][/COLOR]' % provider_color).replace('[B]ACTIVE[/B]', '[COLOR lawngreen][B]ACTIVE[/B][/COLOR]').replace('[/I]', '') + multiline_open + multiline_label2 + multiline_close + '[/I]'
	elif label_settings['highlight_type'] == '1':
		if video_quality.upper() == '4K': leading_color = label_settings['highlight_4K']
		elif video_quality.upper()  == '1080P': leading_color = label_settings['highlight_1080p']
		elif video_quality.upper() == '720P': leading_color = label_settings['highlight_720p']
		else: leading_color = label_settings['highlight_SD']
		if label_settings['multiline_highlight'] == '': multiline_open = leading_color
		else: multiline_open = label_settings['multiline_highlight']
		label = '[COLOR=%s]' % leading_color + label + '[/COLOR]'
		multiline_label = '[COLOR=%s]' % leading_color + multiline_label1 + '[/COLOR]' + '[COLOR=%s]' % multiline_open + multiline_label2 + '[/COLOR]'
	else:
		label = label_settings['single_leading'] + label + label_settings['single_closing']
		multiline_label = label_settings['multi1_leading'] + multiline_label1 + label_settings['multi1_closing'] + label_settings['multi2_leading'] + multiline_label2 + label_settings['multi2_closing']
	return label, multiline_label
