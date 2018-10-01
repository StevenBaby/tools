# coding=utf-8
from __future__ import print_function, unicode_literals
import re
import sys
import os
import datetime
import json
import collections
import traceback
import dandan

reload(sys)
sys.setdefaultencoding("utf-8")


class Offset(object):

    def __init__(self, string='00:00:00'):
        self.string = string
        self.offset = None
        self.make()

    def get_match(self):
        patterns = [
            re.compile(r"(?P<symbol>-){0,1}(?P<minute>\d+):(?P<second>\d+)\.(?P<milli>\d+)"),
            re.compile(r"(?P<symbol>-){0,1}(?P<minute>\d+):(?P<second>\d+):(?P<milli>\d+)"),
            re.compile(r"(?P<symbol>-){0,1}(?P<minute>.*?)(?P<second>\d+).(?P<milli>\d+)"),
        ]
        for pattern in patterns:
            match = pattern.match(self.string)
            if match:
                return match

    def make(self):
        if self.offset:
            return
        match = self.get_match()
        if not match:
            print(self.string)
            raise Exception("string cannot much any pattern")

        power = 3 - len(match.group("milli"))
        millis = int(match.group("milli")) * (10 ** power)

        if match.group("minute"):
            minutes = int(match.group("minute"))
        else:
            minutes = 0

        seconds = int(match.group("second"))

        self.offset = datetime.timedelta(
            minutes=minutes,
            seconds=seconds,
            milliseconds=int(millis))
        if match.group("symbol"):
            self.offset = -self.offset

    def simple(self):
        total = int(self.offset.total_seconds() * 100)

        milli = total % 100
        total /= 100
        second = total % 60
        total /= 60
        minute = total

        string = "{minute:02}:{second:02}.{milli:02}".format(
            minute=minute,
            second=second,
            milli=milli,
        )
        return string

    def __str__(self):
        string = "[{}]".format(self.simple())
        return string

    def __add__(self, other):
        off = Offset()
        off.offset = self.offset + other.offset
        return off

    def __sub__(self, other):
        off = Offset()
        off.offset = self.offset - other.offset
        return off

    def __lt__(self, other):
        return self.offset < other.offset

    def __le__(self, other):
        return self.offset <= other.offset

    def __eq__(self, other):
        return self.offset == other.offset

    def __ne__(self, other):
        return self.offset != other.offset

    def __gt__(self, other):
        return self.offset > other.offset

    def __ge__(self, other):
        return self.offset >= other.offset


class Line(object):

    TYPE_LYRIC = 0
    TYPE_SOURCE = 1
    TYPE_DELAY = 2
    TYPE_SERIAL = 3
    TYPE_NONE = 4
    TYPE_SONGID = 5

    def __init__(self, offset=None, lyric=None, type=TYPE_LYRIC, content=""):
        self.offset = offset
        self.lyric = lyric
        self.type = type
        self.content = content

    def __str__(self):
        return "{}{}".format(self.offset.__str__(), self.lyric)


class Searcher(object):

    @classmethod
    def get_kuwo_id(cls, title, performer, serial=0):
        action = "http://sou.kuwo.cn/ws/NSearch"
        params = dandan.value.AttrDict()
        params.key = "{} - {}".format(performer, title)
        soup = dandan.query.soup(url=action, params=params)
        clearfixs = soup.select("div.list ul li.clearfix")
        for clearfix in clearfixs:
            s_name = clearfix.select_one(".s_name").get_text()
            if not s_name:
                continue
            match = re.search(r'''write\("(.*?)"''', s_name)
            if not match:
                continue
            s_name = match.group(1)
            if s_name != performer:
                continue

            m_name = clearfix.select_one(".m_name").get_text()
            if not m_name:
                continue
            match = re.search(r'''write\("(.*?)"''', m_name)
            if not match:
                continue
            m_name = match.group(1).replace(" ", "").lower()
            if title.lower() != m_name:
                continue
            if serial > 0:
                serial -= 1
                continue

            songid = clearfix.select_one(".number input").attrs.get("value")
            print('''Get "{} - {}" kuwo id "{}"'''.format(performer, title, songid))
            return songid

    @classmethod
    def search_kuwo(cls, title, performer, serial=0,songid=None):
        if not songid:
            songid = cls.get_kuwo_id(title, performer, serial)
        if not songid:
            return
        action = "http://m.kuwo.cn/newh5/singles/songinfoandlrc"
        params = dandan.value.AttrDict()
        params.musicId = songid

        json = dandan.query.json(url=action, params=params)
        if not json:
            return
        if "data" not in json:
            return
        if not json["data"]:
            return
        if "lrclist" not in json["data"]:
            return
        if not json["data"]["lrclist"]:
            return

        lyrics = []
        lyrics.append(Line(type=Line.TYPE_SOURCE, content="kuwo"))
        lyrics.append(Line(type=Line.TYPE_SONGID, content=songid))
        for lyric in json["data"]["lrclist"]:
            offset = Offset(lyric["time"])
            text = lyric["lineLyric"]
            line = Line(offset, text)
            lyrics.append(line)
        return lyrics

    @classmethod
    def search(cls, title, performer, source=None, serial=0, songid=None):
        if source and songid:
            name = "search_{}".format(source)
            if not hasattr(cls, name):
                return
            func = getattr(cls, name)
            result = func(title, performer, songid=songid)
            return result
        if source and serial != 0:
            name = "search_{}".format(source)
            if not hasattr(cls, name):
                return
            func = getattr(cls, name)
            result = func(title, performer, serial=serial)
            return result

        methods = []
        for name in dir(cls):
            if not name.startswith("search_"):
                continue
            attr = getattr(cls, name)
            if not callable(attr):
                continue
            methods.append(attr)

        for func in methods:
            print("{} - {} - {} ".format(func.__name__, performer, title,))
            result = func(title, performer)
            if result:
                return result


class Track(object):

    title_pattern = re.compile(r" <<(?P<title>.*)>> ")

    def __init__(self, title=None, index=None, performer=None):
        self.title = title
        self.performer = performer
        self.index = index
        self.lyrics = []
        self.source = ""
        self.serial = 0
        self.songid = 0
        self.delay = Offset()

    def __str__(self):
        return "{}-{}".format(self.title, self.index, )

    def search_lyric(self):
        lyrics = Searcher.search(
            title=self.title,
            performer=self.performer,
            source=self.source,
            serial=self.serial,
            songid=self.songid)
        if not lyrics:
            return
        self.lyrics = []
        for line in lyrics:
            if line.type == Line.TYPE_LYRIC:
                line.offset += self.index
                self.lyrics.append(line)
            elif line.type == Line.TYPE_SOURCE:
                self.source = line.content
            elif line.type == Line.TYPE_SONGID:
                self.songid = line.content

    def make_delay(self):
        for line in self.lyrics:
            line.offset += self.delay

        self.delay = Offset()

    def get_lyric(self):
        if not self.lyrics or self.serial > 0:
            self.search_lyric()
        title = "\n\n{} <<{}>> \n\n".format(self.index, self.title)
        source = "[source:{}]\n".format(self.source)
        serial = "[serial:{}]\n".format(0)
        songid = "[songid:{}]\n".format(self.songid)
        if self.delay != Offset():
            self.make_delay()

        delay = "[delay:{}]\n".format(self.delay.simple())

        self.lyrics = sorted(self.lyrics, key=lambda e: e.offset)
        result = title + source + songid + serial + delay
        return result + "\n".join([var.__str__() for var in self.lyrics])


class Cue(object):

    def __init__(self, name):
        self.name = name
        self.data = open(name).read()
        self.performer = ""
        self.title = ""
        self.tracks = collections.OrderedDict()

    def make_performer(self):
        pattern = re.compile(r'''PERFORMER "(.*)"''')

        match = pattern.search(self.data)
        if not match:
            return
        self.performer = match.group(1)

    def make_title(self):
        pattern = re.compile(r'''TITLE "(.*)"''')

        match = pattern.search(self.data)
        if not match:
            return
        self.title = match.group(1)

    def make_tracks(self):
        pattern = re.compile(r'''TRACK(.*?)TITLE(.*?)"(?P<title>.*?)"(.*?)PERFORMER(.*?)"(?P<performer>.*?)"\n(.*?)INDEX 01 (?P<index>.*?)\n''', re.DOTALL)
        # print pattern
        match = pattern.finditer(self.data)
        result = collections.OrderedDict()

        for var in match:
            title = var.group("title")
            performer = var.group("performer")
            index = Offset(string=var.group("index"))
            track = Track(title=title, index=index, performer=performer)
            result[title] = track
        self.tracks = result

    def make(self):
        self.make_performer()
        self.make_title()
        self.make_tracks()

    def make_lyrics(self):
        self.load_lyrics()
        self.save_lyrics()

    def load_lyrics(self):
        filename, _ = os.path.splitext(self.name)
        filename = u"{}.lrc".format(filename)
        if not os.path.exists(filename):
            return

        track = None
        for line in open(filename):
            source = re.match(r"\[source:(.+)\]\n", line)
            if source and track:
                track.source = source.group(1)
                continue
            serial = re.match(r"\[serial:(\d+)\]\n", line)
            if serial and track:
                track.serial = int(serial.group(1))
                continue
            delay = re.match(r"\[delay:(.+)\]\n", line)
            if delay and track:
                track.delay = Offset(delay.group(1))
                continue

            songid = re.match(r"\[songid:(.+)\]\n", line)
            if songid and track:
                track.songid = songid.group(1)
                continue

            match = re.match(r"\[(?P<offset>\d+:\d+.\d+)\](?P<lyric>.*)", line)
            if not match:
                continue

            offset = Offset(string=match.group("offset"))

            lyric = match.group("lyric")
            mtitle = Track.title_pattern.search(lyric)

            if not mtitle and track:
                line = Line(offset=offset, lyric=lyric)
                track.lyrics.append(line)
                continue
            if not mtitle:
                continue

            title = mtitle.group("title")
            if title in self.tracks:
                track = self.tracks[title]

    def save_lyrics(self):
        filename, _ = os.path.splitext(self.name)
        filename = u"{}.lrc".format(filename)
        with open(filename, "w") as f:
            f.write(u"[ar:{}]\n".format(self.performer))
            f.write(u"[al:{}]\n".format(self.title))
            for title, track in self.tracks.items():
                f.write(track.get_lyric())


def main():
    cue = Cue("刘欢.-.[名曲集-黑胶CD].专辑.(FLAC).cue")
    cue.make()
    cue.make_lyrics()


if __name__ == '__main__':
    main()
