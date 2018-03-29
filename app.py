from scrapy import cmdline

cmdline.execute('scrapy runspider "scrapnews/spiders/spider.py" -a countries="Russia, Argentina, USA" -a period=day'.split())