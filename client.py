#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, time
import bs4, requests, http.client, urllib, urllib.request
import cv2, json, threading
import numpy as np
import xz_rc

from os import path
from urllib.request import urlopen, Request

from PyQt5 import QtCore, uic, QtWidgets, QtGui
from PyQt5.QtCore import QByteArray, qFuzzyCompare, Qt, QTimer
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtWidgets import (QAction, QActionGroup, QApplication, QDialog, QMainWindow, QMessageBox)


# # # # # # # # # # # # # # #
from FaceAPI import *       # MS Face API
from SpeechAPI import *     # MS Speech API
from readMp3 import *       # play mp3 file
from dht11_ import *        # sensor
from max30100_ import *     # sensor

from cfg_var import *       # variables that can vary by user environment
# name of variables defined in cfg(msg)_var.py starts with 'cfg(msg)_'
from msg_var import *       # KOR / ENG language is not switchable for now
# # # # # # # # # # # # # # #


# loading PyQt ui files
Main_Window="MainWindow2.ui"
Camera_Window="CameraWindow2.ui"
Login_Window="LoginWindow2.ui"
Join_Window="JoinWindow2.ui"
Measure_Window="MeasureWindow2.ui"
Recommend_Window="RecommendWindow3.ui"
Fail_Window="FailWindow2.ui"
Finish_Window="FinishWindow2.ui"

Ui_Main_Window, QtBaseClass =uic.loadUiType(Main_Window)
Ui_Camera_Window, QtBaseClass =uic.loadUiType(Camera_Window)
Ui_Login_Window, QtBaseClass =uic.loadUiType(Login_Window)
Ui_Join_Window, QtBaseClass =uic.loadUiType(Join_Window)
Ui_Measure_Window, QtBaseClass =uic.loadUiType(Measure_Window)
Ui_Recommend_Window, QtBaseClass =uic.loadUiType(Recommend_Window)
Ui_Fail_Window, QtBaseClass =uic.loadUiType(Fail_Window)
Ui_Finish_Window, QtBaseClass =uic.loadUiType(Finish_Window)


face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
login_flag=0        # 1 - login, 0 - join

nickname=''         # JoinWindow
phone=''            # JoinWindow
sex=''              # JoinWindow
temp=0              # MeasureWindow
weather=''          # MeasureWindow 

faces=0             # FaceDetectionWidget

heart_rate=0        # sensor
SpO2=0              # sensor
store_temp=0        # sensor
store_humidity=0    # sensor

groupID=sys.argv[1]             # MS Face Group ID
UserName = ''                   # used in Speech API
person_id = ''
faceinfo = {}                   # faceInfo parsed from Face API
sensor_result = False
recommend_drink = '당근주스'

message_CAMERA1 = msg_CAMERA1_KOR   # CameraWindow
message_EMPTY1 = msg_EMPTY1_KOR     # JoinWindow
message_EMPTY2 = msg_EMPTY2_KOR     # JoinWindow
message_PHONE1 = msg_PHONE1_KOR     # JoinWindow & FailWindow

# Get data from sensor
def collect_sensor_data ():
    global heart_rate    
    global SpO2
    global store_temp
    global store_humidity

    heart_rate = 0
    store_temp,store_humidity=measure_tem_humi()
    #print(store_temp,store_humidity)
    heart_rate,SpO2=measure_pulse_O2()
    #print(heart_rate,SpO2)

    if heart_rate == 0:
        return False
    else:
        return True


# return 1 : correct phone number, return 0 : wrong phone number
def checkPhoneNumber(phone):
    
    if len(phone) == 11:
        for i in range(11):
            if phone[i] <'0' or phone[i]>'9':
                return 0
        return 1
    
    elif len(phone)==13:
        if phone[3]!='-' or phone[8]!='-':
            return 0
        
        for i in range(13):
            if (i!=3 and i!=8) and (phone[i] <'0' or phone[i]>'9'):
                return 0
        return 1
    else:
        return 0


# Naver Weather Info Crawler
def collect_weather_info():
    global temp
    global weather
    
    enc_location=urllib.parse.quote(cfg_LOCATION+'+날씨')
    url='https://search.naver.com/search.naver?ie=utf8&query='+ enc_location

    req=Request(url, headers={'User-Agent':'Mozilla/5.0'})
    page=urlopen(req)
    html=page.read()
    soup=bs4.BeautifulSoup(html,'html.parser')
    
    temp=soup.find('p',class_='info_temperature').find('span',class_='todaytemp').text
    weather=soup.find('ul',class_='info_list').find('p',class_='cast_txt').text       #ex) 구름조금, 어제보다 1도 높음.
    weather=weather.split(',')[0]

    
class RecordVideo(QtCore.QObject):
    image_data = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, camera_port=0, parent=None):
        super().__init__(parent)
        self.camera = cv2.VideoCapture(camera_port)
        self.timer = QtCore.QBasicTimer()

    def start_recording(self):          
        self.timer.start(0, self)
    def stop_recording(self):           
        self.timer.stop()
        self.camera.release()
        self.camera=cv2.VideoCapture(0)
    def timerEvent(self, event):
        if (event.timerId() != self.timer.timerId()):
            return
        read, data = self.camera.read()
        if read:
            self.image_data.emit(data)


class FaceDetectionWidget(QtWidgets.QWidget):
    def __init__(self, haar_cascade_filepath, parent=None):
        super().__init__(parent)
        self.classifier = cv2.CascadeClassifier(haar_cascade_filepath)
        self.image = QtGui.QImage()
        self._red = (0, 0, 255)
        self._width = 2
        self._min_size = (30, 30)

    def detect_faces(self, image: np.ndarray):
        # haarclassifiers work better in black and white
        global faces
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_image = cv2.equalizeHist(gray_image)
        
        faces = self.classifier.detectMultiScale(gray_image,
                                                 scaleFactor=1.3,
                                                 minNeighbors=4,
                                                 flags=cv2.CASCADE_SCALE_IMAGE,
                                                minSize=self._min_size)

        return faces

    def image_data_slot(self, image_data):
        global faces
        global UserName
        global person_id
        global faceinfo
        
        faces = self.detect_faces(image_data)

        # draw face rectangle
        for (x, y, w, h) in faces:
            cv2.rectangle(image_data,
                          (x, y),
                          (x+w, y+h),
                          self._red,
                          self._width)
        
        self.image = self.get_qimage(image_data)
        if self.image.size() != self.size():
            self.setFixedSize(self.image.size())

        
        # check if rectangle is bigger than certain size
        if type(faces) is not tuple and faces[0][3] >250 :
            cv2.imwrite('try.jpg',image_data)

            CameraWindow1.record_video.stop_recording()

            if login_flag==1:               # login
                api_result, faceinfo, UserName = face_api(True,nickname,groupID)
                if api_result == False:     # Face API Fail 2 or 3
                                            # Fail 2 - No Face Detected
                                            # Fail 3 - Nobody Matched
                    FailWindow1.showFullScreen()
                     
                else :                      # Face API Success 2
                    MeasureWindow1.showFullScreen()
                    MeasureWindow1.Measure()
                    
            else:                           # Join
                UserName = nickname
                api_result, faceinfo, person_id = face_api(False,nickname,groupID)
                
                MeasureWindow1.showFullScreen()
                MeasureWindow1.Measure()

            CameraWindow1.close()
    
        else:
            self.update()
    
    def get_qimage(self, image: np.ndarray):
        height, width, colors = image.shape
        bytesPerLine = 3 * width
        QImage = QtGui.QImage

        image = QImage(image.data,
                       width,
                       height,
                       bytesPerLine,
                       QImage.Format_RGB888)

        image = image.rgbSwapped()
        return image

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.image)
        self.image = QtGui.QImage()


# Main Window with background image
# Touch input changes MainWindow to LoginWindow
class MainWindow(QtWidgets.QMainWindow, Ui_Main_Window):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_Main_Window.__init__(self)
        self.setupUi(self)
        self.pushButton_Main.clicked.connect(self.Main_button_clicked)
    
    def Main_button_clicked(self):
        LoginWindow1.showFullScreen()
        self.close()
    

# Login button & Join button
# Login button touched -> CameraWindow
# Join  button touched -> JoinWindow
class LoginWindow(QtWidgets.QMainWindow, Ui_Login_Window):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_Login_Window.__init__(self)
        self.setupUi(self)
        self.pushButton_login.clicked.connect(self.Login_login_button_clicked)
        self.pushButton_join.clicked.connect(self.Login_join_button_clicked)
        
    def Login_login_button_clicked(self):
        global login_flag

        login_flag=1
        CameraWindow1.record_video.start_recording()
        CameraWindow1.showFullScreen()
        self.close()
        
    def Login_join_button_clicked(self):
        JoinWindow1.showFullScreen()
        self.close()


# Camera method powered by OpenCV
# When detected face size exceeds certain value, FaceAPI is called
class CameraWindow(QtWidgets.QMainWindow, Ui_Camera_Window):
    def __init__(self,haar_cascade_filepath):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        self.setGeometry(0, 0, 800, 480)
        self.centralwidget=QtWidgets.QWidget(self)

        # Defines entire camera screen label
        self.camera_main_label=QtWidgets.QLabel(self.centralwidget)
        self.camera_main_label.setGeometry(QtCore.QRect(-1, -1, 800, 480))
        self.camera_main_label.setStyleSheet("border-image: url(:/newPrefix/image/juicebro.jpg);")
        self.camera_main_label.setObjectName("camera_main_label")

        # Defines a text label above the screen
        self.camera_title_label=QtWidgets.QLabel(self.centralwidget)
        self.camera_title_label.setGeometry(QtCore.QRect(50, 40, 680, 71))  

        font = QtGui.QFont()
        font.setFamily(cfg_FONTS)
        font.setPointSize(22)
        self.camera_title_label.setFont(font)
        self.camera_title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.camera_title_label.setObjectName("camera_title_label")

        # Camera widget
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(50, 90, 700, 400))

        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.layout = QtWidgets.QHBoxLayout(self.verticalLayoutWidget)
        self.layout.setObjectName("layout")
        
        fp = haar_cascade_filepath

        self.face_detection_widget = FaceDetectionWidget(fp)
        self.record_video = RecordVideo()
        image_data_slot = self.face_detection_widget.image_data_slot
        self.record_video.image_data.connect(image_data_slot)

        self.layout.addWidget(self.face_detection_widget)
        self.verticalLayoutWidget.setLayout(self.layout)

        self.setCentralWidget(self.centralwidget)
        self.retranslateUi(self)

    def retranslateUi(self, CameraWindow1):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("CameraWindow1", "MainWindow"))
        self.camera_title_label.setText(_translate("CameraWindow1", message_CAMERA1))


class JoinWindow(QtWidgets.QMainWindow, Ui_Join_Window):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_Join_Window.__init__(self)
        self.setupUi(self)
        self.pushButton_join_next.clicked.connect(self.Join_next_button_clicked)
        
    def Join_next_button_clicked(self):
        global nickname
        global phone
        global sex

        nickname=self.lineEdit_id.text()
        phone=self.lineEdit_phone.text()

        if nickname=="" or phone=="":   # empty
            QMessageBox.information(self, "Empty Field", message_EMPTY1)
            return

        if self.radioButton_man.isChecked():
            sex="man"
        elif self.radioButton_woman.isChecked():
            sex="woman"
    
        else:
             QMessageBox.information(self, "Empty Field", message_EMPTY2)
             return

        if checkPhoneNumber(phone)==0:
            QMessageBox.information(self, "Empty Field", message_PHONE1)
            return

        if len(phone)==13:
            list=phone.split('-')
            phone=list[0]+list[1]+list[2]

        CameraWindow1.record_video.start_recording()        

        # Initialize text
        self.lineEdit_id.clear()
        self.lineEdit_phone.clear()
        
        self.group=QtWidgets.QButtonGroup()

        self.group.addButton(self.radioButton_man)
        self.group.addButton(self.radioButton_woman)
        self.group.setExclusive(False)

        self.radioButton_man.setChecked(False)
        self.radioButton_woman.setChecked(False)

        self.group.setExclusive(True)
        
        CameraWindow1.showFullScreen()
        self.close()


# Measure Sensor data and change to RecommendWindow
class MeasureWindow(QtWidgets.QMainWindow, Ui_Measure_Window):
    def __init__(self):
        super().__init__()
        QtWidgets.QMainWindow.__init__(self)
        Ui_Measure_Window.__init__(self)
        self.setupUi(self)

    def Measure(self):
        global sensor_result
        sensor_result = collect_sensor_data()
   
        if sensor_result == True :
            sensor_result = False
            RecommendWindow1.showFullScreen()


# Create TTS mp3 file that recommends beverage to user
# CAUTION : THIS WINDOW MUST BE IMPROVED AND REFINED
class RecommendWindow(QtWidgets.QMainWindow, Ui_Recommend_Window):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_Recommend_Window.__init__(self)
        self.setupUi(self)
        self.pushButton_apple.clicked.connect(self.Apple_button_clicked)
        self.pushButton_carrot.clicked.connect(self.Carrot_button_clicked)

    def Apple_button_clicked(self):
        createMp3(UserName, '사과주스')
        FinishWindow1.showFullScreen()
        FinishWindow1.Recommend()
        self.close()

    def Carrot_button_clicked(self):
        createMp3(UserName, '당근주스')
        FinishWindow1.showFullScreen()
        FinishWindow1.Recommend()
        self.close()


# If the user tries to login but FaceAPI returns Fail
# Get userdata like phone number to identify who the user is
class FailWindow(QtWidgets.QMainWindow, Ui_Fail_Window):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_Fail_Window.__init__(self)
        self.setupUi(self)
        self.pushButton_fail_next.clicked.connect(self.Fail_next_button_clicked)

    def Fail_next_button_clicked(self):
        global phone    
        phone=self.lineEdit_fail_phone.text()
    
        if phone=="":
            QMessageBox.information(self, "Empty Field", message_EMPTY1)
            return

        if checkPhoneNumber(phone)==0:
            QMessageBox.information(self, "Empty Field", message_PHONE1)
            return

        if len(phone)==13:
            list=phone.split('-')
            phone=list[0]+list[1]+list[2]

        self.lineEdit_fail_phone.clear()
        MeasureWindow1.showFullScreen()
        MeasureWindow1.Measure()
        self.close()


# play TTS mp3 created in RecommendWindow
# update weather info and go back to MainWindow
class FinishWindow(QtWidgets.QMainWindow, Ui_Finish_Window):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_Finish_Window.__init__(self)
        self.setupUi(self)

    def Recommend(self):
        readMp3File()
        global login_flag
        global faces
        collect_weather_info()

        if login_flag==0:       # Join
            data={'id':nickname, 'phone':phone,'sex':sex,'weather':weather,'personid':person_id, 'storeid':cfg_LOCATION, 'temp':temp,'faceinfo':json.dumps(faceinfo)}
            print(data)
            #rep=requests.post(cfg_SERVER_URL,data=data)    # REQUIRES SOME IMPROVEMENT
        else:
            login_flag=0
        
        faces=0
        
        MainWindow1.showFullScreen()
        

if __name__ == "__main__":
    script_dir = path.dirname(path.realpath(__file__))
    haar_cascade_filepath = path.join(script_dir,
                                 '..',
                                 'data',
                                 #'C:/Users/new/Desktop/uic/haarcascade_frontalface_default.xml')
                                 cfg_MAIN_DIR + '/haarcascade_frontalface_default.xml')
    haar_cascade_filepath = path.abspath(haar_cascade_filepath)
    app = QtWidgets.QApplication(sys.argv)
    
    MainWindow1=MainWindow()
    LoginWindow1=LoginWindow()
    CameraWindow1=CameraWindow(haar_cascade_filepath)
    JoinWindow1=JoinWindow()
    MeasureWindow1=MeasureWindow()
    RecommendWindow1=RecommendWindow()
    FailWindow1=FailWindow()
    FinishWindow1=FinishWindow()
    
    collect_weather_info()

    MeasureWindow1.showFullScreen()
    FinishWindow1.showFullScreen()
    MainWindow1.showFullScreen()

    sys.exit(app.exec_())

