#!/usr/bin/python

###############################################################################
## Description
###############################################################################
# Functions for web browser automations.
# Using selenium webdrivers (chrome and firefox supported)

###############################################################################
## Imports 
###############################################################################
import tkinter as tk
from pathlib import Path
from urllib.parse import urlparse

import browser_cookie3, requests, win32com.client

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys

###############################################################################
## Constants
###############################################################################
PROMPTS = {
    'fail':             'Failed to create {} instance',
    'ready':            '{} ready to work.'
}

root = Path(__file__).absolute().parent.parent
driver_path = root.joinpath('depository/drivers')

# initialize autoit
try:
    autoit = win32com.client.Dispatch('AutoItX3.Control')
except:
    print('Autoit 3 is not installed. Limited functionality')
    autoit = None
# win_pattern = {
#     'chrome': {
#         'title': '[TITLE:{} - Google Chrome; CLASS:Chrome_WidgetWin_1]',
#     }
# }
###############################################################################
## Classes 
###############################################################################
class DriverMaster():

    def __init__(self):
        pass

    def parse_cookies(self):
        cookiejar = requests.cookies.RequestsCookieJar()
        cookies = self.get_cookies()
        for cookie in cookies:
            name, val = cookie.pop('name'), cookie.pop('value')
            cookiejar.set(name, val, port=cookie.get('port',None), 
                domain=cookie.get('domain', ''), path=cookie.get('path', '/'),
                secure=cookie.get('secure', False), expires=cookie.get('expires', None),
                discard=cookie.get('discard', True), comment=cookie.get('comment', None),
                comment_url=cookie.get('comment_url', None))
        self.cookiejar = cookiejar
        self.set_page_load_timeout(30)
    
    def get_parent(self, ele, level=1):
        for _ in range(level):
            try:
                ele = ele.find_element_by_xpath('..')
            except:
                break
        return ele
    
    def xpath_exists(self, xpath, wait=10, visible=False):
        if visible:
            return WebDriverWait(self, wait).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        return WebDriverWait(self, wait).until(EC.presence_of_element_located((By.XPATH, xpath)))
    
    def wait_xpath(self, xpath, url=None, trial=3, wait=10, visible=False):
        for _ in range(trial):
            if url is not None:
                self.get(url)
            try:
                ele = self.xpath_exists(xpath, wait=wait, visible=visible)
            except TimeoutException:
                continue
            else:
                if ele.is_displayed():
                    return ele
                else:
                    break
        return False
    
    def xpath_any(self, xpaths, url=None, trial=3, wait=1, visible=False):
        for _ in range(trial):
            if url is not None:
                self.get(url)
            for xpath in xpaths:
                if self.wait_xpath(xpath, wait=wait, visible=visible):
                    return True
        return False
    
    def xpath_exists_after(self, xpath, another, wait=10, visible=False):
        if self.wait_xpath(another, wait=wait, visible=visible):
            ele = self.wait_xpath(xpath, wait=wait, visible=visible)
            return ele
        return False

    def find_branch(self, branches, url=None, trial=10, wait=1, visible=False):
        for _ in range(trial):
            if url is not None:
                self.get(url)
            for branch, xpath in branches.items():
                if not isinstance(xpath, list):
                    xpath = [xpath]
                if self.xpath_any(xpath, trial=1, wait=wait, visible=visible):
                    return branch
        return False
    
    def find_displayed_xpath(self, xpath, url=None, trial=10, wait=1):
        for _ in range(trial):
            if url is not None:
                self.get(url)
            return [e for e in self.find_elements_by_xpath(xpath) if e.is_displayed()]
        return False
    
    def find_first_displayed(self, xpath, url=None, trial=10, wait=1):
        for _ in range(trial):
            if url is not None:
                self.get(url)
            try:
                return [e for e in self.find_elements_by_xpath(xpath) if e.is_displayed()][0]
            except:
                continue
        return False
    
    def fill_form(self, items):
        fails = {}
        # xpath-value pairs
        for xpath, v in items.items():
            if not self.fill_form_item(xpath, v):
                fails[xpath] = v
        return fails
    
    def fill_form_item(self, item_xpath, item_value, special=None):
        item_ele = self.xpath_exists(item_xpath, wait=5, visible=True)
        # put value into clipboard; this need blocks among threads
        # tkroot = tk.Tk()
        # tkroot.withdraw()
        # tkroot.clipboard_clear()
        # tkroot.clipboard_append(item_value)
        # tkroot.update()
        # tkroot.destroy()

        # define special element (e.g. dropdown-input)
        # if special == ''

        if item_ele.tag_name in ['input']:
        # checkbox
            if item_ele.get_attribute('type') == 'checkbox': # item_value will be boolean
                item_value = int(item_value)
                if item_ele.is_selected() != item_value:
                    try:
                        item_ele.click()
                    except:
                        self.execute_script('''arguments[0].click()''', item_ele)
                if not item_ele.is_selected == item_value:
                    # pyautogui
                    return False
        # text .etc input
            elif item_ele.get_attribute('type') in ['datetime', 'number', 'email', 'password', 'mySearch', 'text', 'url']:
                try:
                    item_ele.send_keys(getattr(Keys, item_value))
                except:
                    item_ele.send_keys(Keys.CONTROL, 'a')
                    # item_ele.send_keys(item_value)
                    # item_ele.send_keys(Keys.CONTROL, 'v')
                    # using js to input
                    if '\t' in item_value:
                        self.execute_script('''arguments[0].value = arguments[1]''', item_ele, item_value)
                    else:
                        item_ele.send_keys(item_value)
                    # if not item_ele.get_attribute('value') == item_value:
                    #     # pyautogui
                    #     return False
        # buttons
            elif item_ele.get_attribute('type') in ['submit', 'button']:
                try:
                    item_ele.click()
                except:
                    self.execute_script('''arguments[0].click()''', item_ele)
        elif item_ele.tag_name in ['button'] or item_ele.get_attribute('role') == 'button':
            try:
                item_ele.click()
            except:
                self.execute_script('''arguments[0].click()''', item_ele)
        # select
        elif item_ele.tag_name in ['select']: # item_value will be index or name
            # `Select` object in selenium supports 3 ways to select items
            item_select = Select(item_ele)
            try:
                item_select.select_by_index(int(item_value))
                if not item_select.options.index(item_select.first_selected_option) == item_value:
                    # pyautogui
                    return False
            except:
                try:
                    item_select.select_by_value(item_value)
                    if not item_select.first_selected_option.get_attribute('value') == item_value:
                        # pyautogui
                        return False
                except:
                    try:
                        item_select.select_by_visible_text(item_value)
                        if not item_select.first_selected_option.text == item_value:
                            # pyautogui
                            return False
                    except:
                        return False
        # textarea
        elif item_ele.tag_name in ['textarea']:
            item_ele.send_keys(Keys.CONTROL, 'a')
            # item_ele.send_keys(item_value)
            # item_ele.send_keys(Keys.CONTROL, 'v')
            # using js to input
            self.execute_script('''arguments[0].value = arguments[1]''', item_ele, item_value)
            if not item_ele.get_attribute('value') == item_value:
                # pyautogui
                return False
        elif item_value == 'CLICK':
            try:
                item_ele.click()
            except:
                self.execute_script('''arguments[0].click()''', item_ele)
        return True    
    
    def getsu(self, url, checker=None):
        while True:
            try:
                self.get(url)
                break
            except TimeoutException:
                continue
        
        flag = True
        if checker:
            if self.wait_xpath(checker, trial=1, wait=2):
                flag = False
        if flag:
            domain = urlparse(url).hostname
            domain = domain and domain.split('.')[-2]
            for cookie in self.cookiejar:
                if (cookie['domain'] and cookie['domain'] in url) or (domain and domain in cookie['domain']):
                    self.add_cookie(cookie)
            self.get(url)
        if checker:
            return self.wait_xpath(checker, trial=1)
        return True
    
    def open_new_tab(self, trigger_xpath, switch=True):
        curr_win_handles = self.window_handles
        trigger = self.find_element_by_xpath(trigger_xpath)
        trigger.send_keys(Keys.CONTROL, Keys.ENTER)
        tab_handle = [h for h in self.window_handles if not h in curr_win_handles][0]
        if switch:
            self.switch_to_window(tab_handle)
        return tab_handle

class ChromeMaster(DriverMaster, webdriver.Chrome):

    def __init__(self, use_cookies=True, driver_path=driver_path, driver_name='chromedriver.exe', *args, **kwargs):
        # print(driver_path)
        # print(str(Path(driver_path).joinpath(driver_name)))
        kwargs['executable_path'] = str(Path(driver_path).joinpath(driver_name))
        webdriver.Chrome.__init__(self, *args, **kwargs)
        
        self.browsername = 'chrome'
        if use_cookies:
            self.cookiejar = [{'name': c.name, 'value': c.value, 'domain': c.domain} for c in browser_cookie3.chrome()]

class FirefoxMaster(DriverMaster, webdriver.Firefox):

    def __init__(self, use_cookies=True, driver_path=driver_path, driver_name='geckodriver.exe', *args, **kwargs):
        kwargs['executable_path'] = str(Path(driver_path).joinpath(driver_name))
        webdriver.Firefox.__init__(self, *args, **kwargs)

        self.browsername = 'firefox'
        if use_cookies:
            self.cookiejar = [{'name': c.name, 'value': c.value, 'domain': c.domain} for c in browser_cookie3.firefox()]
        
        # self.win_handler = autoit.WinList('[REGEXPTITLE:(?i)({}.*?{})]'.format(self.title, self.browsername))[1][1]





def close_all_tabs(driver):
    main_tab = driver.current_window_handle
    tabs = driver.window_handles
    tabs.remove(main_tab)
    for tab in tabs:
        driver.switch_to_window(tab)
        driver.close()
    driver.switch_to_window(main_tab)

def wait_close_tab(driver, tabs, main='main', n_iter=10, wait=2):
    print(tabs)
    tabs = [[*v, k] for k, v in tabs.items() if not k == main]
    for _ in range(n_iter):
        for t in tabs:
            tab, xpath, *vals = t
            try:
                driver.switch_to_window(tab)
                xpath_exists(driver, xpath, wait=wait)
            except:
                continue
            else:
                driver.close()
                tabs.remove(t)
    return [t[2:] for t in tabs]


# def ofesac(url, driver, ops, suc=None, logger=None):
#     # open form, input or edit, save and close
#     # ops: a list of operations like [[xpath, value], ...]
#     func_name = 'ofesac'
#     (logger.info if logger != None else print)(PROMPTS['start'].format(func_name))
#     failed = False
#     # open
#     driver.get(url)
#     try:
#         xpath_exists(driver, ops[0][0], wait=60)
#     except:
#         failed = True
#     else:
#         # input all values
#         for xpath, val in ops:
#             fill_form_item(driver, xpath, val)