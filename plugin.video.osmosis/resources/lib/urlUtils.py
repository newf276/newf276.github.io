# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import Globals


def stripUnquoteURL(url):
    try:
        import urllib.parse as urllib
    except:
        import urllib

    if url.startswith('image://'):
        url = urllib.unquote_plus(url.replace('image://', '').strip('/'))
    else:
        url = urllib.unquote_plus(url.strip('/'))
    return url


def getURL(par):
    globals = Globals()
    try:
        if par.startswith('?url=plugin://{0}/'.format(globals.PLUGIN_ID)):
            url = par.split('?url=')[1]
        else:
            url = par.split('?url=')[1]
            url = url.split('&mode=')[0]
    except:
        url = None
    return url
