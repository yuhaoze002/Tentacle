#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import requests
import re
import json
import sys
from urllib.parse import quote
from random import choice
from bs4 import BeautifulSoup
from lib.core.settings import HEADERS
from lib.core.settings import AGENTS_LIST
from lib.core.settings import ZOOMEYS_API
from lib.core.data import logger

_Proxy = {
    'http':'http://127.0.0.1:7999',
    'https':'http://127.0.0.1:7999'
    }

def search_api(search,page = 5):
    target_list = []
    for type in ['host','web']:
        for z in _zoomeye_api(search, page, type):
            for url in z:
                target_list.append(url)
    return list(set(target_list))

def search_engine(search,page = 5):
    target_list = []
    try:
        for url in _baidu(search,page):
            target_list.append(url)

        for url in _360so(search,page):
            target_list.append(url)

        for url in _bing(search, page):
            target_list.append(url)

        for url in _google(search, page):
            target_list.append(url)
    except KeyboardInterrupt:
        sys.exit(logger.error("Exit by user."))

    return list(set(target_list))



def _baidu(search, page):
    for n in range(0, page * 10, 10):
        base_url = 'https://www.baidu.com/s?wd=' + str(quote(search)) + '&oq=' + str(
            quote(search)) + '&ie=utf-8' + '&pn=' + str(n)
        try:
            r = requests.get(base_url, headers=HEADERS)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select('div.c-container > h3 > a'):
                url = requests.get(a['href'], headers=HEADERS, timeout=5).url
                yield url
        except:
            yield None


# 360搜索
def _360so(search, page):
    for n in range(1, page + 1):
        base_url = 'https://www.so.com/s?q=' + str(quote(search)) + '&pn=' + str(n) + '&fr=so.com'
        try:
            r = requests.get(base_url, headers=HEADERS)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select('li.res-list > h3 > a'):
                url1 = requests.get(a['href'], headers=HEADERS, timeout=5)
                url = re.findall("URL='(.*?)'", url1.text)[0] if re.findall("URL='(.*?)'", url1.text) else url1.url
                yield url
        except:
            yield None


# 必应搜索
def _bing(search, page):
    for n in range(1, (page * 10) + 1, 10):
        base_url = 'http://cn.bing.com/search?q=' + str(quote(search)) + '&first=' + str(n)
        try:
            r = requests.get(base_url, headers=HEADERS)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select('li.b_algo > div.b_algoheader > a'):
                url = a['href']
                yield url
        except:
            yield None


# Google搜索
def _google(search, page):
    for n in range(0, 10 * page, 10):
        base_url = 'https://www.google.com.hk/search?safe=strict&q=' + str(quote(search)) + '&oq=' + str(
            quote(search)) + 'start=' + str(n)
        try:
            r = requests.get(base_url, headers={'User-Agent': choice(AGENTS_LIST)}, proxies=_Proxy, timeout=16)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select('div.rc > div.r > a'):
                url = a['href']
                if 'translate.google.com' not in url:
                    yield url
        except Exception as e:
            yield None

# 钟馗之眼
def _zoomeye_api(search, page, z_type):
    """
        app:"Drupal" country:"JP"
    """

    # 认证信息
    header = HEADERS
    header["Authorization"] = "JWT " + ZOOMEYS_API
    if z_type.lower() == 'web':
        url_api = "https://api.zoomeye.org/web/search"
    elif z_type.lower() == 'host':
        url_api = "https://api.zoomeye.org/host/search"
    else:
        logger.error("Error Zoomeye api with type {0}.".format(z_type))
        return None
    logger.sysinfo("Using Zoomeye api with type {0}.".format(z_type))
    for n in range(1, page + 1):
        try:
            data = {'query': search, 'page': str(n)}
            res = requests.get(url_api, params=data, headers=header)
            if int(res.status_code) == 422:
                sys.exit(logger.error("Error Zoomeye api token."))
            if z_type.lower() == 'web':
                result = re.compile('"url": "(.*?)"').findall(res.text)
            elif z_type.lower() == 'host':
                result = [str(item['ip']) + ':' + str(item['portinfo']['port']) for item in json.loads(res.text)['matches']]
            yield result
        except Exception:
            yield None


