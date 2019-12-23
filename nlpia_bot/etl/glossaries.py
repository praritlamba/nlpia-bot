# make sure you `pip install --upgrade git+https://github.com/lucasdnd/Wikipedia.git`
import os
import re

from tqdm import tqdm
# import pandas as pd
import yaml

# from nlpia_bot.spacy_language_model import nlp
from nlpia_bot.constants import DATA_DIR, STOPWORDS

import logging
log = logging.getLogger(locals().get('__name__'))


def find_hashtags(s, pattern=r'\s*#[\w\d_-]+'):
    """ Find twitter-style tags embedded within a string.

    >>> d = find_hashtags("Find #this hashtag #too #sarcasm-not.")
    >>> d['cleaned']
    'Find hashtag.'
    >>> d['hashtags']
    ['#sarcasm-not', '#this', '#too']
    """
    s = s or ''
    hashtags = re.findall(pattern, s) or []
    hashtags = sorted(set([t.strip() for t in hashtags]))
    cleaned = re.sub(pattern, '', s)
    return {'cleaned': cleaned, 'hashtags': hashtags}


def possible_acronyms(s, titlize=None):
    """ Extract first letter of each word to try to acronymize it 2 different ways

    >>> ' '.join(sorted(set(possible_acronyms("It\'s the End of the World as We Know It!"))))
    'EWK IEWWKI ItEotWaWKI'
    >>> ' '.join(sorted(set(possible_acronyms("It\'s the End of the World as We Know It!", titlize=True))))
    'EWK IEWWKI ITEOTWAWKI ItEotWaWKI'
    """
    if not titlize:
        tripples = re.findall(r'\W*((([A-Za-z0-9])[A-Za-z0-9\']*)[^a-zA-Z0-9]*)\W*', s)
        log.info(tripples)
        # print(tripples)
        first_letters = ''.join([initial_char for raw_word, clean_word, initial_char in tripples])
        first_letters_nostop = ''.join([initial_char for raw_word, clean_word,
                                        initial_char in tripples if clean_word.lower() not in STOPWORDS])
        first_caps = ''.join(c for c in first_letters if c == c.upper())
        return first_letters, first_letters_nostop, first_caps
    else:
        return list(possible_acronyms(s, titlize=False)) + list(possible_acronyms(s.title(), titlize=False))


def glossary_entry(glossary, term, start_entry_num=2):
    if term in glossary:
        k = start_entry_num
        while f'term ({k})' in glossary:
            k += 1
        return f'term ({k})'
    return term


def load(domains=('dsdh',)):
    """ Load yaml file, use hashtags to create context tags as multihot columns

    Parses acronyms in parentheses and adds them as additional `{acronym: term}` glossary entries.

    >>> g = load(domains='dsdh'.split(','))
    >>> len(g['raw']) <= len(g['cleaned']) > 30
    True
    >>> sorted(g['cleaned']['Allele'])
    ['acronym', 'definition', 'hashtags', 'parenthetical']
    >>>
    """
    glossary_raw = {}
    for domain in tqdm(domains):
        glossary_raw.update(yaml.load(open(os.path.join(DATA_DIR, 'faq', f'glossary-{domain}.yml'))))
    glossary = {}
    for term_raw, definition_raw in glossary_raw.items():
        match = re.match(r'(?P<term>[^(]*)\s*(\((?P<parenthetical>[^)]*)\))?\s*$', term_raw)
        gd = match.groupdict()
        term = (gd['term'] or '').strip()
        paren = (gd['parenthetical'] or '').strip()
        term_acros = possible_acronyms(term)
        paren_acros = possible_acronyms(paren)
        acro = ''
        if len(paren) >= len(term) * 1.2:
            if term in paren_acros:
                term, acro, paren = paren, term, None
        elif len(paren) < len(term):
            if paren in term_acros or ((len(paren) > 1) and paren == paren.upper()):
                term, acro, paren = term, paren, None
        hashtag_dict = find_hashtags(definition_raw)
        if not term:
            continue
        term_entry = glossary_entry(glossary, term)
        glossary[term_entry] = {
            'definition': hashtag_dict['cleaned'],
            'hashtags': hashtag_dict['hashtags']}
        glossary[term_entry]['acronym'] = acro
        glossary[term_entry]['parenthetical'] = paren
        if acro:
            acro_entry = glossary_entry(glossary, acro)
            glossary[acro_entry] = {
                'definition': term_entry,
                'hashtags': hashtag_dict['hashtags']}
            glossary[term_entry]['acronym'] = ''
        glossary[term_entry]['parenthetical'] = paren

    return {'raw': glossary_raw, 'cleaned': glossary}
    #     if match:
    #         acronyms.append(match.groups())
    #     else:
    #         acronyms.append((None, None))
    # acronyms = pd.DataFrame(acronyms, columns='acronym acronym_expanded'.split())
    # cleaned_hashtags = [find_hashtags(s) for s in df['definition']]
    # cleaned_hashtags = pd.DataFrame(cleaned_hashtags)
    # return pd.concat([acronyms, df, cleaned_hashtags], axis=1)


# def parse_sentences(title, sentences, title_depths, see_also=True, exclude_headings=(), d=0, depth=0, max_depth=3):

#     return sentences, title_depths
