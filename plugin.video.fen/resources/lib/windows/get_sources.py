"""
    tknorris shared module
    Copyright (C) 2016 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import xbmcgui, xbmcaddon
from modules.settings import skin_location
from modules.utils import logger

class getSources(object):
    # dialog = None
        
    def create(self, heading, line1='', line2='', line3=''):
        self.dialog = getSources.Window('get_sources.default.xml', skin_location())
        self.dialog.show()
        self.dialog.setHeading(heading)
        self.dialog.setLine1(line1)
        self.dialog.setLine2(line2)
        self.dialog.setLine3(line3)
    
    def update(self, percent, line1='', line2='', line3=''):
        self.dialog.setProgress(percent)
        if line1: self.dialog.setLine1(line1)
        if line2: self.dialog.setLine2(line2)
        if line3: self.dialog.setLine3(line3)
    
    def iscanceled(self):
        logger('iscanceled called', '')
        return self.dialog.cancel
    
    def close(self):
        self.dialog.close()
        del self.dialog

    class Window(xbmcgui.WindowXMLDialog):
        HEADING_CTRL = 100
        LINE1_CTRL = 10
        LINE2_CTRL = 11
        LINE3_CTRL = 12
        PROGRESS_CTRL = 20
        ACTION_PREVIOUS_MENU = 10
        ACTION_BACK = 92
        CANCEL_BUTTON = 200
        cancel = False
            
        def onInit(self):
            pass

            
        def onAction(self, action):
            logger('onAction action', action)
            if action == self.ACTION_PREVIOUS_MENU or action == self.ACTION_BACK:
                self.cancel = True
                self.close()
    
        def onControl(self, control):
            pass
    
        def onFocus(self, control):
            pass
    
        def onClick(self, control):
            logger('onclick control', control)
            if control == self.CANCEL_BUTTON:
                self.cancel = True
                self.close()
        
        def setHeading(self, heading):
            self.setLabel(self.HEADING_CTRL, heading)
            
        def setProgress(self, progress):
            self.getControl(self.PROGRESS_CTRL).setPercent(progress)
    
        def setLine1(self, line):
            self.setLabel(self.LINE1_CTRL, line)
            
        def setLine2(self, line):
            self.setLabel(self.LINE2_CTRL, line)
            
        def setLine3(self, line):
            self.setLabel(self.LINE3_CTRL, line)
            
        def setLabel(self, ctrl, line):
            self.getControl(ctrl).setLabel(line)
