#!/usr/bin/env python

import re
from functools import cache
from bs4 import BeautifulSoup as BS
import requests as r



def parse_table_rows(row):
    vals = row.find_all("th")
    if not vals:
        vals = row.find_all("td")
    return [v.text.strip() for v in vals]


def parse_table(table):
    rows = table.find("tbody").find_all("tr")
    return list(map(parse_table_rows, rows))


def table_name(table):
    if caption := table.find("caption"):
        return caption.text.strip()

    header_pattern = re.compile(r"^h\d+$")
    above_elem = table
    while above_elem:
        if above_elem.name and header_pattern.match(above_elem.name):
            return above_elem.text.replace("[edit]", "").strip()

        above_elem = above_elem.previous_sibling or above_elem.parent

    return None


def extract_tables(page):
    tables = {"__anon__": []}
    for table in page.find_all("table", {"class": "wikitable"}):
        name = "__anon__"
        if tname := table_name(table):
            name = tname
        tables[name] = parse_table(table)

    return tables


def table_to_dicts(table):
    if not table:
        return []

    headers = table[0]
    return [dict(zip(headers, row)) for row in table[1:]]

def parse_wiki_tables(page):
    return {
        name: table_to_dicts(table)
        for name, table in extract_tables(page).items()
    }


def tables_from_url(url):
    resp = r.get(url)
    resp.raise_for_status()
    page = BS(resp.content, "html.parser")

    return parse_wiki_tables(page)

@cache
def country_codes():
    source_url = "https://en.wikipedia.org/wiki/ISO_3166-1"

    table_name = "ISO 3166-1 table"
    name_col = "English short name (using title case)"
    code_col = "Alpha-2 code"

    table_dicts = tables_from_url(source_url)[table_name]
    return {
        data[name_col]: data[code_col]
        for data in table_dicts
    }


@cache
def lang_codes():
    source_url = "https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes"

    table_name = "List of ISO 639-1 codes"
    name_col = "ISO language name"
    code_col = "639-1"

    tables = tables_from_url(source_url)
    table_dicts = tables[table_name]
    return {
        data[name_col]: data[code_col]
        for data in table_dicts
    }


def main():
    from pprint import pprint
    pprint(lang_codes())
    pprint(country_codes())


if __name__ == "__main__":
    main()
