import codecs
import sqlite3


# with codecs.open("cities.txt", "r",encoding='utf-8', errors='ignore') as fdata:
#     lines = fdata.readlines()

with codecs.open("data_json.json.txt", "r",encoding='utf-8', errors='ignore') as fdata:
    lines = fdata.readlines()

for line in lines:
    print(line)

conn = sqlite3.connect("db/cities.db")
c = conn.cursor()



# for line in lines:
#     l = line.split(',')
#     country_short = l[0]
#     city = l[1]
#     c.execute("INSERT OR REPLACE INTO countries(short_name) VALUES (?)",(country_short,))
#     c.execute("INSERT INTO cities(country,city_name) VALUES(?,?)",(country_short,city))

conn.commit()
conn.close()