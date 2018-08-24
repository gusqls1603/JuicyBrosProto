import http.client, urllib.request, urllib.parse, urllib.error, base64
import requests
import sys
import json as js
import ast
from PIL import Image
from cfg_var import *

json = 'application/json'
octet = 'application/octet-stream'

MS_Face_subscription_key = cfg_FACE_SUB_KEY # MS Face subscription key
Face_API_service_area = cfg_FACE_SERV_AREA  # MS Face API service area

img_dir = cfg_MAIN_DIR + '/try.jpg'                   # raspberry


# Create LargePersonGroup
# parameter - group id to create
# return - none
def create(groupID) :
    headers = {
        'Content-Type': json,
        'Ocp-Apim-Subscription-Key': MS_Face_subscription_key
    }    
    params = urllib.parse.urlencode({
        "largePersonGroupId" : groupID  # must be string
    })    
    body = {
        "name" : groupID + '_Name'
    }
    try:
        conn = http.client.HTTPSConnection(Face_API_service_area + '.api.cognitive.microsoft.com')
        conn.request("PUT", "/face/v1.0/largepersongroups/{largePersonGroupId}?%s" % params, str(body), headers)

        response = conn.getresponse()
        data = response.read()

        conn.close()

    except Exception as e:
        print('Error:')
        print(e)


# Detect Face from Local Image
# parameter - image data (binary) & image directory
# return - face id & face info (expired after 24 hours in MS server)
def detect_local(image_data, image_dir = img_dir) :
    data = {}
    headers = {
        'Content-Type': octet,
        'Ocp-Apim-Subscription-Key': MS_Face_subscription_key
    }
    params = {
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes' : 'age,gender,smile,glasses,emotion,makeup,accessories,blur,exposure,noise'
    }
    try:
        response = requests.post('https://' + Face_API_service_area + '.api.cognitive.microsoft.com/face/v1.0/detect',
                                     data = image_data,
                                     headers = headers,
                                     params = params)
        parsed = response.json()
        #print(parsed)  #responsed data from MS server
        
        if not parsed : # No Face Detected
            #print('Face not detected')    
            return False, None

        faceID = str(parsed[0]['faceId'])     

        data['faceId'] = faceID
        data['age'] = str(parsed[0]['faceAttributes']['age'])
        data['smile'] = str(parsed[0]['faceAttributes']['smile'])
        data['emotion'] = str(parsed[0]['faceAttributes']['emotion'])
        data['glasses'] = str(parsed[0]['faceAttributes']['glasses'])
        data['makeup'] = str(parsed[0]['faceAttributes']['makeup'])
        
        # create json file - NOT USED
        #with open(faceID + '.json', 'w') as fp:
        #    js.dump(data, fp)

        # create cropped image - NOT USED
        # print('creating image file...')
        #img = Image.open(image_dir)
        #crop_area = (parsed[0]['faceRectangle']['left'], parsed[0]['faceRectangle']['top'],
        #             parsed[0]['faceRectangle']['left'] + parsed[0]['faceRectangle']['width'],
        #             parsed[0]['faceRectangle']['top'] + parsed[0]['faceRectangle']['height'])
        #img = img.crop(crop_area)
        #img.save(faceID + '.jpg')      #create image file
        
        return faceID, data
        
    except Exception as e:
        print('Error:')
        print(e)
        return


# Create 'Unique' PersonID from Nickname
# Created PersonID will be added in the LargePersonGroup with Userdata
# parameter - group id to add userdata & user's nickname
# return - person id
def create_personid(groupID, nick_name) :
    headers = {
        'Content-Type': json,
        'Ocp-Apim-Subscription-Key': MS_Face_subscription_key
    }
    params = urllib.parse.urlencode({
        "largePersonGroupId" : groupID  # must be string
    })
    body = {
        "name" : nick_name
    }
    try:
        conn = http.client.HTTPSConnection(Face_API_service_area + '.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/largepersongroups/{largePersonGroupId}/persons?%s" % params, str(body).encode('utf-8'), headers)

        response = conn.getresponse()
        data = response.read()
        #print(data)            # print created personID
        conn.close()
        return str(data)[15:-3] # may cause error? seems working for now
    
    except Exception as e:
        print('Error:')
        print(e)


# Add Face data to LargePersonGroup
# parameter - groupid, personid, imgdata
# return - persistedfaceid
# Added data remains after 24 hours unless 'delete api - NOT CODED' is called
# The extracted face feature, instead of the actual image, will be stored on server
def addface_local(groupID, personID, image_data) :
    headers = {
        'Content-Type': octet,
        'Ocp-Apim-Subscription-Key': MS_Face_subscription_key
    }
    params = urllib.parse.urlencode({
        "largePersonGroupId" : groupID,
        'personId': personID
    })
    try:
        response = requests.post('https://' + Face_API_service_area + '.api.cognitive.microsoft.com/face/v1.0/largepersongroups/{largePersonGroupId}/persons/{personId}/persistedfaces',
                                     data = image_data,
                                     headers = headers,
                                     params = params)
        parsed = response.json()
        #print(parsed)      #print persistedFaceID

        return parsed['persistedFaceId']

    except Exception as e:
        print('Error:')
        print(e)


# Train LargePersonGroup
# parameter - group id to train
# return - none
# Face_Identify API is available only after the group is trained
def train(groupID) :
    headers = {
        'Ocp-Apim-Subscription-Key': MS_Face_subscription_key
    }
    params = urllib.parse.urlencode({
        "largePersonGroupId" : groupID
    })
    body = {

    }
    try:
        conn = http.client.HTTPSConnection(Face_API_service_area + '.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/largepersongroups/{largePersonGroupId}/train?%s" % params, str(body), headers)
        response = conn.getresponse()

        data = response.read()
        #print(data)    # empty if success

        conn.close()

    except Exception as e:
        print('Error:')
        print(e)


# With given faceID and target groupID, returns personid of a user that matches most
# parameter - face id, group id
# return - bool, matched user's personid
def face_identify(faceID, groupID) :
    faceidlist = []
    faceidlist.append(faceID)
    headers = {
        'Content-Type': json,
        'Ocp-Apim-Subscription-Key': MS_Face_subscription_key
    }
    params = urllib.parse.urlencode({

    })
    body = {
        "largePersonGroupId": groupID,
        "faceIds": faceidlist,              # must be string
        "maxNumOfCandidatesReturned": 1,    # optional
        "confidenceThreshold": 0.7          # optional
    }
    try:
        conn = http.client.HTTPSConnection(Face_API_service_area + '.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/identify?%s" % params, str(body), headers)

        response = conn.getresponse()
        data = response.read()
        aa=data.decode('utf-8')
        data_dic=ast.literal_eval(aa)
        #print(data_dic)
        #print(type(data_dic[0]['candidates']))
        if len(data_dic[0]['candidates']) ==0:
            return False, 'empty'
        else:
            return True, data_dic[0]['candidates'][0]['personId']
        #    print(data_dic[0]['candidates'])
        conn.close()

    except Exception as e:
        print('Error:')
        print(e)


# Get Userdata from given groupID and personID
# available TARGET : 'personId', 'persistedFaceIds', 'name', 'userData'
# type of TARGET must be str
def get_userData (groupID, personID, TARGET):
    headers = {
        'Ocp-Apim-Subscription-Key': MS_Face_subscription_key
    }
    params = urllib.parse.urlencode({
        'largePersonGroupId' : groupID,
        'personId' : personID
    })
    body = {

    }

    try:
        conn = http.client.HTTPSConnection(Face_API_service_area + '.api.cognitive.microsoft.com')
        conn.request("GET", "/face/v1.0/largepersongroups/{largePersonGroupId}/persons/{personId}?%s" % params, str(body), headers)
        response = conn.getresponse()
        data = response.read()

        bb = data.decode('utf8')    # bytes to string
        cc = js.loads(bb)           # string to dict

        conn.close()
        return cc[TARGET]

    except Exception as e:
        print('Error:')
        print(e)
    

#if login==True  (Sign In), returns bool, None, UserName
#if login==False (Sign Up), returns bool, faceinfo, personid
def face_api (login, nick_name, groupID) :
    with open(img_dir, 'rb') as f:
        img_data = f.read()

    faceID, detect_result = detect_local(img_data)
    
    if login == False :     # Join (Sign Up)
        if faceID==False:   # MS API says 'No Face Detected' in Join mode
            print('FaceAPI Fail 1')
            return False, None, None
        personID = create_personid(groupID, nick_name)
        persistedfaceid = addface_local(groupID, personID, img_data)
        train(groupID)
        print('FaceAPI Success 1')
        return True, detect_result, personID
    else :                  # Login (Sign In)
        if faceID==False:   # MS API says 'No Face Detected' in Login mode
            print('FaceAPI Fail 2')
            return False, None, None
        else:
            res, perID = face_identify(faceID, groupID)
            if res == False:    # Face is found in given image, but 
                                # Nobody in given group matches
                print('FaceAPI Fail 3')
                return False, None, None
            else:
                print('FaceAPI Success 2')
                return True, None, get_userData(groupID, perID, 'name')


# To create new group
if __name__ == "__main__":
    print("IMPORTANT : valid characters include numbers, English letters in lower case, '-' and '_'. The maximum length of the largePersonGroupId is 64")
    grouppID = input('Input groupID to create : ')
    create(grouppID)
    print('Success')
