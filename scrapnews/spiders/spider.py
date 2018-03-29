import scrapy
from googletrans import Translator
from scrapnews.items import NewsItem
from datetime import date
from nltk.corpus import wordnet as wn
import string
import sqlite3
import gensim

COUNTRIES = {'au': 'Australia',
             'ar':'Argentina',
             'am': 'Armenia',
             'by': 'Belarus',
             'bg': 'Bulgary',
             'br': 'Brazil',
             'gb': 'Great Britain',
             'ge': 'Georgia',
             'de': 'Germany',
             'gr': 'Greece',
             'in': 'India',
             'it': 'Italy',
             'kz': 'Kazakhstan',
             'ca': 'Canada',
             'mx': 'Mexica',
             'nl': 'Netherlands',
             'pt': 'Portugal',
             'ru': 'Russia',
             'ro': 'Romania',
             'us': 'USA',
             'uz': 'Uzbekistan',
             'sg': 'Singapore',
             'tr': 'Turkey',
             'ua': 'Ukraine',
             'fi': 'Finland',
             'fr': 'France',
             'cz': 'Czech Republic',
             'ch': 'Switzerland',
             'ee': 'Estonia',
             'jp': 'Japan'}

CO_REVERSED = {y:x for x,y in COUNTRIES.items()}

PERIODS = {'online','hour','day','week','month'}
PUNKTS = ["''",'``','...','’','‘','-']
STOP_WORDS = ["a","about","above","across","after","afterwards","again","against","all","almost","alone","along","already","also","although","always","am","among","amongst","amoungst","amount","an","and","another","any","anyhow","anyone","anything","anyway","anywhere","are","around","as","at","back","be","became","because","become","becomes","becoming","been","before","beforehand","behind","being","below","beside","besides","between","beyond","bill","both","bottom","but","by","call","can","cannot","cant","co","computer","con","could","couldnt","cry","de","describe","detail","do","done","down","due","during","each","eg","eight","either","eleven","else","elsewhere","empty","enough","etc","even","ever","every","everyone","everything","everywhere","except","few","fifteen","fify","fill","find","fire","first","five","for","former","formerly","forty","found","four","from","front","full","further","get","give","go","had","has","hasnt","have","he","hence","her","here","hereafter","hereby","herein","hereupon","hers","herself","him","himself","his","how","however","hundred","i","ie","if","in","inc","indeed","interest","into","is","it","its","itself","keep","last","latter","latterly","least","less","ltd","made","many","may","me","meanwhile","might","mill","mine","more","moreover","most","mostly","move","much","must","my","myself","name","namely","neither","never","nevertheless","next","nine","no","nobody","none","noone","nor","not","nothing","now","nowhere","of","off","often","on","once","one","only","onto","or","other","others","otherwise","our","ours","ourselves","out","over","own","part","per","perhaps","please","put","rather","re","same","see","seem","seemed","seeming","seems","serious","several","she","should","show","side","since","sincere","six","sixty","so","some","somehow","someone","something","sometime","sometimes","somewhere","still","such","system","take","ten","than","that","the","their","them","themselves","then","thence","there","thereafter","thereby","therefore","therein","thereupon","these","they","thick","thin","third","this","those","though","three","through","throughout","thru","thus","to","together","too","top","toward","towards","twelve","twenty","two","un","under","until","up","upon","us","very","via","was","we","well","were","what","whatever","when","whence","whenever","where","whereafter","whereas","whereby","wherein","whereupon","wherever","whether","which","while","whither","who","whoever","whole","whom","whose","why","will","with","within","without","would","yet","you","your","yours","yourself","yourselves","'s","wa","ha","s","di","'re","n't","c.","'ll","'m"]

def translate(text):
    t = Translator()
    return(t.translate(text).text)


def tokenize(text):
    tokens = [t.lower() for t in gensim.utils.tokenize(text) if t.lower() not in STOP_WORDS and t not in PUNKTS and t not in string.punctuation]
    tokens = [wn.morphy(t) if wn.morphy(t) is not None else t for t in tokens]
    return " ".join(tokens)


class NewsSpider(scrapy.Spider):
    name = "news"

    def __init__(self, countries, period, *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)
        if countries=="All":
            self.start_urls = ['https://top.st/' + co + "/" + period for co in COUNTRIES.keys()]
        else:
            self.start_urls = ['https://top.st/' + CO_REVERSED[country] + "/" + period for country in countries.split(', ')]

    def parse(self, response):
        conn = sqlite3.connect('topnews.db')
        c = conn.cursor()
        for i,new in enumerate(response.css('h2')):
            item = NewsItem()
            url = new.css('a::attr(href)').extract_first()
            title = new.css('a::text').extract_first()
            co = response.url.split('/')[-2]
            c.execute("SELECT * FROM topnews WHERE url=?",(url,))
            res = c.fetchone()
            if res:
                item['url'] = res[1]
                item['title'] = res[2]
                item['number'] = res[3]
                item['country'] = res[4]
                item['tokens'] = res[5]
                item['scraping_date'] = str(date.today())
                item['scraping_type'] = response.url.split('/')[-1]

                yield item

            else:
                if co not in ('gb','us'):
                    title = translate(title)

                item['url'] = url
                item['title'] = title
                item['number'] = i + 1
                item['country'] = COUNTRIES[co]
                item['tokens'] = tokenize(title)
                item['scraping_date'] = str(date.today())
                item['scraping_type'] = response.url.split('/')[-1]
                yield item

