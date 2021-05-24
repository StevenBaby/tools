# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__ = "GPL v3"
__copyright__ = "2011, Kovid Goyal <kovid@kovidgoyal.net>; 2011, Li Fanxi <lifanxi@freemindworld.com>"
__docformat__ = "restructuredtext en"

import time

try:
    from queue import Empty, Queue
except ImportError:
    from Queue import Empty, Queue

from calibre.ebooks.metadata import check_isbn
from calibre.ebooks.metadata.sources.base import Option, Source
from calibre.ebooks.metadata.book.base import Metadata
from calibre import as_unicode

from bs4 import BeautifulSoup
import time
import random
import urllib.request
import sys
import re

NAMESPACES = {
    "openSearch": "http://a9.com/-/spec/opensearchrss/1.0/",
    "atom": "http://www.w3.org/2005/Atom",
    "db": "https://www.douban.com/xmlns/",
    "gd": "http://schemas.google.com/g/2005",
}


class Douban(Source):
    name = "Douban Book"
    author = "Li Fanxi, xcffl, jnozsc, else"
    version = (4, 0, 1)
    minimum_calibre_version = (5, 0, 0)

    description = (
        "Downloads metadata and covers from Douban.com. "
        "Useful only for Chinese language books."
    )

    capabilities = frozenset(["identify", "cover"])
    touched_fields = frozenset(
        [
            "title",
            "authors",
            "tags",
            "pubdate",
            "comments",
            "publisher",
            "identifier:isbn",
            "rating",
            "identifier:douban",
        ]
    )  # language currently disabled
    supports_gzip_transfer_encoding = True
    cached_cover_url_is_reliable = True

    ISBN_URL = "http://douban.com/isbn/"
    SUBJECT_URL = "http://book.douban.com/subject/"
    DOUBAN_BOOK_URL = 'https://book.douban.com/subject/%s/'

    options = (
        Option(
            "include_subtitle_in_title",
            "bool",
            True,
            ("Include subtitle in book title:"),
            ("Whether to append subtitle in the book title."),
        ),
    )

    def identify(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30,):
        import json

        time.sleep(random.randint(1, 3))

        log.info("start get metadata from douban...")
        log.info(str(identifiers))
        # query = self.create_query(log, title=title, authors=authors, identifiers=identifiers)
        book = self.get_book(log, identifiers)

        # There is no point running these queries in threads as douban
        # throttles requests returning 403 Forbidden errors
        self.get_all_details(log, book, abort, result_queue, timeout)

        return None

    def to_metadata(self, log, entry_, timeout):  # {{{
        from calibre.utils.date import parse_date, utcnow

        log.info("to_metadata")
        douban_id = entry_.get("id")
        title = entry_.get("title")
        description = entry_.get("summary")
        # subtitle = entry_.get('subtitle')  # TODO: std metada doesn't have this field
        publisher = entry_.get("publisher")
        isbn = entry_.get("isbn13")  # ISBN11 is obsolute, use ISBN13
        pubdate = entry_.get("pubdate")
        authors = entry_.get("author")
        # authors = "author"
        book_tags = entry_.get("tags")
        rating = entry_.get("rating")
        cover_url = entry_.get("cover")
        series = entry_.get("series")

        if not authors:
            authors = [("Unknown")]
        if not douban_id or not title:
            # Silently discard this entry
            return None

        mi = Metadata(title, authors)
        mi.identifiers = {"douban": douban_id}
        mi.publisher = publisher
        mi.comments = description
        # mi.subtitle = subtitle

        # ISBN
        isbns = []
        if isinstance(isbn, (type(""), bytes)):
            if check_isbn(isbn):
                isbns.append(isbn)
        else:
            for x in isbn:
                if check_isbn(x):
                    isbns.append(x)
        if isbns:
            mi.isbn = sorted(isbns, key=len)[-1]
        mi.all_isbns = isbns

        # Tags
        mi.tags = book_tags

        # pubdate
        if pubdate:
            try:
                default = utcnow().replace(day=15)
                mi.pubdate = parse_date(pubdate, assume_utc=True, default=default)
            except BaseException:
                log.error("Failed to parse pubdate %r" % pubdate)

        if rating:
            try:
                # mi.publisher += "#PrB.rating#" + str(rating)
                mi.rating = rating / 2.0
            except BaseException:
                log.exception("Failed to parse rating")
                mi.rating = 0

        # Cover
        mi.has_douban_cover = None
        u = cover_url
        if u:
            # If URL contains "book-default", the book doesn't have a cover
            if u.find("book-default") == -1:
                mi.has_douban_cover = u

        # Series
        if series:
            mi.series = series

        return mi

    # }}}

    def get_isbn_url(self, isbn):  # {{{
        if isbn is not None:
            return self.ISBN_URL + isbn
        else:
            return ""
    # }}}

    def get_douban_url(self, identifiers):
        isbn = self.get_book_isbn(identifiers)
        url = self.get_isbn_url(isbn)
        if url:
            return url
        tup = self.get_book_url(identifiers)
        if tup:
            return tup[2]

    def get_book_url(self, identifiers):  # {{{
        db = identifiers.get('douban', None)
        if db is not None:
            return ('douban', db, self.DOUBAN_BOOK_URL % db)

    # }}}

    def get_book_isbn(self, identifiers):
        isbn = check_isbn(identifiers.get("isbn", None))
        return isbn

    def download_cover(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30, get_best_cover=False,):
        cached_url = self.get_cached_cover_url(identifiers)
        if cached_url is None:
            log.info("No cached cover found, running identify")
            rq = Queue()
            self.identify(
                log, rq, abort, title=title, authors=authors, identifiers=identifiers
            )
            if abort.is_set():
                return
            results = []
            while True:
                try:
                    results.append(rq.get_nowait())
                except Empty:
                    break
            results.sort(
                key=self.identify_results_keygen(
                    title=title, authors=authors, identifiers=identifiers
                )
            )
            for mi in results:
                cached_url = self.get_cached_cover_url(mi.identifiers)
                if cached_url is not None:
                    break
        if cached_url is None:
            log.info("No cover found")
            return

        if abort.is_set():
            return
        br = self.browser
        log("Downloading cover from:", cached_url)
        try:
            cdata = br.open_novisit(cached_url, timeout=timeout).read()
            if cdata:
                result_queue.put((self, cdata))
        except BaseException:
            log.exception("Failed to download cover from:", cached_url)

    # }}}

    def get_cached_cover_url(self, identifiers):  # {{{
        url = None
        db = identifiers.get("douban", None)
        if db is None:
            isbn = identifiers.get("isbn", None)
            if isbn is not None:
                db = self.cached_isbn_to_identifier(isbn)
        if db is not None:
            url = self.cached_identifier_to_cover_url(db)

        return url

    # }}}

    def get_all_details(self, log, book, abort, result_queue, timeout):  # {{{
        try:
            log.info("get_all_details")
            ans = self.to_metadata(log, book, timeout)
            if isinstance(ans, Metadata):
                ans.source_relevance = 0
                douban_id = ans.identifiers["douban"]
                isbn = book.get("isbn13")
                self.cache_isbn_to_identifier(isbn, douban_id)
                if ans.has_douban_cover:
                    self.cache_identifier_to_cover_url(douban_id, ans.has_douban_cover)
                self.clean_downloaded_metadata(ans)
                result_queue.put(ans)
        except BaseException:
            log.exception("Failed to get metadata for identify entry:", book["id"])
        if abort.is_set():
            return

    # }}}

    def get_book(self, log, identifiers={}):
        log.info("start get book......")
        url = self.get_douban_url(identifiers)
        html = self.__get_html(url)
        if html == -1:
            # log.info("book not found: " + isbn)
            return -1

        soup = self.__get_soup(html=html)
        infos = self.__get_infos(soup=soup)
        isbn = self.__get_isbn(identifiers, soup)
        book = {"isbn13": isbn}
        book["author"] = self.__get_authors(infos)
        book["publisher"] = self.__get_info(infos, "出版社:")
        book["pubdate"] = self.__get_info(infos, "出版年:")
        book["series"] = self.__get_info(infos, "丛书:")

        book["id"] = self.__get_id(soup=soup)
        book["tags"] = self.__get_tags(soup=soup)
        book["rating"] = self.__get_score(soup=soup)
        book["title"] = self.__get_title(soup=soup)
        book["summary"] = self.__get_intro(soup=soup)
        book["cover"] = self.__get_cover(soup=soup)
        return book

    def __get_html(self, url):
        headers_ = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"
        }
        request = urllib.request.Request(url, headers=headers_)
        try:
            response = urllib.request.urlopen(request)
        except BaseException:
            return -1
        html = response.read().decode("utf-8")
        return html

    def __get_soup(self, html=""):
        soup = BeautifulSoup(html, "lxml", exclude_encodings="utf-8")
        return soup

    def __get_infos(self, soup):
        soupSelect = str(soup.select("#info"))
        soupTemp = BeautifulSoup(str(soupSelect), "lxml", exclude_encodings="utf-8")
        infosTemp = soupTemp.text.splitlines()
        infos = []
        for info in infosTemp:
            tmp = info.strip()
            if tmp and tmp != "/":
                infos.append(tmp)
        infos.remove("[")
        infos.remove("]")
        return infos

    def __get_info(self, infos, name):
        for token in infos:
            if token.find(name) != -1:
                return token[len(name) + 1:]
        return ""

    def __get_authors(self, infos):
        begin = -1
        end = -1
        i = 0
        for token in infos:
            if token == "作者:":
                begin = i
            elif token.find("出版社:") != -1:
                end = i + 1
                break
            else:
                i = i + 1
        authors = []
        if begin == -1:
            return authors
        if end == -1:
            authors.append(infos[begin + 1])
            return authors
        else:
            for i in range(begin + 1, end):
                author = infos[i].strip()
                author = author.replace("【", "[")
                author = author.replace("】", "]")
                author = author.replace("（", "[")
                author = author.replace("）", "]")
                author = author.replace("〔", "[")
                author = author.replace("〕", "]")
                author = author.replace("(", "[")
                author = author.replace(")", "]")
                author = author.replace("]", "] ")
                author = author.replace("•", "·")
                author = author.replace("・", "·")
                authors.append(author)
            return authors

    def __get_id(self, soup):
        idSelects = str(soup.select("meta")).split()
        for item in idSelects:
            idIndex = item.find("douban.com/book/subject/")
            if idIndex != -1:
                id = item[idIndex + 24: -2]
                return id
        return 0

    def __get_tags(self, soup):
        tagSelect = str(soup.select("#db-tags-section > div"))
        tagTemp = BeautifulSoup(str(tagSelect), "lxml", exclude_encodings="utf-8")
        tagText = tagTemp.text
        tags = tagText.split()
        tags.remove("[")
        tags.remove("]")
        return tags

    def __get_cover(self, soup):
        coverSelect = str(soup.select("#mainpic > a > img"))
        tempCover = str(
            BeautifulSoup(str(coverSelect), "lxml", exclude_encodings="utf-8")
        )
        index1 = tempCover.find("src=")
        tempCover = tempCover[index1 + 5:]
        index2 = tempCover.find('"')
        tempCover = tempCover[:index2]
        return tempCover

    def __get_score(self, soup):
        soupSelect = str(
            soup.select("#interest_sectl > div > div.rating_self.clearfix > strong")
        )
        soupTemp = BeautifulSoup(str(soupSelect), "lxml", exclude_encodings="utf-8")
        score = soupTemp.text.strip("[] \n\t")
        if score:
            s = float(score)
            return s
        else:
            return 0.0

    def __get_title(self, soup):
        soupSelect = str(soup.select("body>div>h1>span"))
        soupTemp = BeautifulSoup(str(soupSelect), "lxml", exclude_encodings="utf-8")
        return str(soupTemp.text).strip("[] \n\t")

    def __get_intro(self, soup):
        soupSelect = soup.select("#link-report")
        soupTemp = BeautifulSoup(str(soupSelect), "lxml", exclude_encodings="utf-8")
        intro = str(soupTemp.text).strip("[] \n\t")
        find = intro.find("(展开全部)")
        if find != -1:
            intro = intro[find + 6:]
        return intro.strip("[] \n\t")

    def __get_isbn(self, identifiers, soup):
        isbn = identifiers.get("isbn", None)
        if isbn:
            return isbn
        info = soup.select("#info")
        print(info)
        return '12312312312'


if __name__ == "__main__":  # tests {{{
    # To run these test use: calibre-debug -e src/calibre/ebooks/metadata/sources/douban.py
    from calibre.ebooks.metadata.sources.test import (
        test_identify_plugin,
        title_test,
        authors_test,
    )

    test_identify_plugin(
        Douban.name,
        [
            (
                {
                    "identifiers": {"isbn": "9787536692930"},
                    "title": "三体",
                    "authors": ["刘慈欣"],
                },
                [title_test("三体", exact=True), authors_test(["刘慈欣"])],
            ),
        ],
    )
# }}}
