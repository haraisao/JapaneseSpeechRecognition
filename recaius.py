#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import time,wave
import math
import json
import urllib
import urllib2
import cookielib

import base64



class RecaiusAuth():
  def __init__(self, service_id, passwd):
     self._baseAuthUrl="https://api.recaius.jp/auth/v2/"
     self._service_id=service_id
     self._passwd=passwd
     self._token = ''

     opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=0),
                             urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
     urllib2.install_opener(opener)

  #-------- Recaius Authorization
  def requestAuthToken(self, srv):
     url = self._baseAuthUrl+'tokens'
     headers = {'Content-Type' : 'application/json' }
     data = { srv : { "service_id" : self._service_id, "password" : self._passwd} }

     request = urllib2.Request(url, data=json.dumps(data), headers=headers)
     try:
       result = urllib2.urlopen(request)
     except urllib2.HTTPError as e:
       print 'Error code:', e.code
       return False
     except urllib2.URLError as e:
       print 'URLErroe reason:', e.reason
       return False
     else:
       response = result.read()
       res = response.decode('utf-8')
       data=json.loads(res)
       self._token=data['token']
       return True
  #
  #
  def refreshAuthToken(self,srv):
     url = self._baseAuthUrl+'tokens'
     headers = {'Content-Type' : 'application/json', 'X-Token' : self._token }
     data = { srv : { "service_id" : self._service_id, "password" : self._passwd} }

     request = urllib2.Request(url, data=json.dumps(data), headers=headers)
     request.get_method = lambda : 'PUT'
     try:
       result = urllib2.urlopen(request)
     except urllib2.HTTPError as e:
       print 'Error code:', e.code
       return -1
     except urllib2.URLError as e:
       print 'URLErroe reason:', e.reason
       return -1
     else:
       response = result.read()
       res = response.decode('utf-8')
       return res

  #
  #
  def checkAuthToken(self):
     query_string = {'service_name' : 'speech_recog_jaJP'}
     url = '{0}?{1}'.format(self._baseAuthUrl+'tokens', urllib.urlencode(query_string))
     headers = {'Content-Type' : 'application/json', 'X-Token' : self._token }

     request = urllib2.Request(url, headers=headers)
     try:
       result = urllib2.urlopen(request)
     except urllib2.HTTPError as e:
       print 'Error code:', e.code
       return -1
     except urllib2.URLError as e:
       print 'URLErroe reason:', e.reason
       return -1
     else:
       response = result.read()
       res = response.decode('utf-8')
       data=json.loads(res)
       return data['remaining_sec']

#
#
#
class RecaiusAsr():
  def __init__(self, service_id, passwd):
     self._baseAsrUrl="https://api.recaius.jp/asr/v2/"
     self._service_id=service_id
     self._passwd=passwd
     self._auth=RecaiusAuth(service_id, passwd)
     self._token = ''
     self._uuid = ''
     self._vid=1
     self._silence = getWavData("silence.wav")
     self._boundary = "----Boundary"

     opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=0),
                             urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
     urllib2.install_opener(opener)

  #-------- Recaius Authorization
  def requestAuthToken(self):
     res = self._auth.requestAuthToken("speech_recog_jaJP")
     if res :
        self._token = self._auth._token
     return res

  def refreshAuthToken(self):
     return self._auth.refreshAuthToken("speech_recog_jaJP")

    
  def checkAuthToken(self):
     return self._auth.checkAuthToken()

  #-------- Voice Recognition
  def startVoiceRecogSession(self):
     url = self._baseAsrUrl+'voices'
     headers = {'Content-Type' : 'application/json', 'X-Token' : self._token }

     data = { "audio_type": "audio/x-linear",
              "result_type": "nbest",
              "push_to_talk": True,
              "model_id": 1,
              "comment": "Start" }

     request = urllib2.Request(url, data=json.dumps(data), headers=headers)
     try:
       result = urllib2.urlopen(request)
     except urllib2.HTTPError as e:
       print 'Error code:', e.code
       print 'Reason:', e.reason
       return False
     except urllib2.URLError as e:
       print 'URLErroe reason:', e.reason
       return False
     else:
       response = result.read()
       res = response.decode('utf-8')
       data=json.loads(res)
       self._uuid = data['uuid']
       self._boundary = "----Boundary"+base64.b64encode(self._uuid)
       return True

  def endVoiceRecogSession(self):
     url = self._baseAsrUrl+'voices/'+self._uuid
     headers = {'X-Token' : self._token }

     request = urllib2.Request(url, headers=headers)
     request.get_method = lambda : 'DELETE'
     try:
       result = urllib2.urlopen(request)
     except urllib2.HTTPError as e:
       print 'Error code:', e.code
       print 'Reason:', e.reason
       return False
     except urllib2.URLError as e:
       print 'URLErroe reason:', e.reason
       return False
     else:
       response = result.read()
       res = response.decode('utf-8')
       if res : print res
       return True

  def getVoiceRecogResult(self, data):
      data = self._silence+data
      data += self._silence+self._silence
      #voice_data = divString(data, 16364)
      voice_data = divString(data, 10240)
      self._vid=0

      for d in voice_data:
        self._vid += 1
        res = self.sendSpeechData(self._vid, d)
        if res :
          data=json.loads(res)

          if data[0]['type'] == 'RESULT' :
             return res
      return self.flushVoiceRecogResult()

  def sendSpeechData(self, vid, data):
     url = self._baseAsrUrl+'voices/'+self._uuid
     headers = {'Content-Type' : 'multipart/form-data','X-Token' : self._token }

     form_data = self._boundary+"\r\n"
     form_data += "Content-Disposition: form-data;name=\"voice_id\"\r\n\r\n"
     form_data += str(vid)+"\r\n"
     form_data += self._boundary+"\r\n"
     form_data += "Content-Disposition: form-data;name=\"voice\"\r\n"
     form_data += "Content-Type: application/octet-stream\r\n\r\n"
     form_data += data
     form_data += "\r\n"
     form_data += self._boundary+"\r\n"

     request = urllib2.Request(url)
     request.add_header( 'X-Token', self._token )
     request.add_header( 'Content-Type', 'multipart/form-data')
     request.add_data(bytearray(form_data))

     request.get_method = lambda : 'PUT'

     try:
       result = urllib2.urlopen(request)
     except urllib2.HTTPError as e:
       print 'Error code:', e.code
       print 'Reason:', e.reason
       return False
     except urllib2.URLError as e:
       print 'URLErroe reason:', e.reason
       return False
     else:
       response = result.read()
       res = response.decode('utf-8')
       if res :
         return res
       return False

  def flushVoiceRecogResult(self):
     url = self._baseAsrUrl+'voices/'+self._uuid+"/flush"
     headers = {'Content-Type' : 'application/json', 'X-Token' : self._token }

     data = { "voice_id": self._vid }

     request = urllib2.Request(url, data=json.dumps(data), headers=headers)
     request.get_method = lambda : 'PUT'

     try:
       result = urllib2.urlopen(request)
     except urllib2.HTTPError as e:
       print 'Error code:', e.code
       print 'Reason:', e.reason
       return False
     except urllib2.URLError as e:
       print 'URLErroe reason:', e.reason
       return False
     else:
       response = result.read()
       res = response.decode('utf-8')
       return res

  def request_speech_recog(self, data):
    result = ""
    self.requestAuthToken()
    recaius = self.startVoiceRecogSession()
    if recaius :
      result = self.getVoiceRecogResult(data)
      self.endVoiceRecogSession()
    return result

#
#
#
class RecaiusTts():
  def __init__(self, service_id, passwd, language='ja_JP'):
     self._baseTtsUrl="https://api.recaius.jp/tts/v2/"
     self._service_id=service_id
     self._passwd=passwd
     self._auth=RecaiusAuth(service_id, passwd)
     self._lang = language
     self._token = ''

     self._speaker_id={ 'male' : { 'ja_JP':'ja_JP-M0001-H00T' },
                       'female' : { 'ja_JP':'ja_JP-F0006-C53T', 'en_US' : 'en_US-F0001-H00T',
                                    'zh_CN':'zh_CN-en_US-F0002-H00T', 'fr_FR' : 'fr_FR-F0001-H00T'}
                           }

     opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=0),
                             urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
     urllib2.install_opener(opener)

     self.requestAuthToken()

  #-------- Recaius Authorization
  def requestAuthToken(self):
     res = self._auth.requestAuthToken("speech_synthesis")
     if res :
        self._token = self._auth._token
     return res

  def refreshAuthToken(self):
     return self._auth.refreshAuthToken("speech_synthesis")

    
  def checkAuthToken(self):
     return self._auth.checkAuthToken()

  #-------- PlainText to Speech
  def text2speech(self, text, id='ja_JP-M0001-H00T'):
     url = self._baseTtsUrl+'plaintext2speechwave'
     print url
     headers = {'Content-Type' : 'application/json', 'X-Token' : self._token }

     print headers

     data = { "plain_text": text,
              "lang": self._lang,      # ja_JP, en_US, es_US, fr_CA, en_UK, de_DE, fr_FR, es_ES, zh_CN-en_US, zh_HK-en_US 
              "speaker_id": id,        # [ ja_JP-F0006-C53T,ja_JP-F0006-U01TT, ja_JP-M0001-H00T, ja_JP-M0002-H02T, en_US-F0001-H00T, zh_CN-en_US-F0002-H00T, ko_KR-F0003-H00T, fr_FR-F0001-H00T ]
#              "speed": 0,              # [ -10:10 ]
#              "pitch": 0,              # [ -10:10 ]
#              "depth" : 0,             # [ -4:4 ]
#              "volume" : 0,            # [ -50:50 ]
#              "upower" : 0,            # [ -10:10 ]
#              "happy"  : 0,            # [ 0:200]
#              "angry"  : 0,            # [ 0:200]
#              "sad"  : 0,              # [ 0:200]
#              "fear"  : 0,             # [ 0:200]
#              "tender"  : 0,           # [ 0:200]
#              "voiceelements"  : 0,    # [ -100:100] (dim 11)
#              "tag_mode"  : 0,         # [ 0, 1 ]
#              "txtproc_jajp_read_digit" : 0,     # [ 0, 1 ]
#              "txtproc_jajp_read_symbol" : 0,    # [ 0, 1 ]
#              "txtproc_jajp_read_alphabet" : 0,  # [ 0, 1 ]
#              "txtproc_read_digit" : 0,          # [ 0, 1 ]
              "codec"  : 'audio/x-linear', # audio/wav, ogg, x-linear, x-adpcm, x-m4a, mpeg
              "kbitrate" : 256        # 352, 256, 128, 64, 32, 15
          }

     print json.dumps(data)
     request = urllib2.Request(url, data=json.dumps(data), headers=headers)
     request.get_method = lambda : 'POST'

     try:
       result = urllib2.urlopen(request)
     except urllib2.HTTPError as e:
       print 'Error code:', e.code
       print 'Reason:', e.reason
       return ""
     except urllib2.URLError as e:
       print 'URLError reason:', e.reason
       return ""
     else:
       response = result.read()
       return response

  def getSpeakerId(self, ch, lang):
    return self._speaker_id[ch][lang]
 
  def getaudio(self, text, fname, speaker_id):
    data = self.text2speech(text, speaker_id)
    print fname
    if data :
       saveWavData(fname, data)
    return
#

#
#
#
def getWavData(fname):
    try:
        f = wave.open(fname)
        data = f.readframes(f.getnframes())
        f.close()
        return data
    except:
        return ""

#
#
#
def saveWavData(fname, data):
    try:
        f=open(fname, 'wb')
        f.write(data)
        f.close()
        return True
    except:
        print "Write Error"
        return False

#
#
#
def divString(s, n):
  ll=len(s)
  res = []
  for x in range(int(math.ceil(float(ll) / n))):
    res.append( s[ x*n : x*n + n ] )

  return res

#
#
#
def show_result(result):
  try:
    data = json.loads( result )
    i=1
    for d in data[0]['result'] :
      if 'confidence' in d:
          print "#"+str(i)+":"+d['str']+" ("+str(d['confidence'])+")"
      else:
          print "#"+str(i)+":"+d['str']
      i+=1
  except:
    print result


#
#
#
def main(id, passwd):
  import glob
  recaius = RecaiusAsr(id, passwd)
  files = glob.glob('log/*.wav')
  files.sort()

  for f in files:
    print f
    data = getWavData(f)

    result = recaius.request_speech_recog(data)
    if result :
      show_result(result)

    else:
      print "No Result"
    print ""


def main_asr(id, passwd, f):
  recaius = RecaiusAsr(id, passwd)
  print f
  data = getWavData(f)

  result = recaius.request_speech_recog(data)
  if result :
    show_result(result)
  else:
    print "No Result"

def main_tts(id, passwd, txt, outfname):
  recaius = RecaiusTts(id, passwd)

  result = recaius.text2speech(txt)
  if result :
    saveWavData(outfname, result)
  else:
    print "No Result"

    
#
#  Main
#
if __name__ == '__main__':
  name = sys.argv[1]
  f=open(name+".txt")
  txt = f.read()
  f.close()
  main_tts('service_id', 'pass',txt, name+".wav")


