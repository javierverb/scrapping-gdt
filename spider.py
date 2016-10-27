# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import json
import mechanize
import os
import re


class Stats(object):
    """
    This object was place inside of a Player
    """

    def __init__(self):
        super(Stats, self).__init__()
        # stats
        self.strength = ""
        self.health = ""
        self.agility = ""
        self.protection = ""
        self.mana = ""


class Player(object):
    """docstring for Player"""

    def __init__(self, stats=None, image=None):
        super(Player, self).__init__()
        self.id = ""
        self.name = ""
        self.rank = ""
        self.url = ""
        self.stats = stats
        self.image = image

    def set_id(self, id):
        self.id = id

    def set_rank(self, rank):
        self.rank = rank

    def set_url(self, url):
        self.url = url

    def set_name(self, name):
        self.name = name

    def set_stats(self, stats_obj):
        self.stats = stats_obj


class ScrapperTitanWars(object):
    """docstring for ScrapperTitanWars"""

    def __init__(self):
        super(ScrapperTitanWars, self).__init__()
        self._url_root = "http://guerradetitanes.net"
        self.__instance_browser(self)
        self.invalid_players = {}
        self.players = {}

    @staticmethod
    def __instance_browser(self):
        browser = mechanize.Browser()
        browser.set_handle_robots(False)
        browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; \
                                    en-US; rv:1.9.0.1) Gecko/2008071615 \
                                    Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        self.browser = browser

    def sign_in(self, username, password):
        url_login = self._url_root + "?sign_in=1"
        self.browser.open(url_login)
        self.browser.select_form(nr=0)
        form = [f for f in self.browser.forms()][0]
        form.new_control("text", "login", {"value": ""})
        form.fixup()

        # Logueo
        self.browser.form["login"] = username
        self.browser.form["pass"] = password
        resp = self.browser.submit().read()

        content_html = BeautifulSoup(resp, 'html.parser')

        has_error = content_html.find('div', {'class': 'error'})
        if has_error:
            print has_error.text
            exit(1)
        else:
            print 'Login complete'

    def dump_all_data(self, f=None):
        d = {}
        for k in self.players:
            d[k] = self.players[k].__dict__
        for k in d:
            d[k]['stats'] = d[k]['stats'].__dict__
        json_data = json.dumps(
            d,
            sort_keys=True,
            indent=2,
            separators=(',', ': ')
        )
        if f:
            f.write(json_data)
            f.close()
        else:
            print json_data

    def __clean_invalid_players(self):
        for k in self.invalid_players:
            self.players.pop(k)
        self.invalid_players = {}

    def hydrate_ranking(self, page):
        """ Carga una colección de jugadores con el ranking, id y url
        """
        def __get_player_id(h):
            return h.replace('/user/', '').replace('/', '') if h else None

        url = self._url_root + "/rating/sumstat/{}".format(page)
        self.browser.open(url)
        resp = self.browser.response().read()
        content_html = BeautifulSoup(resp, 'html.parser')
        content_html = content_html.find_all('div', {'class': 'block_zero'})
        for i, div in enumerate(content_html):
            rank = div.find('span').get_text() if div.find('span') else None
            name = div.find('a', href=True).string if div.find('a') else None
            href = div.find('a', href=True)['href'] if div.find('a') else None

            if name == "Guerrero":
                continue
            player_id = __get_player_id(href)

            p = Player()
            p.set_id(player_id)
            p.set_rank(rank)
            p.set_url(href)
            p.set_name(name)
            self.players.update({player_id: p})

    def hydrate_player_stats(self):
        """ Dada una colección de jugadores, instancia sus stats
            Notar que si el jugador es inválido, lo descarta
        """
        def __get_value(exp):
            try:
                res = re.findall(r'\d+', exp).pop()
            except:
                res = None
            return res

        for k in self.players:
            p = self.players[k]

            try:
                int(p.id)
                self.browser.open(self._url_root + p.url)
            except:
                print 'This is an invalid player: {} so will be mark to invalid'.format(p.name)
                self.invalid_players[k] = p
                continue

            resp = self.browser.response().read()
            content_html = BeautifulSoup(resp, 'html.parser')
            stats_container = content_html.find('div', {'class': 'block_zero'})
            s = Stats()
            s.strength = __get_value(stats_container.find(text=re.compile(u'Fuerza: ')))
            s.agility = __get_value(stats_container.find(text=re.compile(u'Agilidad: ')))
            s.health = __get_value(stats_container.find(text=re.compile(u'Salud: ')))
            s.protection = __get_value(stats_container.find(text=re.compile(u'Protección: ')))
            s.mana = __get_value(stats_container.find(text=re.compile(u'Energía: ')))

            p.set_stats(s)

        self.__clean_invalid_players()

    def hydrate_player_image(self):
        """
        PRE: las urls deben ser válidas
        """
        for k in self.players:
            p = self.players[k]
            self.browser.open(self._url_root + p.url)
            resp = self.browser.response().read()
            content_html = BeautifulSoup(resp, 'html.parser')
            link_container = content_html.find_all('div', {'class': 'float-left'})[0]
            link = link_container.find('a')['href']
            self.browser.open(self._url_root + link)
            resp = self.browser.response().read()
            content_html = BeautifulSoup(resp, 'html.parser')
            img_container = content_html.find_all('div', {'class': 'block_zero center'})[1]
            img_src = img_container.find('img')['src']
            p.image = img_src


spider = ScrapperTitanWars()
spider.sign_in("javierverb", "iseedeadpe12")

for page in xrange(80):
    spider.hydrate_ranking(page)
spider.hydrate_player_stats()
spider.hydrate_player_image()
f = open('d', 'w+')
spider.dump_all_data(f)
