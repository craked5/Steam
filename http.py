#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'nunosilva, github.com/craked5'

import os
import socket
import random
import requests as req
import ast
import ujson
import time
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from http_util import Httpdata

class SteamBotHttp:

    def __init__(self,wte,sma,sessionid,sls,sl,srl,password,username):
        self.httputil = Httpdata(wte,sma,sessionid,sls,sl,srl,password,username)
        self.down_state = 0
        self.host = 'steamcommunity.com'
        self.pre_host_normal = 'http://'
        self.pre_host_https = 'https://'
        self.market = '/market'
        self.mylistings = '/mylistings/'
        #currency=3/2003 == euro
        self.item_price_viewer = '/priceoverview/?currency=3&appid=730&market_hash_name='
        self.recent_listed = '/recent/?country=PT&language=english&currency=3'

        #TESTE RECENT_LISTED -APAGAR DEPOIS
        self.recent_listed_countrys1 = '/recent/?country='
        self.recent_listed_countrys2 = '&language=english&currency=3'

        self.complete_url_item = self.pre_host_normal+self.host+self.market+self.item_price_viewer
        self.complete_url_recent = self.pre_host_normal+self.host+self.market+self.recent_listed
        self.sell_item_url = self.pre_host_https+self.host+self.market+'/sellitem/'
        self.render_item_url_first_part = self.pre_host_normal+self.host+self.market+'/listings/730/'
        self.render_item_url_sencond_part = '/render/?currency=3'
        self.recent_compare = {}

    def login(self):

        donotcache = self.now_milliseconds()

        self.httputil.rsa_data['donotcache'] = donotcache
        self.httputil.login_data['donotcache'] = donotcache

        temp_rsa = req.post('https://steamcommunity.com/login/getrsakey/', headers=self.httputil.rsa_headers,
                            data=self.httputil.rsa_data)
        print temp_rsa.content
        print 'O status code do GETRSA foi ' + str(temp_rsa.status_code)

        temp_ras_good = ujson.loads(temp_rsa.content)
        self.httputil.login_data['rsatimestamp'] = temp_ras_good['timestamp']
        mod = long(temp_ras_good['publickey_mod'], 16)
        exp = long(temp_ras_good['publickey_exp'], 16)
        rsa_key = RSA.construct((mod, exp))
        rsa = PKCS1_v1_5.PKCS115_Cipher(rsa_key)
        encrypted_password = rsa.encrypt(self.httputil.password)
        encrypted_password = base64.b64encode(encrypted_password)
        self.httputil.login_data['password'] = encrypted_password

        temp_dologin = req.post('https://steamcommunity.com/login/dologin/', headers=self.httputil.rsa_headers,
                                data=self.httputil.login_data)
        print temp_dologin.content
        print 'O status code do DOLOGIN foi ' + str(temp_dologin.status_code)

        temp_dologin_good = ujson.loads(temp_dologin.content)
        self.httputil.transfer_data['steamid'] = temp_dologin_good['transfer_parameters']['steamid']
        self.httputil.transfer_data['token'] = temp_dologin_good['transfer_parameters']['token']
        self.httputil.transfer_data['auth'] = temp_dologin_good['transfer_parameters']['auth']
        self.httputil.transfer_data['remember_login'] = temp_dologin_good['transfer_parameters']['remember_login']
        self.httputil.transfer_data['token_secure'] = temp_dologin_good['transfer_parameters']['token_secure']

        temp_transfer = req.post('https://store.steampowered.com/login/transfer', headers=self.httputil.transfer_headers
                                 ,data=self.httputil.transfer_data)
        print 'O status code do LOGINTRANSFER foi ' + str(temp_transfer.status_code)

    def logout(self):
        temp_logout = req.post('https://steamcommunity.com/login/logout/', headers= self.httputil.headers_logout,
                               data= self.httputil.logout_data)
        print 'O status code do LOGOUT FOR ' + str(temp_logout.status_code)


    def now_milliseconds(self):
        self.donotcache = int(time.time() * 1000)

    def querypriceoverview(self,item):
        try:
            steam_response = req.get(self.complete_url_item + item, headers=self.httputil.headers_item_priceoverview,timeout=15)
            if steam_response.status_code == 200:
                try:
                    item_temp_str_no_uni = steam_response.content.decode('unicode_escape').encode('ascii','ignore')
                    item_temp = ujson.loads(item_temp_str_no_uni)
                except ValueError:
                    return steam_response.status_code, steam_response.content
                return item_temp
            else:
                return steam_response.status_code
        except req.Timeout:
            return False

    def queryrecent(self,host,thread):
        try:

            steam_response = req.get(self.complete_url_recent.replace(self.host,host),
                                     headers=self.httputil.headers_recent,timeout=15)

            if steam_response.status_code == 200:
                print 'Status code: ' + str(steam_response.status_code) + ' na thread ' + str(thread)
                timestamp = time.time()
                time_temp = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp))
                self.httputil.headers_recent['If-Modified-Since'] = time_temp
                try:
                    recent_temp = ujson.loads(steam_response.text)
                except ValueError:
                    return False
                return recent_temp

            elif steam_response.status_code == 304:
                print 'Status code: ' + str(steam_response.status_code) + ' na thread ' + str(thread)
                return -1

        except req.ConnectionError:
            return False
        except req.Timeout:
            return -2

        return False

    def urlqueryrecentwithcountry(self,host,country,thread):
        try:

            steam_response = req.get(self.pre_host_normal+host+self.market+self.recent_listed_countrys1+country+
                                     self.recent_listed_countrys2,
                                     headers=self.httputil.headers_recent,timeout=15)

            if steam_response.status_code == 200:
                print 'Status code: ' + str(steam_response.status_code) + ' na thread ' + str(thread) + ' e country code' \
                                                                                                        ': ' + country
                timestamp = time.time()
                time_temp = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp))
                self.httputil.headers_recent['If-Modified-Since'] = time_temp
                try:
                    recent_temp = ujson.loads(steam_response.text)
                except ValueError:
                    return False
                return recent_temp

            elif steam_response.status_code == 304:
                print 'Status code: ' + str(steam_response.status_code) + ' na thread ' + str(thread) + ' e country code' \
                                                                                                        ': ' + country
                return -1

        except req.ConnectionError:
            tempfile = open('util/fail_ip.txt', 'a')
            tempfile.write('A thread ' + str(thread) +' falhou no ip '+ str(host) +'\n')
            tempfile.flush()
            os.fsync(tempfile.fileno())
            tempfile.close()
            return False
        except req.Timeout:
            tempfile = open('util/fail_ip.txt', 'a')
            tempfile.write('A thread ' + str(thread) +' falhou no ip '+ str(host) +'\n')
            tempfile.flush()
            os.fsync(tempfile.fileno())
            tempfile.close()
            return -2
        except socket.timeout:
            tempfile = open('util/fail_ip.txt', 'a')
            tempfile.write('A thread ' + str(thread) +' falhou no ip '+ str(host) +'\n')
            tempfile.flush()
            os.fsync(tempfile.fileno())
            tempfile.close()
            return -2

        return False
    def urlqueryspecificitemind(self,host,item,language):

        try:
            steam_response = req.get(self.render_item_url_first_part.replace(self.host,host)+item+
                                     self.render_item_url_sencond_part+'&language='+language,
                                     headers = self.httputil.headers_item_list_ind)
            timestamp = time.time()
            time_temp = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp))
            self.httputil.headers_item_list_ind['If-Modified-Since'] = time_temp
        except req.ConnectionError:
            return False

        except req.Timeout, req.ReadTimeout:
            print "shit i got a timeout"
            return False

        if steam_response.status_code == 429:
            print 'GOT 429 on host ' + str(host)
            return False
        else:
            try:
                recent_temp = ujson.loads(steam_response.text)
            except ValueError:
                return False
        print str(host)
        return recent_temp

    def getpositiononeiteminv(self):

        temp_inv = req.get('http://steamcommunity.com/id/craked5/inventory/json/730/2/')
        array = ujson.loads(temp_inv.content)

        for key in array['rgInventory']:
            if array['rgInventory'][key]['pos'] == 1:
                temp_id = array['rgInventory'][key]['id']
                return temp_id

        return False

    #price = ao preco que eu quero receber
    #price vem em float
    def sellitem(self,assetid,price):

        list_return = []
        price_temp = price * 100
        price_temp = round(price_temp)

        self.httputil.data_sell['assetid'] = int(assetid)
        self.httputil.data_sell['price'] = int(price_temp)

        temp = req.post(self.sell_item_url, data=self.httputil.data_sell, headers=self.httputil.headers_sell)

        list_return.append(temp.status_code)
        list_return.append(temp.content)
        list_return.append(int(price_temp))

        return list_return

    def buyitem(self,listing,subtotal,fee,currency,host):

        temp_tuple = []

        self.httputil.data_buy['currency'] = int(currency) - 2000
        self.httputil.data_buy['subtotal'] = int(subtotal)
        self.httputil.data_buy['fee'] = int(fee)
        self.httputil.data_buy['total'] = int(self.httputil.data_buy['subtotal'] + self.httputil.data_buy['fee'])
        try:
            temp = req.post(self.pre_host_https+host+self.market+'/buylisting/'+listing, data=self.httputil.data_buy,
                            headers=self.httputil.headers_buy, verify=False)
        except req.ConnectionError:
            temp_tuple.append(False)

        temp_tuple.append(int(temp.status_code))
        try:
            temp_tuple.append(ast.literal_eval(temp.content))
        except SyntaxError:
            temp_tuple.append(False)

        return temp_tuple

    def buyitemTEST(self,listing,subtotal,fee,currency,host):

        temp_tuple = []

        self.httputil.data_buy['currency'] = int(currency) - 2000
        self.httputil.data_buy['subtotal'] = int(subtotal)
        self.httputil.data_buy['fee'] = int(fee)
        self.httputil.data_buy['total'] = int(self.httputil.data_buy['subtotal'] + self.httputil.data_buy['fee'])
        urll = 'https://'+str(host)+'/market/buylisting/'+listing
        print urll
        temp = req.post(urll, data=self.httputil.data_buy,
                        headers=self.httputil.headers_buy,verify=False)

        temp_tuple.append(int(temp.status_code))
        temp_tuple.append(ast.literal_eval(temp.content))

        return temp_tuple

    def getsteamwalletsite(self):
        temp = req.get('http://steamcommunity.com/market/',headers=self.httputil.headers_wallet)
        if temp.status_code == 200:
            return temp.content
        else:
            return False

    def getmyactivelistingsraw(self):
        my_listings = req.get(self.pre_host_normal+'steamcommunity.com'+self.market+self.mylistings,
                              headers=self.httputil.headers_active_listings)
        if my_listings.status_code == 200:
            my_listings_dict = ujson.loads(my_listings.content)
            return my_listings_dict
        else:
            return False

#-----------------------------------------AUX FUNCTIONS------------------------------------------------------------------

    def queryitemtest(self,item):

        steam_response = req.get(self.render_item_url_first_part+item,headers = self.httputil.headers_item_list_ind)

        print steam_response.status_code
        print steam_response.url

        return steam_response.content