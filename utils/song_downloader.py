import os
import dandan
import urllib.parse 


url = "http://www.qqmusic.cc/gequlianjie/9177047.html"
location = r"E:\song"

logger = dandan.logger.getLogger("default")


QUALITY_128 = "128kbps"
QUALITY_320 = "320kbps"
QUALITY_FLAC = "FLAC无损"
QUALITY_APE = "APE无损"

QUALITIES = [QUALITY_128, QUALITY_320, QUALITY_FLAC, QUALITY_APE]

def download(url, quality=QUALITY_320):
    if not os.path.exists(location):
        os.makedirs(location)

    soup = dandan.query.soup(url, encoding="gbk")
    content = soup.select_one(".content")
    if not content:
        logger.fatal("cannot found .content")
        return

    singer = "Unknown"
    title = os.path.basename(url).split(".")[0]
    album = ""
    resource_url = ""

    ps = content.select("p")
    for p in ps:
        text = p.get_text().strip()
        if text.startswith("歌手："):
            singer = text.strip("歌手：")
            continue

        if text.startswith("歌名："):
            title = text.strip("歌名：")
            pass
        if text.startswith("下载："):
            hrefs = content.select("a")
            for href in hrefs:
                q = href.get_text()
                if q not in QUALITIES:
                    continue
                if q != quality:
                    continue
                break

            href = href.attrs.get("href", None)
            if not href:
                logger.fatal("cannot get resource url for quality %s", quality)
                return
            resource_url = urllib.parse.urljoin(url, href)
            break
    logger.info('''get song "%s - %s" from %s''', singer, title, resource_url)

    filename = os.path.join(location, "{} - {}.mp3".format(singer, title))

    logger.info("downloading %s to %s",resource_url, filename)
    dandan.traffic.download(resource_url, filename)


def main():
    logger.info("downloader starting...")
    download(url)


if __name__ == '__main__':
    main()
