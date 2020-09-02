#!/usr/bin/env python
# coding=utf-8
'''
@project: Selenium_Crawler_Amazon
@author: Boyang Xia (Alvin)
@file: reviewsCrawler.py
@time: 2020/8/25 10:51
@desc:
'''

import _thread
import time, openpyxl
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

class ReviewsCrawler():
    def __init__(self, merchantInfo: dict):
        self.merchantInfo = merchantInfo
        self.page = int(input('startPage = '))
        self.exitFlag = 0
        self.reviewList = []

    def start(self):
        self.main_loop()
        print(f'Exit, end page = {self.page}')

    def console(self):
        if input() == 'exit':
            self.exitFlag = 1

    def main_loop(self):
        # console thread
        _thread.start_new_thread(self.console)

        # browser configurations
        # desired_capabilities = DesiredCapabilities.CHROME
        # desired_capabilities["pageLoadStrategy"] = 'none'
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        session = webdriver.Chrome(chrome_options=chrome_options)
        session.get(
            f"https://www.amazon.com/s?i=merchant-items&me={self.merchantInfo['merchantId']}&page={self.page}&marketplaceID={self.merchantInfo['marketplaceId']}")
        self.check_delivery(session)
        time.sleep(1)

        while self.exitFlag == 0 and self.page <= 150:
            session.get(f"https://www.amazon.com/s?i=merchant-items&me={self.merchantInfo['merchantId']}&page={self.page}&marketplaceID={self.merchantInfo['marketplaceId']}")
            self.iterate_through_plist(session)

            # open spreadsheet workbook
            try:
                wb = openpyxl.load_workbook(f"{self.merchantInfo['name']}_reviews.xlsx")
            except FileNotFoundError:
                wb = openpyxl.workbook.Workbook()
            try:
                sheet = wb["reviews"]
            except KeyError:
                sheet = wb.create_sheet("reviews")
                sheet.append(['ASIN', 'RATING', 'LINK', 'REVIEWER', 'DATE', 'FORM', 'TITLE', 'REVIEW'])

            for review in self.reviewList:
                sheet.append(review)
            wb.save(f"{self.merchantInfo['name']}_reviews.xlsx")

            self.reviewList = []
            logFile = open('log_review_crawler.txt', mode='a+')
            logFile.write(f"{time.ctime()} {self.merchantInfo['name']} {self.page} page written\n")
            logFile.close()
            self.page += 1

    def iterate_through_plist(self, session: webdriver.Chrome):
        wait = WebDriverWait(session, 10)
        wait.until(lambda driver: driver.find_element_by_xpath(
            "//div[@class='s-main-slot s-result-list s-search-results sg-row']").is_displayed())
        # results = session.find_elements_by_xpath("//div[@data-component-type='s-search-result']")
        for index in range(0, 16):
            try:
                result = session.find_element_by_xpath(
                    f"//div[@data-index='{index}']")
                webdriver.ActionChains(session).move_to_element(result).perform()
                time.sleep(0.5)

                trigger = session.find_element_by_xpath(f"//div[@data-index='{index}']//a[@class='a-popover-trigger a-declarative']")
                    # ("//a[@class='a-popover-trigger a-declarative']")
                    # //div[{index}]/div[1]/span[1]/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/span[1]/span[1]/a[1]
                webdriver.ActionChains(session).move_to_element(trigger).perform()
                # wait.until(lambda driver: driver.find_element_by_xpath("//div[@class='a-popover-content']").is_displayed())
                time.sleep(1)
                try:
                    reviewLink = session.find_element_by_xpath(
                        "//a[contains(text(),'See all customer reviews')]").get_attribute('href')
                except Exception as error:
                    print(error)
                else:
                    asin = session.find_element_by_xpath(
                        f"//div[@data-index='{index}']").get_attribute('data-asin')
                    session.get(reviewLink)
                    wait.until(lambda driver: driver.find_element_by_xpath(
                        "//div[@data-hook='top-customer-reviews-widget']").is_displayed())
                    self.get_review(wait, asin, reviewLink, session)
                    session.back()
                    wait.until(lambda driver: driver.find_element_by_xpath(
                        "//div[@class='s-main-slot s-result-list s-search-results sg-row']").is_displayed())

            except Exception as error:
                print(error)

    def get_review(self, wait: WebDriverWait, asin, reviewLink, session: webdriver.Chrome):
        productRating = session.find_element_by_xpath("//span[@data-hook='rating-out-of-text']").text
        productRating = productRating[:productRating.find(' ')]

        reviews = session.find_elements_by_css_selector('div[data-hook=review]')
        for review in reviews:
            reviewId = review.get_attribute('id')
            reviewer = session.find_element_by_xpath(f"//div[@id='{reviewId}']//span[@class='a-profile-name']").text
            reviewDate = session.find_element_by_xpath(f"//div[@id='{reviewId}']//span[@data-hook='review-date']").text
            try:
                form = session.find_element_by_xpath(f"//div[@id='{reviewId}']//span[@data-hook='format-strip-linkless']").text
            except:
                form = ''
            reviewTitle = session.find_element_by_xpath(f"//div[@id='{reviewId}']//a[@data-hook='review-title']/span[1]").text
            reviewBody = session.find_element_by_xpath(f"//div[@id='{reviewId}']//div[@data-hook='review-collapsed']/span[1]").text
            self.reviewList.append([asin, productRating, reviewLink, reviewer, reviewDate, form, reviewTitle, reviewBody])
            print([asin, productRating, reviewLink, reviewer, reviewDate, form, reviewTitle, reviewBody])
            pass

    def check_delivery(self, session: webdriver.Chrome):
        WebDriverWait(session, 10).until(
            lambda driver: driver.find_element_by_xpath("//span[@id='glow-ingress-line2']"))
        if session.find_element_by_xpath("//span[@id='glow-ingress-line2']").text[:16] != 'Cincinnati 45201':
            session.find_element_by_xpath("//span[@id='glow-ingress-line2']").click()
            WebDriverWait(session, 10).until(
                lambda driver: driver.find_element_by_xpath("//input[@id='GLUXZipUpdateInput']"))
            session.find_element_by_xpath("//input[@id='GLUXZipUpdateInput']").send_keys('45201')
            session.find_element_by_xpath("//span[@id='GLUXZipUpdate']//input[@class='a-button-input']").click()
            WebDriverWait(session, 10).until(lambda driver: driver.find_element_by_xpath(
                "//div[@class='a-popover-footer']//input[@id='GLUXConfirmClose']"))
            session.find_element_by_xpath("//div[@class='a-popover-footer']//input[@id='GLUXConfirmClose']").click()