#!/usr/bin/env python
# coding=utf-8
'''
@project: A_Amazon_Crawler
@author: Boyang Xia
@file: SkuListGenerator.py
@time: 2020/8/18 14:54
@desc:
'''

import time
import threading, queue
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options


# from selenium.webdriver.common.keys import Keys
# import tkinter as tk

# simplify the listing url found, keep essential path only
def simplify_listing_url_en(url):
    count = 0
    urlLength = 0
    for char in url:
        if char == '/':
            count += 1
        if count == 6:
            break
        urlLength += 1
    return url[:urlLength]


def simplify_listing_url_zh(url):
    count = 0
    urlLength = 0
    for char in url:
        if char == '/':
            count += 1
        if count == 6:
            break
        urlLength += 1
    return url[:urlLength]


# threading class to generate lists of sku records
class SkuListGeneratorThread(threading.Thread):

    def __init__(self, threadId, dateQueue: queue.Queue, queueLock: threading.Lock, sRange, merchantInfo: dict, proxy):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.dateQueue = dateQueue  # yymmdd
        self.queueLock = queueLock
        self.queueLock.acquire()
        self.date = self.dateQueue.get()
        self.queueLock.release()
        # self.root = tk.Tk()
        # self.skuPointer = 0
        # self.emptyCounter =
        self.merchantInfo = merchantInfo
        self.searchKey = merchantInfo.get('name', 'uxcell')
        self.searchRange = sRange
        self.currentSkuRecord = []
        self.skuRecordList = []
        # self.isListEnd = False
        self.skuCounter = 0
        self.deliverToUS = False
        self.proxy = proxy

    def run(self):
        print(f'Thread id {self.threadId} start:')
        self.crawl_start()
        # return self.skuCounter

    '''may add a decorator'''

    def sku_id_generator(self, skuPointer):
        # should follow a self.skuPointer += 1
        suffix = str(skuPointer)
        while len(suffix) < 4:
            suffix = '0' + suffix
        return f'a{self.date}00ux{suffix}'

    # generate a record of a single sku
    def simple_sku_record_generator(self, skuId, Session: webdriver.Chrome, logFile):
        try:
            WebDriverWait(Session, 10, 1.5).until(lambda driver: driver.find_element_by_id('twotabsearchtextbox'))
            Session.find_element_by_id('twotabsearchtextbox').clear()
            Session.find_element_by_id('twotabsearchtextbox').send_keys(skuId)
            Session.find_element_by_id('twotabsearchtextbox').submit()
            # xpath = chrome xpath
            WebDriverWait(Session, 10, 1.5).until(lambda driver: driver.find_element_by_xpath(
                "//div[@class='s-main-slot s-result-list s-search-results sg-row']/div[1]"))
            result = Session.find_element_by_xpath(
                "//div[@class='s-main-slot s-result-list s-search-results sg-row']/div[1]")
            if result.get_attribute('data-asin') != '':
                skuTitle = result.find_element_by_xpath(
                    "//span[@class='a-size-medium a-color-base a-text-normal']").text
                if skuTitle[:len(self.searchKey)] == self.searchKey:
                    skuAsin = result.get_attribute('data-asin')
                    skuListing = simplify_listing_url_en(
                        result.find_element_by_xpath("//a[@class='a-link-normal s-no-outline']").get_attribute('href'))
                    skuPrice = '$' + result.find_element_by_xpath(
                        "//span[@class='a-price-whole']").text + '.' + result.find_element_by_xpath(
                        "//span[@class='a-price-fraction']").text
                    try:
                        skuStock = result.find_element_by_xpath("//span[@class='a-color-price']").text
                    except:
                        skuStock = 'In stock'
                    self.currentSkuRecord = [skuId, skuListing, skuAsin, skuTitle, skuPrice, skuStock]
                    # return current_sku
                    return True
            self.currentSkuRecord = []
            return False
        except Exception as Error:
            print(f'###Error###:[Thread: {self.threadId}][{skuId}]: {Error}')
            logFile.writelines(f'###Error###:[Thread: {self.threadId}][{skuId}]: {Error}\n')
            self.currentSkuRecord = []
            return False

    def crawl_start(self):
        # browser configurations
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities["pageLoadStrategy"] = 'none'
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'--proxy-server=http://{self.proxy}')

        session = webdriver.Chrome(chrome_options=chrome_options)
        session.get(
            f"https://www.amazon.com/s?me={self.merchantInfo['merchantId']}&marketplaceID={self.merchantInfo['marketplaceId']}")
        # self.check_delivery(session)
        time.sleep(0.5)

        logFile = open(f'Log_{self.searchKey}_{self.date[:4]}.txt', mode='a')

        for skuPointer in range(1, self.searchRange):
            skuId = self.sku_id_generator(skuPointer)
            record = self.simple_sku_record_generator(skuId, session, logFile=logFile)
            if record:
                self.skuRecordList.append(self.currentSkuRecord)
                self.skuCounter += record

                logFile.write(f'[{self.threadId}][{self.skuCounter}][{skuId}][{record}]\n')
            print(f'[{self.threadId}][{self.skuCounter}][{skuId}][{record}]:{self.currentSkuRecord}')
            # if current_sku != None:
            #   self.skuRecordList.append(current_sku)
        session.close()
        logFile.close()
        # self.root.quit()
        # self.root.mainloop()
        print(f'Thread {self.threadId} ends, {self.skuCounter} skus founded')

    def check_delivery(self, Session: webdriver.Chrome):
        WebDriverWait(Session, 10).until(
            lambda driver: driver.find_element_by_xpath("//span[@id='glow-ingress-line2']"))
        if Session.find_element_by_xpath("//span[@id='glow-ingress-line2']").text[:16] != 'Cincinnati 45201':
            Session.find_element_by_xpath("//span[@id='glow-ingress-line2']").click()
            WebDriverWait(Session, 10).until(
                lambda driver: driver.find_element_by_xpath("//input[@id='GLUXZipUpdateInput']"))
            Session.find_element_by_xpath("//input[@id='GLUXZipUpdateInput']").send_keys('45201')
            Session.find_element_by_xpath("//span[@id='GLUXZipUpdate']//input[@class='a-button-input']").click()
            WebDriverWait(Session, 10).until(lambda driver: driver.find_element_by_xpath(
                "//div[@class='a-popover-footer']//input[@id='GLUXConfirmClose']"))
            Session.find_element_by_xpath("//div[@class='a-popover-footer']//input[@id='GLUXConfirmClose']").click()

    '''# deprecated
    def isListEnd(self, current_sku):
        if current_sku[2] == '':
            self.emptyCounter += 1
        else:
            self.emptyCounter = 0
        if self.emptyCounter > 20
            return True
        else:
            return False
    '''
