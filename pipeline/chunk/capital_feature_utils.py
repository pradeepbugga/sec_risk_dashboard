import re

def capitalized_word_ratio(text):
    words = re.findall(r"[A-Za-z']+", text)

    if not words:
        return 0

    capitalized = 0
    eligible = 0

    stopwords = {"to", "of", "and", "in", "for", "on", "at", "with", "by", "our", "the"}

    for i, w in enumerate(words):
        if w.lower() in stopwords:
            continue
        if i == 0:
            continue  # ignore first word
        eligible += 1
        if w[0].isupper():
            capitalized += 1

    if eligible == 0:
        return 0

    return capitalized / eligible

def is_title_case(text):

    words = re.findall(r"[A-Za-z']+", text)

    if not words:
        return 0

    stopwords = {
        "to", "of", "and", "in", "for", "on", "at",
        "with", "by", "our", "the", "a", "an"
    }

    eligible = 0
    capitalized = 0

    for i, w in enumerate(words):

        if w.lower() in stopwords:
            continue

        if i == 0:
            # first word allowed to be capitalized in sentence case
            continue

        eligible += 1

        if w[0].isupper():
            capitalized += 1

    if len(words) == 1:
        return 1
    if eligible == 0:
        return 0

    ratio = capitalized / eligible

    # strict threshold for structural signal
    return 1 if ratio >= 0.8 else 0