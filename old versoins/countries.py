import sqlite3
import csv


conn = sqlite3.connect("db/countries.db")
c = conn.cursor()

with open('Countries.csv', 'r',encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile, delimiter=';', quotechar='|')
    for row in reader:
        c.execute("INSERT INTO countries VALUES (?,?,?,?,?,?,?,?,?,?)",(row[0],row[1],row[2],row[3],
                                                                row[4],row[5],row[6],row[8],row[9],
                                                                row[10]))
conn.commit()
conn.close()