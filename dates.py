from datetime import datetime
now = datetime.now()

MONTHS = {'january':'01','february':'02','march':'03','april':'04','may':'05','june':'06','july':'07','august':'08',
              'september':'09','october':'10','november':'11','december':'12',
              'jan':'01','feb':'02','mar':'03','apr':'04','jun':'06','jul':'07','aug':'08','sept':'09','oct':'10','nov':'11','dec':'12'}

def ismonth(str):

    if str.lower() in MONTHS.keys() or str in MONTHS.values():
        return True
    else:
        return False

def isyear(str):
    if str.isdigit() and 1000 <= int(str) <= 2200:
        return True
    else:
        return False

def isday(str):
    if str.isdigit() and 1 <= int(str) <= 12:
        return True
    else:
        return False



def process_dates(text):
    dates = []
    for i,t in enumerate(text):
        try:
            dt = datetime.strptime(t,'%m/%d/%Y')
            date = (str(dt.day),str(dt.month),str(dt.year))
            dates.append(date)
        except ValueError:
            if ismonth(t):
                if t.lower() in MONTHS.keys():
                    month = MONTHS[t.lower()]
                else:
                    month = t
                year = None
                day = None

                try:
                    if isyear(text[i+2]):
                        year = text[i+2]
                    if isday(text[i+2]):
                        day = text[i+2]
                except IndexError:
                    pass
                try:
                    if isyear(text[i-2]):
                        year = text[i-2]
                    if isday(text[i-2]):
                        day = text[i-2]
                except IndexError:
                    pass

                try:
                    if isyear(text[i+1]):
                        year = text[i+1]
                    if isday(text[i+1]):
                        day = text[i+1]
                except IndexError:
                    pass
                try:
                    if isyear(text[i-1]):
                        year = text[i-1]
                    if isday(text[i-1]):
                        day = text[i-1]
                except IndexError:
                    pass

                if not year:
                    year = now.year
                if not day:
                    day = now.day

                dates.append((str(day),str(month),str(year)))
    return dates


