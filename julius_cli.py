#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, socket, subprocess, signal, threading, platform
import time, struct, traceback, locale, codecs, getopt, wave, tempfile
import optparse

import json
import urllib
import urllib2

import glob

#
#  
#
class JuliusCli():
    #
    #  Constructor
    #
    def __init__(self, host="localhost", port=10000):
        self.setServer(host, port)
        self._lang = "jaJP"
        self._apikey=""

    #
    #  Set JuliusServer
    #
    def setServer(self, host, port):
        self._host = host
        self._port = port
        self._endpoint = "http://%s:%d/asr" % (self._host, self._port)


    #
    #  Request  Voice Recognition
    #
    def request_asr(self, data):
        query_string = {'output': 'json', 'lang': self._lang, 'key': self._apikey}
        url = '{0}?{1}'.format(self._endpoint, urllib.urlencode(query_string)) 

        headers = {'Content-Type': 'audio/l16; rate=16000'}
        voice_data = str(bytearray(data))

        try:
            request = urllib2.Request(url, data=voice_data, headers=headers)
            result = urllib2.urlopen(request)
            response = result.read()
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
      res = json.loads(result)
      i=0

      for x in res['result'] :
        i += 1
        if 'confidence' in x :
            print "#"+str(i)+":"+x['str']+"("+str(x['confidence'])+")"
        else :
            print "#"+str(i)+":"+x['str']

    except:
      print result
      pass
    print "\n"

def main():
  rec = JuliusCli()

  files = glob.glob('log/*.wav')
  files.sort()

  for f in files:
    print f
    data = getWavData(f)
    result=rec.request_asr(data)
    show_result(''.join(result) )
    print "\n"

#
#  Main
#
if __name__ == '__main__':
  req = JuliusCli('hara.jpn.com')

  data = getWavData(sys.argv[1])
  result=req.request_asr(data)

  show_result( ''.join(result) )


