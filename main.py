#!/usr/bin/env python
# coding=utf-8
'''
@project: A_Amazon_Crawler
@author: Boyang Xia
@file: main.py
@time: 2020/8/18 16:54
@desc:
'''

import SkuListGenerator
# import time
# import pandas as pd
import queue
import threading
import openpyxl

merchantInfo = {
    'name': 'uxcell',
    'merchantId': 'A1THAZDOWP300U',
    'marketplaceId': 'ATVPDKIKX0DER'
}

configCrawler = {
    'year': '19',
    'month': '03',
    'startDate': '22',
    'endDate': '25',
    'searchRange': 1800,
    'threadNum': 2,
    'proxyServers': []
}

threadIdList = [id for id in range(configCrawler['threadNum'])]
dateList = [configCrawler['year']+configCrawler['month']+str(date) for date in range(int(configCrawler['startDate']), int(configCrawler['endDate'])+1)]
dateQueue = queue.Queue(1 + int(configCrawler['endDate']) - int(configCrawler['startDate']))
queueLock = threading.Lock()

queueLock.acquire()
for formatDate in dateList:
    dateQueue.put(formatDate)
queueLock.release()

proxyPointer = 0

def a_proxy():
    global proxyPointer
    if proxyPointer == len(configCrawler['proxyServers']):
        proxyPointer = 0
    proxy = configCrawler['proxyServers'][proxyPointer]
    proxyPointer += 1
    return proxy

# main loop
while not dateQueue.empty():
    threads = []

    # open spreadsheet workbook
    try:
        wb = openpyxl.load_workbook(f"{merchantInfo['name']}_sku_list.xlsx")
    except FileNotFoundError:
        wb = openpyxl.workbook.Workbook()
    try:
        sheet = wb.get_sheet_by_name(f"{configCrawler['year']}{configCrawler['month']}")
    except KeyError:
        sheet = wb.create_sheet(f"{configCrawler['year']}{configCrawler['month']}")

    for threadId in threadIdList:
        thread = SkuListGenerator.SkuListGeneratorThread(threadId, dateQueue, queueLock, configCrawler['searchRange'], merchantInfo, a_proxy())
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
        for record in thread.skuRecordList:
            sheet.append(record)

        del thread
    wb.save(f"{merchantInfo['name']}_sku_list.xlsx")

print('exit, writen to xlsx.')



