#! /usr/bin/env python3

# -*- coding: utf-8 -*-

###
#Copyright (c) Microsoft Corporation
#All rights reserved. 
#MIT License
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the ""Software""), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###
import http.client, urllib.parse, json
from xml.etree import ElementTree
import io
from cfg_var import *

MS_Speech_subscription_key = cfg_SPEECH_SUB_KEY
Speech_API_service_area = cfg_SPEECH_SERV_AREA
mp3_dir = cfg_MAIN_DIR + '/music.mp3'  # dir to save TTS mp3 file

# Note: new unified SpeechService API key and issue token uri is per region
# New unified SpeechService key
# Free: https://azure.microsoft.com/en-us/try/cognitive-services/?api=speech-services
# Paid: https://go.microsoft.com/fwlink/?LinkId=872236

def createMp3(user = '회원', drink = '당근주스'):
	params = ""
	headers = {"Ocp-Apim-Subscription-Key": MS_Speech_subscription_key}

	#AccessTokenUri = "https://eastasia.api.cognitive.microsoft.com/sts/v1.0/issueToken"
	AccessTokenHost = Speech_API_service_area + ".api.cognitive.microsoft.com"
	path = "/sts/v1.0/issueToken"

	# Connect to server to get the Access Token
	print ("Connect to server to get the Access Token")
	conn = http.client.HTTPSConnection(AccessTokenHost)
	conn.request("POST", path, params, headers)
	response = conn.getresponse()
	print(response.status, response.reason)

	data = response.read()
	conn.close()

	accesstoken = data.decode("UTF-8")
	print ("Access Token: " + accesstoken)

	body = ElementTree.Element('speak', version='1.0')
	body.set('{http://www.w3.org/XML/1998/namespace}lang', 'ko-KR')
	voice = ElementTree.SubElement(body, 'voice')
	voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'ko-KR')
	voice.set('{http://www.w3.org/XML/1998/namespace}gender', 'Female')
	voice.set('name', 'Microsoft Server Speech Text to Speech Voice (ko-KR, HeamiRUS)')
	voice.text = user + ' 님의 맞춤 음료는 ' + drink + ' 입니다.'

	headers = {"Content-type": "application/ssml+xml", 
				"X-Microsoft-OutputFormat": "audio-16khz-64kbitrate-mono-mp3",
				"Authorization": "Bearer " + accesstoken, 
				"X-Search-AppId": "07D3234E49CE426DAA29772419F436CA", 
				"X-Search-ClientID": "1ECFAE91408841A480F00935DC390960", 
				"User-Agent": "TTSForPython"}
			
	#Connect to server to synthesize the wave
	print ("\nConnect to server to synthesize the wave")
	conn = http.client.HTTPSConnection(Speech_API_service_area + ".tts.speech.microsoft.com")
	conn.request("POST", "/cognitiveservices/v1", ElementTree.tostring(body), headers)
	response = conn.getresponse()
	print(response.status, response.reason)

	data = response.read()
	binary_file=open(mp3_dir,mode="wb+")
	#binary_file=open("/home/pi/uic_new/music.mp3",mode="wb+")
	binary_file.write(data)

	conn.close()
	print("The synthesized wave length: %d" %(len(data)))


if __name__ == "__main__":
	createMp3()