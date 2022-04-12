#!/usr/bin/env python
import requests as r
from functools import cached_property
from urllib.parse import urljoin
from bs4 import BeautifulSoup as BS
from bs4.element import Tag

from iso_codes import country_codes, lang_codes


class Maserati:

    MASERATI_URL_FMT = "https://www.maserati.com/{country_code}/{lang_code}/"

    def __init__(self, country="Canada", lang="English"):
        self.base_url = self.MASERATI_URL_FMT.format(
            country_code=country_codes()[country].lower(),
            lang_code=lang_codes()[lang].lower(),
        )


    def get(self, path):
        resp = r.get(urljoin(self.base_url, path))
        resp.raise_for_status()
        return BS(resp.content, "html.parser")

    def _node_name(self, node):
        name = node.name

        for attr in ["class", "id"]:
            if val := node.attrs.get(attr):
                if isinstance(val, list):
                    name = val[0]
                else:
                    name = val
        return name

    def _merge_dict(self, dest, src):
        for k, v in src.items():
            if k not in dest:
                dest[k] = v
            else:
                if isinstance(dest[k], dict):
                    if not isinstance(v, dict):
                        raise Exception("type miss match for merging {type(dest) != {type(src)}}")
                    self._merge_dict(dest[k], v)
                elif isinstance(dest[k], list):
                    if isinstance(v, list):
                        dest[k].extend(v)
                    else:
                        dest[k].append(v)
                else:
                    dest[k] = [dest[k], v]
                data.update(cinfo)


    def _extract_info(self, node):
        if not isinstance(node, Tag):
            return node.text.strip()

        if node.name == "img":
            return node["src"]

        data = {"__value__": [], "__links__": {}}
        for child in  node.children:
            if cinfo := self._extract_info(child):
                if isinstance(cinfo, dict):
                    self._merge_dict(data, cinfo)
                elif isinstance(cinfo, list):
                    if isinstance(cinfo[0], tuple):
                        data["__links__"].update(dict(cinfo))
                    else:
                        data["__value__"].append(cinfo)
                elif isinstance(cinfo, tuple):
                    data["__links__"].update(dict([cinfo]))
                else:
                    data["__value__"].append(cinfo)

        for k in list(data.keys()):
            if not data[k]:
                del data[k]
            elif len(data[k]) == 1 and isinstance(data[k], list):
                data[k] = data[k][0]

        name = node.name
        if len(classes := node.get("class", [])) == 1 and (cname := classes[0]):
            name = cname

        if not data:
            return

        if len(data) == 1:
            if "__links__" in data:
                return  list(map(tuple, data["__links__"].items()))
            data = list(data.values())[0]
            if isinstance(data, tuple):
                return data

        if node.name == "a":
            return data, node.attrs.get("href")

        return {name: data}

    @cached_property
    def models(self):
        page = self.get("models")
        model_divs = page.find("div", class_="models").find_all("div", class_="model")
        return {
            (model := self._extract_info(model_div)["model"])["title"]: model
            for model_div in model_divs
        }


def main():
    from pprint import pprint

    maserati = Maserati()
    pprint(maserati.models)


if __name__ == "__main__":
    main()
