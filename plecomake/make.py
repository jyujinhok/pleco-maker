from tqdm import tqdm
import xml.etree.ElementTree as ET
import sys
import re
import json
import itertools
import string
NEWLINE = "\uEAB1"
BOLD = "\uEAB2"
END_BOLD = "\uEAB3"
INDENT = "  "

# These should be the names used by zh-dial-syn
LECTS = ["Hong Kong", "Taishan", "Beijing"]
# Mapping from codes used by zh-pron to a human-readable name
PRONS = {"m": "Mandarin", "c": "Cantonese", "c-t": "Taishanese"}

# only generate entries that have at least one of the following two
REQUIRED_LECTS = ["Hong Kong", "Taishan"]
REQUIRED_PRONS = ["c-t"]

# Mapping between zh-dial-syn names and zh-pron codes
LECT_PRON_MAP = {"Beijing": "m", "Hong Kong": "c", "Taishan": "c-t"}

SUPERSCRIPTS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁻"
TRANSLATE_MAP = {str(num): SUPERSCRIPTS[num] for num in range(0, 10)}
TRANSLATE_MAP["-"] = "⁻"
# TRANSLATE = string.maketrans(TRANSLATE_MAP)


def superscriptify(s):
    return s.translate(s.maketrans(TRANSLATE_MAP))

# Wiktionary handles sandhi for 不 and 一 by directly sticking them in the pronunciations
# We don't care about this, we want citation tones
def mandarin_sandhi_remove(s):
    return s.replace("不", "bù").replace("一", "yī")

def clean_prons(prons):
    prons = [mandarin_sandhi_remove(superscriptify(p)) for p in prons.split(",") if "=" not in p]
    return ", ".join(prons)
# get the pronunciation list for synonym syn, with synonym head syn_head
# etymology_number can be None if unknown
def get_syn_pron(syn, syn_head, etymology_number, articledata):
    if syn not in articledata:
        return None
    article = articledata[syn]
    etym = None
    if etymology_number and etymology_number in article:
        etym = article[etymology_number]
    else:
        for e in article:
            a_e = article[e]
            if "dial" in a_e and (syn_head in a_e["dial"] or "self" in a_e["dial"]):
                etym = a_e
    if not etym:
        return None
    return etym.get("pron")


def display_syns(lect, syn_list, syn_head, articledata):
    all_cleaned = []
    for syn in syn_list:
        # : used for further specifying the type of synonym
        split = syn.split(":")
        # _ used for etymology numbers
        undersplit = split[0].split("_")
        cleaned = undersplit[0]
        etymology_number = None
        if len(undersplit) > 1:
            etymology_number = undersplit[1]

        pron = get_syn_pron(cleaned, syn_head, etymology_number, articledata)
        relevant_pron = None
        if pron:
            relevant_pron = pron.get(LECT_PRON_MAP[lect])
        if relevant_pron:
            cleaned += f" ({clean_prons(relevant_pron)})"
        if len(split) > 1:
            cleaned += f" [{split[1]}]"
        all_cleaned += [cleaned]

    if len(all_cleaned) == 1:
        return all_cleaned[0]
    else:
        return f"{NEWLINE}{INDENT}{INDENT}" + f"{NEWLINE}{INDENT}{INDENT}".join(all_cleaned)
    return ", ".join(all_cleaned)

def line_for_article(article_name, etym, dial_map, articledata):
    pron = etym.get("pron")
    dials = etym.get("dial")
    if not dials:
        dials = []
    line = None
    if not pron:
        return
    headpron = ""

    found_requirements = False
    for p in REQUIRED_PRONS:
        if p in pron:
            found_requirements = True

    if "m" in pron:
        headpron = mandarin_sandhi_remove(pron["m"].split(',')[0])
    elif "c" in pron:
        headpron = pron["c"].split(",")[0]
        headpron = "{" + headpron + "}"
    else:
        for p in PRONS:
            if p in pron:
                break
        else:
            # No pronunciation for lects we care about
            return None

    line = f"[{article_name}]\t{headpron}\t"
    line += f"{BOLD}Pronunciation:{END_BOLD}{NEWLINE}"
    for p in PRONS:
        if p in pron:
            cleaned = clean_prons(pron[p])
            line += f"{INDENT}{PRONS[p]}: {cleaned} {NEWLINE}"

    for dial in dials:
        iter_requirements = False
        syn_head = dial
        if syn_head == "self":
            syn_head = article_name
        dial_entry = dial_map[syn_head]
        for lect in REQUIRED_LECTS:
            if lect in dial_entry["dials"]:
                lect_entry = dial_entry["dials"][lect]
                # Always include map for synonym roots
                if syn_head == article_name:
                    # but not if the synonym doesn't actually exist for a required lect
                    if lect_entry != [syn_head]:
                        iter_requirements = True
                # for non-root entries, make sure this article actually shows up somewhere for this lect
                elif any(article_name in x for x in lect_entry):
                        iter_requirements = True
        for lect in LECTS:
            if lect in dial_entry["dials"]:
                break
        else:
            continue

        # Only show relevant dialectical info
        if not iter_requirements:
            continue
        found_requirements = True

        line += f"{NEWLINE} {NEWLINE}{BOLD}Dialectical synonyms of {syn_head.split('-')[0]}{END_BOLD} ({dial_entry['meaning']}): {NEWLINE}"
        for lect in LECTS:
            if lect in dial_entry["dials"]:
                syns = display_syns(lect, dial_entry['dials'][lect], syn_head, articledata)
                line += f"{INDENT}{lect}: {syns}{NEWLINE}"
    if not found_requirements:
        return None

    return line

print("Loading dialect data...")
dial_map = json.load(open("dial.json", "r"))
print("Loading article data...")
articledata = json.load(open("articledata.json", "r"))

outfile = open("dict.csv", "w")

iterator = tqdm(articledata)
# iterator = itertools.islice(tqdm(articledata), 30)
for article_name in iterator:
    article = articledata[article_name]
    # if article_name != "一點":
    #     continue
    for etym_number in article:
        etym = article[etym_number]
        line = line_for_article(article_name, etym, dial_map, articledata)
        if line:
            outfile.write(line)
            outfile.write("\n")
