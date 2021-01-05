# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from kodi_six.utils import py2_decode

import re

import xbmcvfs

from .common import Globals, Settings
from .create import fillPluginItems
from .fileSys import readMediaList
from .guiTools import selectDialog
from .l10n import getString
from .moduleUtil import getModule
from .stringUtils import getProviderId, getStrmname, parseMediaListURL

actor_update_manual = 0
actor_update_periodictime = 1
actor_update_fixtime = 2
actor_update_kodistart = 3


def strm_update(selectedItems=None, actor=0):
    globals = Globals()
    thelist = sorted(readMediaList())
    if not selectedItems and actor == actor_update_manual:
        selectActions = [dict(id='Movies', string_id=39111), dict(id='TV-Shows', string_id=39112), dict(id='Audio', string_id=39113), dict(id='All', string_id=39122)]
        choice = selectDialog('{0}: {1}'.format(getString(39123, globals.addon), getString(39109, globals.addon)), [getString(selectAction.get('string_id')) for selectAction in selectActions])
        if choice == -1:
            return
        elif choice == 3:
            cTypeFilter = None
        else:
            cTypeFilter = selectActions[choice].get('id')
    else:
        cTypeFilter = None

    items = selectedItems if selectedItems else [{'entry': item} for item in thelist]
    if len(items) > 0:
        settings = Settings()
        if settings.SHOW_UPDATE_PROGRESS and \
                ((actor == 0 and settings.SHOW_UPDATE_PROGRESS_MANUALLY) or \
                ((actor == 1 or actor == 2) and settings.SHOW_UPDATE_PROGRESS_SCHEDULED) or \
                (actor == 3 and settings.SHOW_UPDATE_PROGRESS_STARTUP)):
            pDialog = globals.dialogProgressBG
            pDialog.create(getString(39140, globals.addon))
        else:
            pDialog = None

        iUrls = 0
        splittedEntries = []
        for item in items:
            splits = item.get('entry').split('|')
            if cTypeFilter and not re.findall(cTypeFilter, splits[0]):
                continue
            iUrls += len(splits[2].split('<next>'))
            splittedEntries.append(splits)

        if iUrls == 0:
            if pDialog:
                pDialog.close()
            return

        tUrls = iUrls
        step = j = 100 / tUrls
        for index, splittedEntry in enumerate(splittedEntries):
            cType, name, url = splittedEntry[0], splittedEntry[1], splittedEntry[2]

            urls = url.split('<next>')
            for url in urls:
                name_orig, plugin_url = parseMediaListURL(url)
                plugin_id = getProviderId(plugin_url).get('plugin_id')
                if plugin_id:
                    module = getModule(plugin_id)
                    if module and hasattr(module, 'update'):
                        url = module.update(name, url, 'video', thelist)

                if pDialog:
                    pDialog.update(int(j), heading='{0}: {1}/{2}'.format(getString(39140, globals.addon), (index + 1), iUrls), message='\'{0}\' {1}'.format(getStrmname(name), getString(39134, globals.addon)))
                j += step

                fillPluginItems(url, strm=True, strm_name=name, strm_type=cType, name_orig=name_orig, pDialog=pDialog)
                tUrls -= 1
        if pDialog:
            pDialog.close()

        if actor == actor_update_periodictime:
            globals.dialog.notification(getString(39123, globals.addon), '{0} {1}h'.format(getString(39136, globals.addon), settings.SCHEDULED_UPDATE_INTERVAL), globals.MEDIA_ICON, 5000, True)
        elif actor == actor_update_fixtime:
            globals.dialog.notification(getString(39123, globals.addon), '{0} {1}h'.format(getString(39137, globals.addon), settings.SCHEDULED_UPDATE_TIME), globals.MEDIA_ICON, 5000, True)
