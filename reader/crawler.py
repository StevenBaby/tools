#!/usr/bin/python
# encoding=utf-8
import os
import sys
import time
import logging
import logging.config
import dandan
from selenium import webdriver

import config

reload(sys)
sys.setdefaultencoding("utf-8")


class Crawler(object):

    FIREFOX = "FireFox"

    def __init__(self, type=FIREFOX):
        self.init_logging()
        self.browser = None

        logger = logging.getLogger("crawler")
        logger.info("Browser {} is starting...".format(type))
        if type == self.FIREFOX:
            profile_path = os.environ.get("FIREFOX_PROFILE")
            profile = webdriver.FirefoxProfile(profile_path)
            self.browser = webdriver.Firefox(profile)
            self.browser.set_page_load_timeout(30)
            self.browser.maximize_window()

    def init_logging(self):
        logging.config.dictConfig(config.LOGGING)

    def __del__(self):
        if not self.browser:
            return
        self.browser.quit()

    def get_books(self, url, bookname):
        logger = logging.getLogger("crawler")
        logger.info("request {}".format(url))
        self.browser.get(url)

        logger.info(u"send keys {}".format(bookname))
        self.browser.find_element_by_xpath("//input[@name='key']").send_keys(bookname)

        logger.info("click search...")
        self.browser.find_element_by_xpath('''//form[@action='/search.do']/button[@type='submit']''').click()

        books = self.browser.find_elements_by_xpath("//div[contains(@class, 'book')]")
        logger.info("get {} books".format(len(books)))

        items = []
        for book in books:
            item = dandan.value.AttrDict()
            item.name = book.find_element_by_css_selector("h5").text
            item.star = len(book.find_elements_by_xpath("./div[contains(@class, 'w-star')]/span[not(contains(@class, 'no'))]"))
            item.price = book.find_element_by_xpath("./p[contains(@class, 'price')]").text
            item.desc = book.find_element_by_xpath("./p[contains(@class, 'disc')]").text
            logger.debug(item)

            items.append(item)

        return items

    def crawl(self, url, bookname):
        logger = logging.getLogger("crawler")

        books = self.get_books(url, bookname)
        logger.info("get books {}".format(books))


def main():
    crawler = Crawler()
    crawler.crawl("http://yuedu.163.com/", u"西游记")


if __name__ == '__main__':
    main()
    # pass
