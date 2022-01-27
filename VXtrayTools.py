#!/usr/bin/env python
# Module     : SysTrayIcon.py
# Synopsis   : Windows System tray icon.
# Programmer : Simon Brunning - simon@brunningonline.net
# Date       : 11 April 2005
# Notes      : Based on (i.e. ripped off from) Mark Hammond's
#              win32gui_taskbar.py and win32gui_menu.py demos from PyWin32
'''TODO

For now, the demo at the bottom shows how to use it...'''
         
import os
import sys

import subprocess

import win32ui #new added

import win32api
import win32con
import win32gui_struct
from configobj import ConfigObj
from menuoption_logcons_dll import *
try:
    import winxpgui as win32gui
except ImportError:
    import win32gui

class SysTrayIcon(object):
    '''TODO'''
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]
    
    FIRST_ID = 1023
    
    def __init__(self,
                 icon,
                 hover_text,
                 menu_options,
                 on_quit=None,
                 default_menu_index=None,
                 window_class_name=None,):
        
        self.icon = icon
        self.hover_text = hover_text
        self.on_quit = on_quit
        
        self.menu_options = menu_options

        self.reloadMenuOptions(self.menu_options)
        
        
        self.default_menu_index = (default_menu_index or 0)
        self.window_class_name = window_class_name or "SysTrayIconPy"
        
        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
                       win32con.WM_DESTROY: self.destroy,
                       win32con.WM_COMMAND: self.command,
                       win32con.WM_USER+20 : self.notify,}
        # Register the Window class.
        window_class = win32gui.WNDCLASS()
        hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(window_class)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom,
                                          self.window_class_name,
                                          style,
                                          0,
                                          0,
                                          win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT,
                                          0,
                                          0,
                                          hinst,
                                          None)
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()
        
        win32gui.PumpMessages()

    def reloadMenuOptions(self, menu_options):
        self.menu_options = None
        self._next_action_id = self.FIRST_ID
        self.menu_actions_by_id = set()
        self.menu_actions_params_by_id = set()
        lista = list(menu_options)
        lista.append( ('Quit', None, self.QUIT, None) ) 
        self.menu_options = self._add_ids_to_menu_options( lista )
        self.menu_actions_by_id = dict(self.menu_actions_by_id)
        self.menu_actions_params_by_id = dict(self.menu_actions_params_by_id)
        del self._next_action_id

    def _add_ids_to_menu_options(self, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_icon, option_action, option_action_params = menu_option
            if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
                self.menu_actions_by_id.add((self._next_action_id, option_action))
                self.menu_actions_params_by_id.add((self._next_action_id, option_action_params))
                result.append(menu_option + (self._next_action_id,))
            elif non_string_iterable(option_action):
                result.append((option_text,
                               option_icon,
                               self._add_ids_to_menu_options(option_action),
                               option_action_params,
                               self._next_action_id))
            else:
                print('Unknown item', option_text, option_icon, option_action, option_action_params)
            self._next_action_id += 1
        return result
        
    def refresh_icon(self):
        # Try and find a custom icon
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:
            print("Can't find icon file - using default.")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_id: message = win32gui.NIM_MODIFY
        else: message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd,
                          0,
                          win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                          win32con.WM_USER+20,
                          hicon,
                          self.hover_text)
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def restart(self, hwnd, msg, wparam, lparam):
        self.refresh_icon()

    def destroy(self, hwnd, msg, wparam, lparam):
        if self.on_quit: self.on_quit(self)
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0) # Terminate the app.

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam==win32con.WM_LBUTTONDBLCLK:
            self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
        elif lparam==win32con.WM_RBUTTONUP:
            self.show_menu()
        elif lparam==win32con.WM_LBUTTONUP:
            pass
        return True
        
    def show_menu(self):
        menu = win32gui.CreatePopupMenu()
        self.create_menu(menu, self.menu_options)
        #win32gui.SetMenuDefaultItem(menu, 1000, 0)
        
        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
    
    def create_menu(self, menu, menu_options):
        for option_text, option_icon, option_action, option_action_params, option_id in menu_options[::-1]: #lets go in reversed order
            if option_icon:
                option_icon = self.prep_menu_icon(option_icon)
            #option_icon = self.prep_menu_icon_from_dll('c:/windows/system32/shell32.dll',0)
            #option_icon = self.prep_menu_icon(option_icon)
            #https://docs.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-menuiteminfoa
            if option_id in self.menu_actions_by_id:                
                if option_text == "-":
                    fType = 0x00000800 #MFT_SEPARATOR 0x00000800L Specifies that the menu item is a separator. A menu item separator appears as a horizontal dividing line. The dwTypeData and cch members are ignored. This value is valid only in a drop-down menu, submenu, or shortcut menu.  
                else:
                    fType= 0x0 
                item, extras = win32gui_struct.PackMENUITEMINFO(fType=fType, text=option_text,
                                                                    hbmpItem=option_icon,
                                                                    wID=option_id)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                self.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(self, icon):
        # First load the icon.
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hIcon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        #If you're working with the Windows API then I would be consistent, so use LoadBitmap (or LoadIimage), that will give you a valid HBITMAP (which is just a long number or DWORD) which you can work with.

        hwndDC = win32gui.GetWindowDC(self.hwnd)
        #win32gui.SetBkMode(hwndDC,win32con.TRANSPARENT) 
        dc = win32ui.CreateDCFromHandle(hwndDC)
        
        memDC = dc.CreateCompatibleDC()
        iconBitmap = win32ui.CreateBitmap()
        iconBitmap.CreateCompatibleBitmap(dc, ico_x, ico_y)
        oldBmp = memDC.SelectObject(iconBitmap)
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)

        win32gui.FillRect(memDC.GetSafeHdc(), (0, 0, ico_x, ico_y), brush)
        win32gui.DrawIconEx(memDC.GetSafeHdc(), 0, 0, hIcon , ico_x, ico_y, 0, 0, win32con.DI_NORMAL)

        memDC.SelectObject(oldBmp)
        memDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwndDC)

        return iconBitmap.GetHandle()


    def prep_menu_icon_from_dll(self, dllName, iconIndex):
        # First load the icon.
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)

        large, small = win32gui.ExtractIconEx(dllName,iconIndex)
        win32gui.DestroyIcon(large[0])

        hwndDC = win32gui.GetWindowDC(self.hwnd)    
        #win32gui.SetBkMode(hwndDC,win32con.TRANSPARENT)
        dc = win32ui.CreateDCFromHandle(hwndDC)
         
        memDC = dc.CreateCompatibleDC()
        iconBitmap = win32ui.CreateBitmap()
        iconBitmap.CreateCompatibleBitmap(dc, ico_x, ico_y)
        oldBmp = memDC.SelectObject(iconBitmap)
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)

        win32gui.FillRect(memDC.GetSafeHdc(), (0, 0, ico_x, ico_y), brush)
        win32gui.DrawIconEx(memDC.GetSafeHdc(), 0, 0, small[0] , ico_x, ico_y, 0, 0, win32con.DI_NORMAL)

        memDC.SelectObject(oldBmp)
        memDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwndDC)

        return iconBitmap.GetHandle()        



    def command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        self.execute_menu_option(id)
        
    def execute_menu_option(self, id):
        menu_action = self.menu_actions_by_id[id]      
        menu_action_params = self.menu_actions_params_by_id[id]     
        if menu_action == self.QUIT:
            win32gui.DestroyWindow(self.hwnd)
        else:
            if (menu_action_params):
                menu_action(self,menu_action_params)
            else: 
                menu_action(self)
            
def non_string_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return not isinstance(obj, str)

# Minimal self test. You'll need a bunch of ICO files in the current working
# directory in order for this to work...
if __name__ == '__main__':
    import itertools, glob
    
    icons = itertools.cycle(glob.glob('*.ico'))
    hover_text = "VX Tray Tools"
    def hello(sysTrayIcon): print("Hello World.")
    def simon(sysTrayIcon): print("Hello Simon.")
    def open_folder(sysTrayIcon,path): 
        print("Opening folder {0}".format(path))
        path_to_explorer = 'C:\\Windows\\explorer.exe'
        path_to_file = path
        subprocess.call([path_to_explorer, path_to_file])
    def open_file(sysTrayIcon,tuple): 
        print("Opening file {0}".format(tuple))
        path_to_exe = tuple[0]
        path_to_file = tuple[1]
        subprocess.call([path_to_exe, path_to_file])        
    def vx_logs_switcher(sysTrayIcon,path): 
        switch_logcons(path)
        sysTrayIcon.reloadMenuOptions(build_menu_options())
        #sysTrayIcon.restart ( sysTrayIcon.hwnd , win32con.WM_DESTROY, win32con.WM_COMMAND, win32con.WM_USER+20 )
        #sysTrayIcon.show_menu() # SysTrayIcon(next(icons), hover_text, menu_options, on_quit=bye, default_menu_index=1)
    #

    def build_menu_options():
        "F:\Games\VX\Binaries\extensions.ini"
        ##############################################################################################################
        files_config = ConfigObj("config_main.ini")
        menu_entries = ()
        for section in files_config.keys():
            if "extensions.ini" == section:
                alias = files_config[section]["alias"]
                path = files_config[section]["path"]
                menu_options = ( (read_logcons_dll_status(path), "icon_console.ico", vx_logs_switcher, path), )
        ##############################################################################################################        
        #menu_options = menu_options + (('Say Hello', next(icons), hello, None),)
        menu_options = menu_options + ( ("-", None, hello, None), )
        #menu_options = menu_options + ( ('Logs switcher', None, vx_logs_switcher, None), )
        #menu_options = menu_options + ( ('Switch Icon', None, switch_icon, None), )                
        """         menu_options = menu_options + (     ('A sub-menu', next(icons), ( ('Say Hello to Simon', next(icons), simon, None),
                                                    ('Switch Icon', next(icons), switch_icon, None),
                                                    ) , None
                                            ),
                                    ) """
        ##############################################################################################################
        files_config = ConfigObj("config_files.ini")
        menu_entries = ()
        for section in files_config.keys():
            if "file_" in section:
                alias = files_config[section]["alias"]
                app = files_config[section]["app"]
                params = files_config[section]["params"]
                icon = files_config[section]["icon"]
                menu_entry = ( (alias, None, open_file, (app,params), ), ) #
                menu_entries = menu_entries + menu_entry
        menu_options = menu_options + ( ('Files', "icon_files.ico", ( menu_entries ), None ), )
        ###############################################################################################################
        menu_options = menu_options + ( ("-", None, hello, None), )
        ###############################################################################################################
        folders_config = ConfigObj("config_folders.ini")
        menu_entries = ()
        for section in folders_config.keys():
            if "folder_" in section:
                alias = folders_config[section]["alias"]
                path = folders_config[section]["path"]
                icon = folders_config[section]["icon"]
                menu_entry = ( (alias, None, open_folder, (path), ), ) #
                menu_entries = menu_entries + menu_entry
        menu_options = menu_options + ( ('Folders', "icon_folders.ico", ( menu_entries ), None ), )
        ###############################################################################################################
        menu_options = menu_options + ( ("-", None, hello, None), )
        ###############################################################################################################
        return menu_options
    def switch_icon(sysTrayIcon):
        sysTrayIcon.icon = next(icons)
        sysTrayIcon.refresh_icon()
    
    menu_options = build_menu_options()

    def bye(sysTrayIcon): print('Bye, then.')
    


    SysTrayIcon("icon_vx.ico", hover_text, menu_options, on_quit=bye, default_menu_index=1)
