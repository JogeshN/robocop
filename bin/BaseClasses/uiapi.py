# -*- coding: utf-8 -*-

from robotpageobjects import Page
import time, re, os, sys
# import xmltodict
import subprocess,codecs
from robot.utils import asserts
import time
from Tkinter import Tk

class webutil(Page, InitResources):
    uri="/"
 
    selectors = {
                }
           
    def __init__(self):
        Page.__init__(self)
        
        if not self.selectors:
            obj_selectors = self.get_selectors_from_obj_file()
            self.selectors.update(obj_selectors)
    
    def get_clipboard_data(self):
        r = Tk()
        authkey = r.selection_get(selection = "CLIPBOARD")
        return authkey
     
    def get_table_cell_data(self,xpath,colnum):
        #xpath=.//*[@id='page']/div/div/div[2]/div/div/div/table
        count = self.get_matching_xpath_count(xpath + "/tbody/tr")
        print(count, is_console=False)
        cells = {}
        for i in range(1,int(count) + 2):
            cell = self.get_table_cell("xpath=" + xpath, str(i), str(colnum))
            cells[str(i)] = cell
            
        print(cells, is_console=False)
        
        return cells
                
    def verify_element_exist(self,
                             locator
                             ):
        print("locator found is %s"%locator,is_console=False)
        #msg = "Element locator '" + locator + "' did not match any elements."
        msg = '"'+locator +'"'+" did not match any elements."
        msg=msg.replace('"','').replace("'","")
        msg1 = '"'+locator+ '"'+" is not a valid locator."
        msg1=msg1.replace('"','').replace("'","")
        print("Message is %s" %msg,is_console=False)
        print("Message 1 is %s" %msg1,is_console=False)
        try:
            self.click_element(locator)
            asserts.fail("Element present : %s"%locator)
        except Exception,Fault:
            F=str(Fault).replace('"','').replace("'","")
            print("exception found : %s"%str(Fault),is_console=False)
            #asserts.assert_equals((str(Fault),msg) or (str(Fault),msg1) ,"Unexpected exception found: %s"%Fault)
            #msg = "Unexpected Error found. [%s]" %(Fault)
            tflag=False
            if (msg in F) or (msg1 in F):
                tflag=True
            msg = "Unexpected exception found.[%s]" %(F)    
            if not tflag:
                asserts.fail(msg)
            #asserts.fail_if((msg not in F) and (msg1 not in F) , msg)
        return self 
    
    def wait_for_spinner_to_complete(self,timeout=30,interval=2):
        print("Started wait for Spinner now", is_console=False)
        waittimer = Timer()
        waittime = waittimer.start(timeout, interval=interval)
        
        while (self.is_visible("spinner_in_progress") and waittimer.active()):
            print("Waiting for the page to get loaded", is_console=False)
        print("Exit from wait for Spinner now", is_console=False)
        return self
    
    def wait_for_element_visible(self,locator,timeout=60, interval=2):
        waittimer = Timer()
        waittime = waittimer.start(timeout, interval=interval)
        find = self.is_visible(locator)
        while not find and waittime.active():
            print("visibility status of locator [%s] is %s" %(locator,find), is_console=True)
            find = self.is_visible(locator)
            if find:
                print("visibility status of locator [%s] is %s" %(locator,find), is_console=True)
                break
        return self
    
    def wait_for_element_invisible(self,locator,timeout=10):
        try:
            self.wait_until_element_is_not_visible(locator, timeout)
        except:
            pass
        return self
        
    def ajax_complete(self,timeout=20, interval=2):
        waittimer = Timer()
        waittime = waittimer.start(timeout, interval=interval)
        current_status = self.execute_javascript("return window.jQuery != undefined && jQuery.active == 0")
        while waittime.active() and not current_status:
            current_status = self.execute_javascript("return window.jQuery != undefined && jQuery.active == 0")
        return self
    
    
    def get_selectors_from_obj_file(self, filename=''):
        if filename:
            try: 
                fullfilename = os.path.join("AutoBot", "ObjectRepo", self.edition.lower() + "_" + filename) 
    #             print("Object Repo file name %s" % fullfilename, is_console=True) 
                objfile = file(fullfilename, "U").read() 
            except: 
                fullfilename = os.path.join("ObjectRepo", self.edition.lower() + "_" + filename) 
    #             print("Object Repo file name %s" % fullfilename, is_console=True) 
                objfile = file(fullfilename, "U").read() 
            print("Object Repo file name %s" % fullfilename, is_console=True)
            # dictionary of pages, where pages is dictionary of elements on that page
            page_dict = {}
            exec objfile in page_dict
            selectors = page_dict['selectors']
        else:
            selectors = self.selectors
        #Add common object repo
        try:
            commobj = file(os.path.join("AutoBot", "ObjectRepo", self.edition.lower()  + "_" + "obj_common.py"), "U").read() 
        except: 
            commobj = file(os.path.join("ObjectRepo", self.edition.lower()  + "_" + "obj_common.py"), "U").read() 
        comm_obj = {}
        exec commobj in comm_obj
        comm_selectors = comm_obj['selectors']
        
        #Add common selectors to page selectors
        selectors.update(comm_selectors)
        
        return selectors   
  
    def set_value_from_autosuggest(self, myselector, value):
        self.click_element(myselector)
        self.input_text(myselector, value)
        value = self.get_value(myselector)
        print("Value is %s" %value, is_console=False)
        waittimer = Timer()
        waittime = waittimer.start(10,3)
        while waittime.active() and not value:
            value = self.get_value(myselector)
            print("Value is %s" %value, is_console=False)
        self.press_key(myselector, "\\13")
        self.ajax_complete()
        return self
    
    def match_expected_notification(self,expected_notification=''):
        if not expected_notification:
            asserts.fail("Expected Message not provided.")
        
        act_msg = ""
        act_msg = self.get_text("LabelValueNotificationMsg")
        print("LabelValueNotificationMsg is %s" %act_msg)
        waittimer = Timer()
        waittime = waittimer.start(90,1)
        print("Expected message is {%s}, %s" % (expected_notification,type(expected_notification)), is_console=False)
        print("Actual message is {%s}, %s" %(act_msg,type(act_msg)), is_console=False)
        while ((act_msg.lower() != expected_notification.lower()) and waittimer.active()):
            #print("Waiting for Actual notification message.",is_console=False)
            act_msg = self.get_text("LabelValueNotificationMsg")
            if act_msg:
                print("Actual message is %s" %act_msg,is_console=False)
        
        print("Actual message retrieved is {%s}" %act_msg,is_console=False)
            
        try:
            self.click_element('close_notification')
            print("Notification message closed.", is_console=False)
        except:
            pass
        
        result = 0
        if act_msg.lower() == expected_notification.lower():
            result = 1
        
        if not result:
            match = self.match_string_to_regexp(expected_notification, act_msg)
            result = 1 if match == 1 else 0
        
        return result

    def check_value_not_present_in_autosuggest(self, myselector, value):
        print("Value to check in auto suggest is - %s" %value, is_console=True)
        self.click_element(myselector)
        value_to_input=value[:-1]
        print("Value to input in auto suggest box is %s" %value_to_input, is_console=True)
        self.input_text(myselector, value_to_input)
        self.press_key(myselector, "\\13")
        actual_value = self.get_value(myselector)
        asserts.fail_if(actual_value == value,'Verification failed, as value to check - %s appears in auto suggest'%value)
        print('Verification passed. Value to check - %s does not appear in auto suggest'%value)
        return self

class Timer():
    def __init__(self):
        self.timeout = None
        self.starttime = None
        self.interval = None
    
    def start(self, seconds=30, interval=None):
        self.starttime = time.time()
        self.timeout = seconds
        self.interval = interval
        return self
    
    def active(self): 
        if self.interval:
            time.sleep(self.interval)
        if time.time() - self.starttime > self.timeout:
            return False
        else:
            return True
