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

exitFlag = 0

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
    'threadNum': 2
}

threadIdList = [id for id in range(configCrawler['threadNum'])]
dateList = [configCrawler['year']+configCrawler['month']+str(date) for date in range(int(configCrawler['startDate']), int(configCrawler['endDate'])+1)]
dateQueue = queue.Queue(1 + int(configCrawler['endDate']) - int(configCrawler['startDate']))
queueLock = threading.Lock()

queueLock.acquire()
for formatDate in dateList:
    dateQueue.put(formatDate)
queueLock.release()

'''df0 = pd.DataFrame({
        'skuId': [], 'skuListing': [], 'skuAsin': [], 'skuTitle': [], 'skuPrice': [], 'skuStock': []
    })'''


# main loop
while not dateQueue.empty():
    threads = []

    # open spreadsheet workbook
    try:
        wb = openpyxl.load_workbook(f"{merchantInfo['name']}_sku_list.xlsx")
    except FileNotFoundError:
        wb = openpyxl.Workbook()
    try:
        sheet = wb.get_sheet_by_name(f"{configCrawler['year']}{configCrawler['month']}")
    except KeyError:
        sheet = wb.create_sheet(f"{configCrawler['year']}{configCrawler['month']}")

    for threadId in threadIdList:
        thread = SkuListGenerator.SkuListGeneratorThread(threadId, dateQueue, queueLock, configCrawler['searchRange'], merchantInfo)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
        for record in thread.skuRecordList:
            sheet.append(record)

            '''df0 = pd.concat([df0,pd.DataFrame({
                'skuId': [record[0]],
                'skuListing': [record[1]],
                'skuAsin': [record[2]],
                'skuTitle': [record[3]],
                'skuPrice': [record[4]],
                'skuStock': [record[5]]
            })])'''
        del thread
    wb.save(f"{merchantInfo['name']}_sku_list.xlsx")

print('exit, writen to xlsx.')


'''with pd.ExcelWriter(f"{merchantInfo['name']}_sku_list.xlsx", engine='openpyxl', mode='a') as writer:
    df0.to_excel(writer, sheet_name=f"{configCrawler['year']}{configCrawler['month']}")
'''

