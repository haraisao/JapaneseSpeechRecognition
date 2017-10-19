#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, socket, subprocess, signal, threading, platform
import time, struct, traceback, locale, codecs, getopt, wave, tempfile
import optparse

import json
import urllib
import urllib2

#
#  
#
class GoogleSpeech():
    #
    #  Constructor
    #
    def __init__(self, language='ja-JP'):
        self._endpoint = 'http://www.google.com/speech-api/v2/recognize'
        self._lang=language
        self._apikey = ''

    #
    #  Set ApiKey
    #
    def set_apikey(self, key):
        self._apikey = key

    #
    #  Set Lang
    #  (ja-JP, en-US, en-GB, en-AU, de-DE, ....)
    #
    def set_lang(self, lang):
        self._lang = lang

    #
    #  Request Google Voice Recognition
    #
    def request_google(self, data):
        query_string = {'output': 'json', 'lang': self._lang, 'key': self._apikey}
        url = '{0}?{1}'.format(self._endpoint, urllib.urlencode(query_string)) 

        headers = {'Content-Type': 'audio/l16; rate=16000'}
        voice_data = str(bytearray(data))

        try:
            request = urllib2.Request(url, data=voice_data, headers=headers)
            result = urllib2.urlopen(request)
            response = result.read()
            #print response
            return response.decode('utf-8').split()
        except:
            print url
            print traceback.format_exc()
            return ["Error"]

def getWavData(fname):
    try:
        f = wave.open(fname)
        data = f.readframes(f.getnframes())
        f.close()
        return data
    except:
        return ""


def show_result(result):
    try:
      result.pop(0)
      res = json.loads(''.join(result))
      i=0
      for x in res['result'][0]['alternative'] :
        i += 1
        if 'confidence' in x :
            
            print "#"+str(i)+":"+x['transcript']+"("+str(x['confidence'])+")"
        else :
            print "#"+str(i)+":"+x['transcript']
    except:
      print "---"


def main(key):
  import glob
  rec = GoogleSpeech()
  rec.set_apikey(key)

  files = glob.glob('log/*.wav')
  files.sort()

  for f in files:
    print f
    data = getWavData(f)
    result=rec.request_google(data)
    show_result(result)
    print ""

#
#  Main
#
if __name__ == '__main__':
  key = <Your API-KEY>
  rec = GoogleSpeech()
  rec.set_apikey(key)
  f=sys.argv[1]

  print f
  data = getWavData(f)
  result=rec.request_google(data)
  show_result(result)



