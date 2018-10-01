# encoding = utf8
import sys
import dandan

reload(sys)
sys.setdefaultencoding("utf8")


def get_urls():
    url = "http://open.163.com/movie/2017/9/Q/S/MCTMNN3UI_MCTMNR8QS.html"

    soup = dandan.query.soup(url)

    urls = []

    for item in soup.select(".item.f-pr"):
        a = item.select_one("a.f-c6")
        if not a:
            urls.append(url)
            continue
        href = a.attrs.get('href')
        urls.append(href)

    print "get {} url".format(len(urls))
    return urls


def get_video_urls(url):

    api = "http://www.flvcd.com/parse.php"

    res = dandan.value.AttrDict()

    params = dandan.value.AttrDict()
    params.kw = url

    soup = dandan.query.soup(api, params=params, encoding="gbk")
    name = soup.select_one('input[name="name"]').attrs.get("value")
    video_url = soup.select_one('input[name="inf"]').attrs.get("value").strip("|")
    res.name = name
    res.url = video_url
    return res


def main():
    urls = get_urls()
    for url in urls:
        res = get_video_urls(url)
        print res.url
        print res.name
        print "---------------------------------------"

    # url = "http://open.163.com/movie/2017/9/Q/S/MCTMNN3UI_MCTMNR8QS.html"
    # print get_video_urls(url)


if __name__ == '__main__':
    main()
