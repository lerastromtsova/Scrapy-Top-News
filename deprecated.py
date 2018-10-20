def similar(topics):
    new_topics = list()

    for t in topics:
        if t is not None:
            others = []
            for to in topics:
                if to and set(to.news) != set(t.news):
                    others.append(to)

            similar = {t}
            freq_words = t.most_frequent()
            freq_words = freq_words[:ceil(len(freq_words) / 2)]

            for o in others:
                if o is not None:
                    try:

                        common_words = t.name.intersection(o.name)
                        common_news = set(t.news).intersection(set(o.news))
                        news_countries = {n.country for n in common_news}
                        where = {w for w in common_words if iscountry(w)}
                        who = {w for w in common_words if w[0].isupper() and not iscountry(w)}
                        what = {w for w in common_words if w[0].islower()}
                        cw_in_unique = t.new_name.intersection(o.new_name)
                        freq_words1 = o.most_frequent()
                        freq_words1 = freq_words1[:ceil(len(freq_words1) / 2)]
                        common_freq = intersection_with_substrings(freq_words1, freq_words)

                        # a
                        if len(where) >= 1 and len(who) >= 1 and len(what) >= 2:
                            print("A", o.name, t.name)
                            similar.add(o)
                            continue

                        # b
                        if len(where) >= 1 and len(who) >= 1 and len(what) >= 1 and len(common_news) >= 1:
                            print("B", o.name, t.name)
                            similar.add(o)
                            continue

                        # c
                        if len(news_countries) >= 2:
                            print("C", o.name, t.name)
                            similar.add(o)
                            continue

                        # d
                        if len(where) >= 1 and not who and len(what) >= 3:
                            print("D", o.name, t.name)
                            similar.add(o)
                            continue

                        # e
                        if len(where) >= 1 and not who and len(what) >= 2 and len(common_news) >= 1:
                            print("E", o.name, t.name)
                            similar.add(o)
                            continue

                        # f
                        if len(cw_in_unique) / len(t.new_name) > 0.5 and len(cw_in_unique) / len(o.new_name) > 0.5:
                            print("F", o.name, t.name)
                            similar.add(o)
                            continue

                        # g
                        if (len(common_freq) / len(freq_words) > 0.5 and len(common_freq) / len(
                                freq_words1) > 0.5) and len(cw_in_unique) >= 1:
                            print("G", o.name, t.name)
                            similar.add(o)

                    except ZeroDivisionError:
                        continue

            new_topic = Topic(t.name, init_news=t.news)
            for s in similar:
                new_topic.name.update(s.name)
                new_topic.main_words.update(t.main_words.intersection(s.main_words))
                new_topic.new_name.update(t.new_name.intersection(s.new_name))
                for n in s.news:
                    if n not in new_topic.news:
                        new_topic.news.extend(s.news)
                new_topic.subtopics.add(s)
                new_topic.most_frequent()
                topics[topics.index(s)] = None

            new_topic.news = list(set(new_topic.news))
            new_topics.append(new_topic)

    return new_topics

def assign_news(topics, rows):
    for row in rows:

        for topic in topics:

            cw_unique = {w for w in row.all_text if w in topic.new_name}

            if cw_unique:
                common_words = topic.name.intersection(row.all_text)
                where = {w for w in common_words if iscountry(w)}
                who = {w for w in common_words if w[0].isupper() and not iscountry(w)}
                what = {w for w in common_words if w[0].islower()}
                if len(where) >= 1 and (len(who) >= 1 and len(what) >= 2 or len(what) >= 3):
                    print("a")
                    print(topic.name)
                    print(row.id)
                    print(where, who, what)

                    topic.news.append(row)

                freq_words_50 = topic.most_frequent()[:ceil(len(topic.frequent) / 2)]
                cw_freq_50 = set(row.all_text).intersection(set(freq_words_50))

                try:

                    if len(cw_freq_50) / len(freq_words_50) > 0.5:
                        if len(where) >= 1 and len(who) >= 1 and len(what) >= 1:
                            if row not in topic.news:
                                print("b")
                                print(topic.name)
                                print(row.id)
                                print(where, who, what)
                                print(cw_freq_50)
                                topic.news.append(row)

                except ZeroDivisionError:
                    continue

    for topic in topics:
        topic.news = delete_dupl_from_news(topic.news)

    topics = delete_duplicates(topics)

    return topics

def find_objects(topics):
    new_topics = set()

    for topic in topics:

        for new in topic.news:

            objects = new.description.intersection(topic.new_name)

            if len(objects) >= 1:
                topic.objects.update(objects)
                new_topics.add(topic)

            for new1 in topic.news:

                if new != new1:

                    for i in range(len(new.sentences)):
                        for j in range(len(new1.sentences)):

                            unique_cw = {w for w in topic.new_name if w in new.sentences[i] and w in new1.sentences[j]}

                            if unique_cw:


                                cw = intersect(set(new.sentences[i].split()), set(new1.sentences[j].split()))

                                not_unique_cw = {word for word in cw - unique_cw if word[0].islower()}

                                if unique_cw and not_unique_cw:
                                    topic.obj.update(cw)
                                    new_topics.add(topic)

        cw_in_descr = topic.news[0].description.intersection(topic.news[1].description)

        topic.objects = {o for o in topic.objects if len(o) > 2}
        topic.obj = {o for o in topic.obj if len(o) > 2}

        if all(True if w[0].isupper() else False for w in topic.name):
            topic.name.update(topic.obj)

        if count_countries(cw_in_descr) >= 1 and count_not_countries(cw_in_descr) >= 2:
            new_topics.add(topic)

    return list(new_topics)


def extend_topic_names(topics):
    for topic in topics:
        if all(True if w[0].isupper() else False for w in topic.name):
            topic.name.update(topic.news[0].description.intersection(topic.news[1].description))

        if len([w for w in topic.name if w[0].islower()]) >= 1:
            topic.name.update(
                topic.news[0].named_entities['content'].intersection(topic.news[1].named_entities['content']))

    return topics


def add_words_to_topics(topics):

    for topic in topics:
        sent_dict = dict.fromkeys(list(range(len(topic.news))))

        for word in topic.new_name:

            common_words = set()

            for i, new in enumerate(topic.news):
                sent_dict[i] = {word: {w for sent in new.sentences for w in sent.split() if word in sent}}

            for i, new in enumerate(topic.news):
                common_words &= sent_dict[i][word]

            topic.name.update(common_words)

    return topics

def count_similar(word, words_list):
    c = 0
    for w in words_list:
        if w == word:
            c += 1
            continue
        if sublist(word, w) and len(w.split()) > 1:
            c += 1
    return c




def unite_fio1(topics):
    for topic in topics:

        fios = set()
        # text1 = topic.news[0].all_text_splitted.copy()
        # text1 = [w for w in text1 if len(w) > 1]
        # # print(text1)
        # strings_to_check1 = find_all_uppercase_sequences(text1)
        # strings_to_check2 = trim_words(strings_to_check2)

        strings_to_check1 = topic.news[0].uppercase_sequences
        strings_to_check2 = topic.news[1].uppercase_sequences

        print(1, strings_to_check1)
        print(2, strings_to_check2)

        common_strings = intersect_with_two(strings_to_check1, strings_to_check2)
        print(3, common_strings)
        # print(1, strings_to_check1)
        # print(2, strings_to_check2)
        # print(3, common_strings)

        fios.update(common_strings)

        short_strings1 = {w for w in strings_to_check1 if len(w.split()) <= 2}

        short_strings2 = {w for w in strings_to_check2 if len(w.split()) <= 2}
        print("short1", short_strings1)
        print("short2", short_strings2)

        for word1 in short_strings1:
            for word2 in short_strings2:
                if len(word2.split()) >= 2:
                    if word1 == word2.split()[-1]:
                        if any(w for w in strings_to_check1 if word1 == w.split()[-1] and word1 != w and w != word2) \
                                and any(w for w in strings_to_check2 if word1 == w.split()[
                            -1] and word1 != w and w != word2):  # if word1 consists in any fios in sequences1 and 2
                            pass
                        else:
                            print(word2)
                            fios.add(word2)
                if len(word1.split()) >= 2:
                    if word2 == word1.split()[-1]:
                        if any(w for w in strings_to_check2 if word2 == w.split()[-1] and word2 != w and w != word1) \
                                and any(
                            w for w in strings_to_check1 if word2 == w.split()[-1] and word2 != w and w != word1):
                            pass
                        else:
                            print(word1)
                            fios.add(word1)

        topic.news[0].all_text.update(set(fios))
        topic.news[1].all_text.update(set(fios))

        topic.name = intersect(topic.news[0].all_text, topic.news[1].all_text)
        print("Name", topic.name)

        # to_remove = set()
        #
        # for str1 in strings_to_check1:
        #     for str2 in strings_to_check2:
        #         if str1.split()[0] == str2.split()[0]:
        #             if str1 != str2:
        #                 if str1.split()[0] in topic.name:
        #                     to_remove.add(str1.split()[0])
        #
        # topic.name -= to_remove

        name = topic.name.copy()

        name = unite_countries_in(name)

        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}
                print(word)

        topic.name = name

        short_to_check = {w for w in name if len(w.split()) == 1 and not iscountry(w) and w[0].isupper()}

        long = name - short_to_check

        checked_entities = check_first_entities(short_to_check)
        checked_lower = {w for w in checked_entities.keys() if not checked_entities[w]}
        checked_upper = {w for w in checked_entities.keys() if checked_entities[w]}

        name = long | checked_upper

        name = name | checked_lower

        topic.name = name

        to_remove = set()

        for word in topic.name:

            try:
                words1_containing = {w for w in strings_to_check1 if
                                     word == w.split()[-2] or word == w.split()[-2] + "s" and word != w}
            except IndexError:
                words1_containing = {w for w in strings_to_check1 if
                                     word == w.split()[0] or word == w.split()[0] + "s" and word != w}
            try:
                words2_containing = {w for w in strings_to_check2 if
                                     word == w.split()[-2] or word == w.split()[-2] + "s" and word != w}
            except IndexError:
                words2_containing = {w for w in strings_to_check2 if
                                     word == w.split()[0] or word == w.split()[0] + "s" and word != w}

            if words1_containing and words2_containing and not words1_containing.intersection(words2_containing):
                to_remove.add(word)

        name -= to_remove
        topic.name = name

        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}

        topic.name = name
        # print(topic.name)
        # print("\n")
        topic.new_name = topic.name.copy()
        # print(topic.name)

    return topics

def last_check_topics(topics):
    positive = set()
    negative = set()
    for topic in topics:

        topic.frequent = topic.most_frequent()

        if len(topic.frequent) >= 8:
            freq_50 = topic.frequent[:ceil(len(topic.frequent) / 2)]
        elif 4 <= len(topic.frequent) <= 8:
            freq_50 = topic.frequent[:4]
        else:
            freq_50 = topic.frequent[:len(topic.frequent)]

        if len(freq_50) >= 3:
            positive.add(topic)
        elif len(freq_50) >= 2 and len(topic.new_name) >= 1 and count_countries(topic.name) >= 1:
            positive.add(topic)
    negative = {t for t in topics if t not in positive}
    return positive, negative


def check_neutral_topics_copy(topics):
    positive = set()
    for topic in topics:
        """ 2)	Хотя бы есть среди уникальных 1Загл, 1ФИО, 1 прописн
            3)	Хотя бы есть среди уникальных 1ФИО 1 прописн 1СТ
            4)	Хотя бы есть среди уникальных 1 ФИО 2 прописных
            5)	Хотя бы есть среди уникальных 1 Загл 3 прописных
            6)	Хотя бы есть среди уникальных 2 Загл 1 прописн 1 СТ
            7)	Хотя бы есть 2 ФИО,  среди уникальных 1 ФИО 1 Загл
            8)	Хотя бы есть 2 ФИО,  среди уникальных 1 ФИО 2 СТ
            9)	Хотя бы есть 7 Всех слов, среди уникальных 1 ФИО
            10)	Хотя бы есть 7 Всех слов, среди уникальных 1 Загл
            11)	Хотя бы есть 3 прописных слов, среди уникальных 1 Загл
            12)	 Хотя бы есть 5 Всех слов, 2 прописных, среди уникальных 1 Загл
            13)	Хотя бы есть 1 ФИО, среди уникальных 2 Загл
            14)	Хотя бы есть 4 прописных, среди уникальных 3 прописных
            15) 1 ФИО, 3 прописных - проходит 
            16) 2 Загл, 2 прописных - проходит
            17) 1 прописное, среди уникальных 2 Загл - проходит 
        """
        all_words, num_all_words = topic.all_words(topic.name)
        # all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_small_and_countries(all_words)
        fio, num_fio = topic.fio(all_words)
        big, num_big = topic.big(all_words)
        small, num_small = topic.small(all_words)
        # countries, num_countries = topic.countries(all_words)

        unique_words, num_unique_words = topic.all_words(topic.new_name)
        # unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        # unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_small_and_countries(unique_words)
        unique_fio, num_unique_fio = topic.fio(unique_words)
        unique_big, num_unique_big = topic.big(unique_words)
        unique_small, num_unique_small = topic.small(unique_words)
        unique_countries, num_unique_countries = topic.countries(unique_words)
        unique_ids, _ = topic.ids(unique_words)

        # 2
        if num_unique_big >= 1 and num_unique_fio >= 1 and num_unique_small >= 1:
            positive.add(topic)
            topic.method.add('2) уникальных 1Загл, 1ФИО, 1 прописн - проходит ')
            continue

        # 3
        if num_unique_countries >= 1 and num_unique_fio >= 1 and num_unique_small >= 1:
            positive.add(topic)
            topic.method.add('3) уникальных 1ФИО 1 прописн 1СТ - проходит')
            continue

        # 4
        if num_unique_fio >= 1 and num_unique_small >= 2:
            positive.add(topic)
            topic.method.add('4) уникальных 1 ФИО 2 прописных - проходит ')
            continue

        # 5
        if num_unique_big >= 1 and num_unique_small >= 3:
            positive.add(topic)
            topic.method.add('5) уникальных 1 Загл 3 прописных - проходит ')
            continue

        # 6
        if num_unique_big >= 2 and num_unique_small >= 1 and num_unique_countries >= 1:
            positive.add(topic)
            topic.method.add('6) уникальных 2 Загл 1 прописн 1 СТ - проходит ')
            continue

        # 7
        if num_fio >= 2 and num_unique_fio >= 1 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('7) 2 ФИО, среди уникальных 1 ФИО 1 Загл - проходит ')
            continue

        # 8
        if num_fio >= 2 and num_unique_fio >= 1 and num_unique_countries >= 2:
            positive.add(topic)
            topic.method.add('8) 2 ФИО, среди уникальных 1 ФИО 2 СТ - проходит ')
            continue

        # 9
        if num_all_words >= 7 and num_unique_fio >= 1:
            positive.add(topic)
            topic.method.add('9) 7 Всех слов, среди уникальных 1 ФИО - проходит ')
            continue

        # 10
        if num_all_words >= 7 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('10) 7 Всех слов, среди уникальных 1 Загл - проходит ')
            continue

        # 11
        if num_small >= 3 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('11) 3 прописных слов, среди уникальных 1 Загл - проходит ')
            continue

        # 12
        if num_all_words >= 5 and num_small >= 2 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('12) 5 Всех слов, 2 прописных, среди уникальных 1 Загл - проходит ')
            continue

        # 13
        if num_fio >= 1 and num_unique_big >= 2:
            positive.add(topic)
            topic.method.add('13) 1 ФИО, среди уникальных 2 Загл - проходит ')
            continue

        # 14
        if num_small >= 4 and num_unique_small >= 3:
            positive.add(topic)
            topic.method.add('14) 4 прописных, среди уникальных 3 прописных - проходит')
            continue

        # 15
        if num_fio >= 1 and num_small >= 3:
            positive.add(topic)
            topic.method.add('15) 1 ФИО, 3 прописных - проходит ')
            continue

        # 16
        if num_big >= 2 and num_small >= 2:
            positive.add(topic)
            topic.method.add('16) 2 Загл, 2 прописных - проходит ')
            continue

        # 17
        if num_small >= 1 and num_unique_big >= 2:
            positive.add(topic)
            topic.method.add('17) 1 прописное, среди уникальных 2 Загл - проходит ')
            continue

    return positive


def check_neutral_topics(topics, coefficients):
    positive = set()
    for topic in topics:
        all_words, num_all_words = topic.all_words(topic.name)
        # all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_small_and_countries(all_words)
        fio, num_fio = topic.fio(all_words)
        big, num_big = topic.big(all_words)
        small, num_small = topic.small(all_words)
        ids, num_ids = topic.ids(all_words)
        countries, num_countries = topic.countries(all_words)

        unique_words, num_unique_words = topic.all_words(topic.new_name)
        # unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        # unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_small_and_countries(unique_words)
        unique_fio, num_unique_fio = topic.fio(unique_words)
        unique_big, num_unique_big = topic.big(unique_words)
        unique_small, num_unique_small = topic.small(unique_words)
        unique_countries, num_unique_countries = topic.countries(unique_words)
        unique_ids, num_unique_ids = topic.ids(unique_words)

        result = 0

        result += num_fio * coefficients['fio']
        result += num_big * coefficients['big']
        result += num_small * coefficients['small']
        result += num_ids * coefficients['ids']
        if num_countries >= 2:
            result += num_countries * coefficients['countries']

        result += num_unique_fio * coefficients['ufio']
        result += num_unique_big * coefficients['ubig']
        result += num_unique_small * coefficients['usmall']
        result += num_unique_ids * coefficients['uids']
        result += num_unique_countries * coefficients['ucountries']

        if result >= 1:
            topic.result = result
            positive.add(topic)

    return positive


def last_check_topics(topics):
    positive = set()
    negative = set()
    for topic in topics:

        topic.frequent = topic.most_frequent()

        if len(topic.frequent) >= 8:
            freq_50 = topic.frequent[:ceil(len(topic.frequent) / 2)]
        elif 4 <= len(topic.frequent) <= 8:
            freq_50 = topic.frequent[:4]
        else:
            freq_50 = topic.frequent[:len(topic.frequent)]

        if len(freq_50) >= 3:
            positive.add(topic)
        elif len(freq_50) >= 2 and len(topic.new_name) >= 1 and count_countries(topic.name) >= 1:
            positive.add(topic)
    negative = {t for t in topics if t not in positive}
    return positive, negative


def check_neutral_topics_copy(topics):
    positive = set()
    for topic in topics:
        """ 2)	Хотя бы есть среди уникальных 1Загл, 1ФИО, 1 прописн
            3)	Хотя бы есть среди уникальных 1ФИО 1 прописн 1СТ
            4)	Хотя бы есть среди уникальных 1 ФИО 2 прописных
            5)	Хотя бы есть среди уникальных 1 Загл 3 прописных
            6)	Хотя бы есть среди уникальных 2 Загл 1 прописн 1 СТ
            7)	Хотя бы есть 2 ФИО,  среди уникальных 1 ФИО 1 Загл
            8)	Хотя бы есть 2 ФИО,  среди уникальных 1 ФИО 2 СТ
            9)	Хотя бы есть 7 Всех слов, среди уникальных 1 ФИО
            10)	Хотя бы есть 7 Всех слов, среди уникальных 1 Загл
            11)	Хотя бы есть 3 прописных слов, среди уникальных 1 Загл
            12)	 Хотя бы есть 5 Всех слов, 2 прописных, среди уникальных 1 Загл
            13)	Хотя бы есть 1 ФИО, среди уникальных 2 Загл
            14)	Хотя бы есть 4 прописных, среди уникальных 3 прописных
            15) 1 ФИО, 3 прописных - проходит 
            16) 2 Загл, 2 прописных - проходит
            17) 1 прописное, среди уникальных 2 Загл - проходит 
        """
        all_words, num_all_words = topic.all_words(topic.name)
        # all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_small_and_countries(all_words)
        fio, num_fio = topic.fio(all_words)
        big, num_big = topic.big(all_words)
        small, num_small = topic.small(all_words)
        # countries, num_countries = topic.countries(all_words)

        unique_words, num_unique_words = topic.all_words(topic.new_name)
        # unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        # unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_small_and_countries(unique_words)
        unique_fio, num_unique_fio = topic.fio(unique_words)
        unique_big, num_unique_big = topic.big(unique_words)
        unique_small, num_unique_small = topic.small(unique_words)
        unique_countries, num_unique_countries = topic.countries(unique_words)
        unique_ids, _ = topic.ids(unique_words)

        # 2
        if num_unique_big >= 1 and num_unique_fio >= 1 and num_unique_small >= 1:
            positive.add(topic)
            topic.method.add('2) уникальных 1Загл, 1ФИО, 1 прописн - проходит ')
            continue

        # 3
        if num_unique_countries >= 1 and num_unique_fio >= 1 and num_unique_small >= 1:
            positive.add(topic)
            topic.method.add('3) уникальных 1ФИО 1 прописн 1СТ - проходит')
            continue

        # 4
        if num_unique_fio >= 1 and num_unique_small >= 2:
            positive.add(topic)
            topic.method.add('4) уникальных 1 ФИО 2 прописных - проходит ')
            continue

        # 5
        if num_unique_big >= 1 and num_unique_small >= 3:
            positive.add(topic)
            topic.method.add('5) уникальных 1 Загл 3 прописных - проходит ')
            continue

        # 6
        if num_unique_big >= 2 and num_unique_small >= 1 and num_unique_countries >= 1:
            positive.add(topic)
            topic.method.add('6) уникальных 2 Загл 1 прописн 1 СТ - проходит ')
            continue

        # 7
        if num_fio >= 2 and num_unique_fio >= 1 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('7) 2 ФИО, среди уникальных 1 ФИО 1 Загл - проходит ')
            continue

        # 8
        if num_fio >= 2 and num_unique_fio >= 1 and num_unique_countries >= 2:
            positive.add(topic)
            topic.method.add('8) 2 ФИО, среди уникальных 1 ФИО 2 СТ - проходит ')
            continue

        # 9
        if num_all_words >= 7 and num_unique_fio >= 1:
            positive.add(topic)
            topic.method.add('9) 7 Всех слов, среди уникальных 1 ФИО - проходит ')
            continue

        # 10
        if num_all_words >= 7 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('10) 7 Всех слов, среди уникальных 1 Загл - проходит ')
            continue

        # 11
        if num_small >= 3 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('11) 3 прописных слов, среди уникальных 1 Загл - проходит ')
            continue

        # 12
        if num_all_words >= 5 and num_small >= 2 and num_unique_big >= 1:
            positive.add(topic)
            topic.method.add('12) 5 Всех слов, 2 прописных, среди уникальных 1 Загл - проходит ')
            continue

        # 13
        if num_fio >= 1 and num_unique_big >= 2:
            positive.add(topic)
            topic.method.add('13) 1 ФИО, среди уникальных 2 Загл - проходит ')
            continue

        # 14
        if num_small >= 4 and num_unique_small >= 3:
            positive.add(topic)
            topic.method.add('14) 4 прописных, среди уникальных 3 прописных - проходит')
            continue

        # 15
        if num_fio >= 1 and num_small >= 3:
            positive.add(topic)
            topic.method.add('15) 1 ФИО, 3 прописных - проходит ')
            continue

        # 16
        if num_big >= 2 and num_small >= 2:
            positive.add(topic)
            topic.method.add('16) 2 Загл, 2 прописных - проходит ')
            continue

        # 17
        if num_small >= 1 and num_unique_big >= 2:
            positive.add(topic)
            topic.method.add('17) 1 прописное, среди уникальных 2 Загл - проходит ')
            continue

    return positive


def check_neutral_topics(topics, coefficients):
    positive = set()
    for topic in topics:
        all_words, num_all_words = topic.all_words(topic.name)
        # all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_small_and_countries(all_words)
        fio, num_fio = topic.fio(all_words)
        big, num_big = topic.big(all_words)
        small, num_small = topic.small(all_words)
        ids, num_ids = topic.ids(all_words)
        countries, num_countries = topic.countries(all_words)

        unique_words, num_unique_words = topic.all_words(topic.new_name)
        # unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        # unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_small_and_countries(unique_words)
        unique_fio, num_unique_fio = topic.fio(unique_words)
        unique_big, num_unique_big = topic.big(unique_words)
        unique_small, num_unique_small = topic.small(unique_words)
        unique_countries, num_unique_countries = topic.countries(unique_words)
        unique_ids, num_unique_ids = topic.ids(unique_words)

        result = 0

        result += num_fio * coefficients['fio']
        result += num_big * coefficients['big']
        result += num_small * coefficients['small']
        result += num_ids * coefficients['ids']
        if num_countries >= 2:
            result += num_countries * coefficients['countries']

        result += num_unique_fio * coefficients['ufio']
        result += num_unique_big * coefficients['ubig']
        result += num_unique_small * coefficients['usmall']
        result += num_unique_ids * coefficients['uids']
        result += num_unique_countries * coefficients['ucountries']

        if result >= 1:
            topic.result = result
            positive.add(topic)

    return positive




def unite_fio_copy(topics):
    for topic in topics:

        fios1 = set()
        fios2 = set()

        text1 = topic.news[0].all_text_splitted.copy()
        strings_to_check1 = [' '.join(b) for a, b in itertools.groupby(text1, key=lambda x: x[0].isupper() and x.lower() not in STOP_WORDS) if a]
        for k in range(3):
            strings_to_check1 = [word if len(word) > 1 and not word.split()[0][0].islower() else " ".join(word.split()[1:]) for word in strings_to_check1]
            strings_to_check1 = [word if len(word) > 1 and not word.split()[-1][0].islower() else " ".join(word.split()[:-1]) for word in strings_to_check1]
            strings_to_check1 = [word if word.lower() not in STOP_WORDS else "" for word in strings_to_check1]
        strings_to_check1 = [word for word in strings_to_check1 if word]


        def split_by_two_words(strings_to_check):
            strings_to_check_copy = strings_to_check.copy()

            for word in strings_to_check:
                word_splitted = word.split()
                by_two = []
                if len(word_splitted) > 2:
                    for i in range(len(word_splitted)-1):
                        by_two.append(word_splitted[i]+" "+word_splitted[i+1])
                if by_two:
                    strings_to_check_copy.remove(word)
                    strings_to_check_copy.extend(by_two)

            return strings_to_check_copy

        strings_to_check1 = split_by_two_words(strings_to_check1)

        text2 = topic.news[1].all_text_splitted.copy()
        strings_to_check2 = [' '.join(b) for a, b in itertools.groupby(text2, key=lambda x: x[0].isupper() and x.lower() not in STOP_WORDS or x[0].isupper()) if a]
        for k in range(3):
            strings_to_check2 = [word if len(word) > 1 and not word.split()[0][0].islower() else " ".join(word.split()[1:]) for word in strings_to_check2]
            strings_to_check2 = [word if len(word) > 1 and not word.split()[-1][0].islower() else " ".join(word.split()[:-1]) for word in strings_to_check2]
            strings_to_check2 = [word if word.lower() not in STOP_WORDS else '' for word in strings_to_check2]
        strings_to_check2 = [word for word in strings_to_check2 if word]

        strings_to_check2 = split_by_two_words(strings_to_check2)

        for word1 in strings_to_check1:
            if strings_to_check1.count(word1) >= 2:
                fios1.add(word1)
                continue
            if strings_to_check1.count(word1) >= 1 and strings_to_check2.count(word1) >= 1:
                fios1.add(word1)
                continue
            if any(True if w in word1 else False for w in strings_to_check2):
                fios1.add(word1)
                continue

        for word2 in strings_to_check2:
            if strings_to_check2.count(word2) >= 2:
                fios2.add(word2)
                continue
            if strings_to_check2.count(word2) >= 1 and strings_to_check1.count(word2) >= 1:
                fios2.add(word2)
                continue
            if any(True if w in word2 else False for w in strings_to_check1):
                fios2.add(word2)
                continue

        topic.news[0].all_text.update(set(fios1))
        topic.news[1].all_text.update(set(fios2))

        # topic.name = topic.news[0].all_text.intersection(topic.news[1].all_text)
        topic.name = intersection_with_substrings(topic.news[0].all_text, topic.news[1].all_text)
        name = topic.name.copy()

        name = unite_countries_in(name)

        for word in topic.name:
            if any(True if word in w else False for w in topic.name - {word}):
                name -= {word}

        topic.name = name
        # print(topic.name)
        topic.new_name = topic.name.copy()

    return topics

def split_into_single(dataset):
    new_dataset = set()
    for d in dataset:
        for s in d.split(' '):
            if not all(True if w.isupper() else False for w in s):
                new_dataset.add(s)
            else:
                new_dataset.add(d)
    return new_dataset


def delete_without_lower(topics):
    new_topics = []
    for topic in topics:
        if not all(True if w[0].isupper() or w.isdigit() else False for w in topic.name):
            new_topics.append(topic)

    return new_topics





def filter_topics_copy(topics):

    positive = set()
    for topic in topics:

        # All words
        all_words, num_all_words = topic.all_words(topic.name)
        # if num_all_words >= 9:
        #     positive.add(topic)
        #     topic.method.add('9 "ВСЕ СЛОВА" - проходит ')
        #     continue
        # elif num_all_words <= 1:
        #     negative.add(topic)
        #     continue

        # All w/o countries
        all_wo_countries, num_all_wo_countries = topic.all_wo_countries(all_words)
        # if num_all_wo_countries >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ВСЕ СЛОВА – Страны" - проходит')
        #     continue
        # elif num_all_wo_countries <= 1:
        #     negative.add(topic)
        #     continue

        # All w/o small & countries
        all_wo_small_and_countries, num_all_wo_small_and_countries = topic.all_wo_countries_and_small(all_words)
        # if num_all_wo_small_and_countries >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ВСЕ СЛОВА - Прописные и Страны" - проходит ')
        #     continue

        # FIO
        fio, num_fio = topic.fio(all_words)
        # if num_fio >= 3:
        #     positive.add(topic)
        #     topic.method.add('3 "ФИО" - проходит ')
        #     continue

        # Big letter
        big, num_big = topic.big(all_words)
        # if num_big >= 4:
        #     positive.add(topic)
        #     topic.method.add('4 "ЗАГЛАВНЫЕ" - проходит ')
        #     continue

        # Small - already count
        small, num_small = topic.small(all_words)
        # if num_small >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ПРОПИСНЫЕ" - проходит ')
        #     continue

        # Countries - already count
        countries, num_countries = topic.countries(all_words)
        # if num_countries >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "СТРАНЫ" - проходит ')
        #     continue

        # All unique
        unique_words, num_unique_words = topic.all_words(topic.new_name)
        # if num_unique_words >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ВСЕ УНИКАЛЬНЫЕ" - проходит ')
        #     continue
        # elif num_unique_words == 0:
        #     negative.add(topic)
        #     continue

        # Unique w/o countries
        unique_wo_countries, num_unique_wo_countries = topic.all_wo_countries(unique_words)
        # if num_unique_wo_countries >= 5:
        #     positive.add(topic)
        #     topic.method.add('5 "ВСЕ УНИКАЛЬНЫЕ - Страны" - проходит ')
        #     continue
        # elif num_unique_wo_countries == 0:
        #     negative.add(topic)
        #     continue

        # Unique w/o countries and small
        unique_wo_small_countries, num_unique_wo_small_countries = topic.all_wo_countries_and_small(unique_words)
        # if num_unique_wo_small_countries >= 3:
        #     positive.add(topic)
        #     topic.method.add('3 "ВСЕ УНИКАЛЬНЫЕ - Страны и Прописные" - проходит ')
        #     continue

        # Unique FIO
        unique_fio, num_unique_fio = topic.fio(unique_words)
        # if num_unique_fio >= 2:
        #     positive.add(topic)
        #     topic.method.add('2 "УНИКАЛЬНЫЕ ФИО" - проходит ')
        #     continue

        # Unique big
        unique_big, num_unique_big = topic.big(unique_words)
        # if num_unique_big >= 3:
        #     positive.add(topic)
        #     topic.method.add('3 "УНИКАЛЬНЫЕ ЗАГЛАВНЫЕ" - проходит ')
        #     continue

        # Unique small - already count
        unique_small, num_unique_small = topic.small(unique_words)
        # if num_unique_small >= 4:
        #     positive.add(topic)
        #     topic.method.add('4 "УНИКАЛЬНЫЕ ПРОПИСНЫЕ" - проходит ')
        #     continue

        # Unique countries - already count
        unique_countries, num_unique_countries = topic.countries(unique_words)
        # if num_unique_countries >= 3:
        #     positive.add(topic)
        #     topic.method.add('3 "УНИКАЛЬНЫЕ СТРАНЫ" - проходит ')
        #     continue

        # Unique IDs
        unique_ids, _ = topic.ids(unique_words)
        # if unique_ids:
        #     positive.add(topic)
        #     topic.method.add('1 "УНИКАЛЬНЫЕ id" - проходит ')
        #     continue

        # 1) 1 уФИО + 2 ФИО
        frequent = topic.most_frequent()
        num_frequent = len(frequent)

        if len(frequent) >= 8:
            frequent_50 = frequent[:ceil(len(frequent) / 2)]
        elif 4 <= len(frequent) <= 8:
            frequent_50 = frequent[:4]
        else:
            frequent_50 = frequent[:len(frequent)]

        num_frequent_50 = len(frequent_50)

        # 1) 1 уФИО + 2 ФИО

        if num_unique_fio >= 1 and num_fio >= 2 and num_countries >= 1 and (
                num_fio >= 3 or num_big >= 1 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('.1) уФИО + 2 ФИО')
            # continue

        # 2) 1 уФИО + 1 оЗагл
        if num_unique_fio >= 1 and num_big >= 1 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 2 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('.2) 1 уФИО + 1 оЗагл')
            # continue

        # 3) 1 уФИО + 2 оМал
        if num_unique_fio >= 1 and num_small >= 2 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 1 or num_small >= 3 or num_countries >= 3):
            positive.add(topic)
            topic.method.add('.3) 1 уФИО + 2 оМал')
            # continue

        # 4) 1 уЗагл + 1 оФИО
        if num_unique_big >= 1 and num_fio >= 1 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 2 or num_small >= 2 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('.4) 1 уЗагл + 1 оФИО')
            # continue

        # 5) 1 уЗагл + 2 оЗагл
        if num_unique_big >= 1 and num_big >= 2 and num_countries >= 1 and (
                num_unique_fio >= 1 or num_big >= 3 or num_unique_small >= 2 or num_unique_countries >= 2):
            positive.add(topic)
            topic.method.add('.5) 1 уЗагл + 2 оЗагл')
            # continue

        # 6) 1 уЗагл + 2 оМал
        if num_unique_big >= 1 and num_small >= 2 and num_countries >= 1 and (
                num_unique_fio >= 1 or num_unique_big >= 2 or num_unique_small >= 2 or num_unique_countries >= 2):
            positive.add(topic)
            topic.method.add('.6) 1 уЗагл + 2 оМал')
            # continue

        # 7) 1 уЗагл + 3 оСтр
        if num_unique_big >= 1 and num_countries >= 3 and (
                num_unique_fio >= 1 or num_unique_big >= 2 or num_unique_small >= 2 or num_countries >= 5):
            positive.add(topic)
            topic.method.add('.7) 1 уЗагл + 3 оСтр')
            # continue

        # 8) 2 уМал + 2 оФИО
        if num_unique_small >= 2 and num_fio >= 2 and num_countries >= 1 and (
                num_fio >= 3 or num_big >= 1 or num_small >= 2 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('.8) 2 уМал + 2 оФИО')
            # continue

        # 9) 2 уМал + 2 оЗагл
        if num_unique_small >= 2 and num_big >= 2 and num_countries >= 1 and (
                num_unique_fio >= 1 or num_unique_big >= 1 or num_unique_small >= 2 or num_unique_countries >= 2):
            positive.add(topic)
            topic.method.add('.9) 2 уМал + 2 оЗагл')
            # continue

        # 10) 4 уМал
        if num_unique_small >= 4 and num_countries >= 1 and (
                num_fio >= 1 or num_big >= 1 or num_small >= 5 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('10) 4 уМал ')
            # continue

        # 11) 3 оФИО
        if num_fio >= 3 and num_countries >= 1:
            positive.add(topic)
            topic.method.add('11) 3 оФИО')
            # continue

        # 12) 1 оФИО + 2 оЗагл
        if num_fio >= 1 and num_big >= 2 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 3 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('12) 1 оФИО + 2 оЗагл')
            # continue

        # 13) 1 оФИО + 2 оМал
        if num_fio >= 1 and num_small >= 2 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 1 or num_small >= 4 or num_countries >= 3):
            positive.add(topic)
            topic.method.add('13) 1 оФИО + 2 оМал')
            # continue

        # 14) 2 уФИО
        if num_unique_fio >= 2 and num_countries >= 1 and (
                num_fio >= 3 or num_big >= 1 or num_small >= 1 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('14) 2 уФИО ')
            # continue

        # 15) 3 уМал + 1 оФИО
        if num_unique_small >= 3 and num_fio >= 1 and num_countries >= 1 and (
                num_fio >= 3 or num_big >= 1 or num_small >= 3 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('15) 3 уМал + 1 оФИО')
            # continue

        # 16) 4 оЗагл
        if num_unique_big >= 4 and num_countries >= 1:
            positive.add(topic)
            topic.method.add('16) 4 оЗагл')
            # continue

        # 17) 1 оЗагл + 2 оМал
        if num_big >= 1 and num_small >= 2 and num_countries >= 1 and (
                num_fio >= 1 or num_big >= 2 or num_small >= 4 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('17) 1 оЗагл + 2 оМал')
            # continue

        # 18) 3 уЗагл
        if num_unique_big >= 3 and num_countries >= 1:
            positive.add(topic)
            topic.method.add('18) 3 уЗагл')
            # continue

        # 19) 3 оЗагл + 1 оМал
        if num_big >= 3 and num_small >= 1 and num_countries >= 1 and (
                num_fio >= 1 or num_big >= 4 or num_small >= 2 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('19) 3 оЗагл + 1 оМал')
            # continue

        # 20) 5 оСтран
        if num_countries >= 5 and num_countries >= 1:
            positive.add(topic)
            topic.method.add('20) 5 оСтран')
            # continue

        # 21) 2 уМал + 1 оЗагл
        if num_unique_small >= 2 and num_big >= 1 and num_countries >= 1 and (
                num_fio >= 1 or num_big >= 2 or num_small >= 3 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('21) 2 уМал + 1 оЗагл')
            # continue

        # 22) 1 уФИО + 2 уМал
        if num_unique_fio >= 1 and num_unique_small >= 2 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 1 or num_small >= 2 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('22) 1 уЗагл + 2 уМал')
            # continue

        # 23) 4 уМал
        if num_unique_small >= 4 and num_countries >= 1 and (
                num_fio >= 1 or num_big >= 1 or num_small >= 5 or num_countries >= 2):
            positive.add(topic)
            topic.method.add('23) 4 уМал')
            # continue

        # 24) 1 уФИО + 2 уСтран
        if num_unique_fio >= 1 and num_unique_countries >= 2:
            positive.add(topic)
            topic.method.add('25) 1 уФИО + 2 уСтран')
            # continue

        # 25) 2 уМал + Страны
        if num_unique_small >= 2 and num_unique_countries >= 2 and (
                num_fio >= 1 or num_big >= 1 or num_small >= 2 or num_countries >= 3):
            positive.add(topic)
            topic.method.add('26) 2 уМал + 1 уСтран')
            # continue

        # 26) 3 уСтр
        if num_unique_countries >= 3 and (num_fio >= 1 or num_big >= 2 or num_small >= 1 or num_countries >= 5):
            positive.add(topic)
            topic.method.add('27) 3 уСтр')
            # continue

        # 27) 2 уМал + 1 оФИО
        if num_unique_small >= 2 and num_small >= 2 and num_fio >= 1 and num_countries >= 1 and (
                num_fio >= 2 or num_big >= 1 or num_small >= 3 or num_countries >= 3):
            positive.add(topic)
            topic.method.add('27) 2 уМал + 1 оФИО')
            # continue

    negative = {topic for topic in topics if topic not in positive}
    return positive, negative


def unite_topics_by_news(topics):

    to_remove = set()
    to_add = set()

    for topic in topics:
        other_topics = [t for t in topics if t != topic]
        for other_topic in other_topics:
            common_news = [n for n in topic.news if n in other_topic.news]
            if len(topic.news)-len(common_news)<=1 or len(other_topic.news)-len(common_news)<=1:
                    news = topic.news.copy()
                    news.extend(other_topic.news)
                    name = topic.name.union(other_topic.name)

                    new_topic = Topic(name, news)
                    new_topic.news = delete_dupl_from_news(new_topic.news)
                    f, _ = filter_topics([new_topic])
                    if f:
                        to_add.add(new_topic)
                        to_remove.add(topic)
                        to_remove.add(other_topic)

    topics = [t for t in topics if t not in to_remove]
    topics.extend(to_add)
    topics = delete_duplicates(topics)

    return topics

def unite_topics(topics):
    for i, topic in enumerate(topics):
        if topic:
            topic.subtopics = set()
            others = [t for t in corpus.topics if t and set(t.news) != set(topic.news)]
            similar = {}
            topic_copy = Topic(topic.name.copy(), topic.news.copy())
            topic_copy.new_name = topic.new_name.copy()

            for ot in others:
                if ot:
                    new_name = unite_news_text_and_topic_name(topic.name, ot.name)
                    new_unique = unite_news_text_and_topic_name(topic.new_name, ot.name)
                    news_list = list(set(topic.news).union(set(ot.news)))

                    new_topic = Topic(new_name, news_list)
                    new_topic.new_name = new_unique
                    t, _ = filter_topics([new_topic])
                    if t:
                        similar[ot] = t.pop().method

            if similar:
                similar[topic_copy] = ''
                for s, m in similar.items():
                    topic.subtopics.add(s)
                    s.method = m
                    topic.news.extend(s.news)

                topic.news = delete_dupl_from_news(topic.news)
    return topics


def define_main_topics_copy(topics):

    topic_indicators = {topic: False for topic in topics}  # True if topic is main or added to other

    for i, topic in enumerate(topics):
        if not topic_indicators[topic]:
            old_name = {}
            other_topics = [t for t in topics if not topic_indicators[t] and t != topic]
            while old_name != topic.name:
                old_name = topic.name.copy()
                topic = extend_topic(topic, other_topics, topic_indicators)


    return topics


def extend_topic_copy(topic, other_topics, t_i):
    topic_copy = Topic(topic.name.copy(), topic.news.copy())
    topic_copy.new_name = topic.new_name.copy()

    def extend_first_topic():
        topic.name = topic.name.union(other_topic.name)
        topic.new_name = topic.new_name.union(other_topic.new_name)
        topic.news = new_topic.news
        topic.subtopics.add(other_topic)
        topic.subtopics.add(topic_copy)
        t_i[other_topic] = True
        t_i[topic] = True

    for other_topic in other_topics:

        new_name = unite_news_text_and_topic_name(topic.name, other_topic.name)
        new_unique = unite_news_text_and_topic_name(topic.new_name, other_topic.name)
        news_list = list(set(topic.news).union(set(other_topic.news)))
        new_topic = Topic(new_name, news_list)
        new_topic.new_name = new_unique
        t, _ = filter_topics([new_topic])
        if t:
            extend_first_topic()

        else:
            news_difference1 = {n for n in topic.news if n not in other_topic.news}
            news_difference2 = {n for n in other_topic.news if n not in topic.news}
            if len(news_difference1) <= 1 or len(news_difference2) <= 1:
                extend_first_topic()

    return topic
