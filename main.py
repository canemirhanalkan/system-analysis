import sys
from urllib.request import urlopen
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView
import xml.etree.ElementTree as et
import cv2
from ultralytics import YOLOv10
import supervision as sv
import re




class SystemAnalysis(QMainWindow):
    def __init__(self):
        super(SystemAnalysis, self).__init__()

        self.setWindowTitle("System Analysis Project")
        self.setGeometry(100,100,800,800)


        
    #------------cam area
        self.cam_label = QtWidgets.QLabel(self)
        self.cam_label.setGeometry(150,100,500,400)



                
        #-----------rates
        self.url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        self.xml = et.ElementTree(file=urlopen(self.url))

        self.root = self.xml.getroot()

        for self.rate in self.root:
            if self.rate.attrib.get("CurrencyCode") == "USD":
                self.usd = float(self.rate.find("BanknoteSelling").text)

            elif self.rate.attrib.get("CurrencyCode") == "EUR":
                self.euro = float(self.rate.find("BanknoteSelling").text)

            elif self.rate.attrib.get("CurrencyCode") == "GBP":
                self.gbp = float(self.rate.find("BanknoteSelling").text)



    
    #------------Currencys labels
        #-----------tl
        self.tl = QtWidgets.QLabel(self)
        self.tl.setText("Turkish Lira")
        self.tl.setGeometry(50,530,150,40)
        self.tl.setStyleSheet("font-weight: bold;")
            #------tl-value
        self.tl_value = QtWidgets.QLabel(self)
        self.tl_value.setGeometry(50,570,100,30)
        self.tl_value.setStyleSheet("font-size: 20px; color: #f95959;")




        #-----------usd
        self.usd_label = QtWidgets.QLabel(self)
        self.usd_label.setText(f"USD | {self.usd:.2f}")
        self.usd_label.setGeometry(210,530,150,40)
        self.usd_label.setStyleSheet("font-weight: bold;")
            #------usd-value
        self.usd_value = QtWidgets.QLabel(self)
        self.usd_value.setGeometry(210,570,100,30)
        self.usd_value.setStyleSheet("font-size: 20px; color: #f95959;")


        #-----------euro
        self.euro_label = QtWidgets.QLabel(self)
        self.euro_label.setText(f"Euro | {self.euro:.2f}")
        self.euro_label.setGeometry(370,530,150,40)
        self.euro_label.setStyleSheet("font-weight: bold;")
            #------euro-value
        self.euro_value = QtWidgets.QLabel(self)
        self.euro_value.setGeometry(370,570,100,30)
        self.euro_value.setStyleSheet("font-size: 20px; color: #f95959;")


        #-----------gbp
        self.gbp_label = QtWidgets.QLabel(self)
        self.gbp_label.setText(f"British Pound | {self.gbp:.2f}")
        self.gbp_label.setGeometry(530,530,230,40)
        self.gbp_label.setStyleSheet("font-weight: bold;")
            #------gbp-value
        self.gbp_value = QtWidgets.QLabel(self)
        self.gbp_value.setGeometry(530,570,100,30)
        self.gbp_value.setStyleSheet("font-size: 20px; color: #f95959;")




        #detect-object
        self.detected_label = QtWidgets.QLabel(self)
        self.detected_label.setText("Money: ")
        self.detected_label.setGeometry(210, 650, 400, 100)
        self.detected_label.setStyleSheet("font-size: 30px;")


        self.money_detection()


    def money_detection(self): 
        
        #yolo-model
        self.model = YOLOv10('moneys.pt')

        self.cap = cv2.VideoCapture(0)
 
        if not self.cap.isOpened():
            print("error:cam")
            return
    
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30) #30ms fps update

        self.bounding_box_annotator = sv.BoundingBoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()

        

    def update_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            print("error:cam")
            self.timer.stop()
            return
        
        result = self.model(frame)[0]
        detections = sv.Detections.from_ultralytics(result)


        self.detected_labels = [result.names[int(class_id)] for class_id in detections.class_id]
        self.detected_text = ", ".join(self.detected_labels) if self.detected_labels else "NaN"

        self.numerical_value = re.findall(r'\d+', self.detected_text)
        
        if self.numerical_value:
            self.numerical_value = int(self.numerical_value[0])

        
        #----------money names
        if self.detected_text == "10_tl":
            self.detected_label.setText(f"Money: {self.numerical_value} TURKISH LIRA")
        elif self.detected_text == "100_tl":
            self.detected_label.setText(f"Money: {self.numerical_value} TURKISH LIRA")
            self.detected_label.setStyleSheet("font-size: 28px;")
        elif self.detected_text == "10_usd":
            self.detected_label.setText(f"Money: {self.numerical_value} USD")
        elif self.detected_text == "50_euro":
            self.detected_label.setText(f"Modney: {self.numerical_value} EURO")




        self.calculate()



        annotated_image = self.bounding_box_annotator.annotate(
            scene=frame,
            detections=detections
        )

        annotated_image = self.label_annotator.annotate(
            scene=annotated_image,
            detections=detections
        )


        rgb_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_image.shape
        qimg = QImage(rgb_image.data, width, height, channel * width, QImage.Format_RGB888)

        self.cam_label.setPixmap(QPixmap.fromImage(qimg).scaled(self.cam_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))



    def closeEvent(self, event):
        if self.cap.isOpened():
            self.cap.release()
        event.accept()



    def calculate(self):
        if self.detected_text == "10_tl":
            self.tl_value.setText(f"{self.numerical_value} ₺")
            
            tl_usd = round(self.numerical_value / self.usd, 2)
            self.usd_value.setText(f"{tl_usd} $")

            tl_euro = round(self.numerical_value / self.euro, 2)
            self.euro_value.setText(f"{tl_euro} €")

            tl_gbp = round(self.numerical_value / self.gbp, 2)
            self.gbp_value.setText(f"{tl_gbp} £")
        
        #100turkishlira
        elif self.detected_text == "100_tl":
            self.tl_value.setText(f"{self.numerical_value} ₺")
            
            tl_usd = round(self.numerical_value / self.usd, 2)
            self.usd_value.setText(f"{tl_usd} $")

            tl_euro = round(self.numerical_value / self.euro, 2)
            self.euro_value.setText(f"{tl_euro} €")

            tl_gbp = round(self.numerical_value / self.gbp, 2)
            self.gbp_value.setText(f"{tl_gbp} £")
        

        elif self.detected_text == "10_usd":
            #usd-tl
            usd_tl = round(self.numerical_value * self.usd, 2)
            self.tl_value.setText(f"{usd_tl} ₺")

            #usd-usd
            self.usd_value.setText(f"{self.numerical_value} $")

            #usd-euro
            usd_euro = round((self.numerical_value * (self.usd / self.euro)), 2)
            self.euro_value.setText(f"{usd_euro} €")

            #usd-gbp
            usd_gbp = round((self.numerical_value * (self.usd / self.gbp)), 2)
            self.gbp_value.setText(f"{usd_gbp} £")

        elif self.detected_text == "50_euro":
            #euro-tl
            euro_tl = round(self.numerical_value * self.euro, 2)
            self.tl_value.setText(f"{euro_tl} ₺")
        
            #euro-usd
            euro_usd = round(self.numerical_value * (self.euro / self.usd), 2)
            self.usd_value.setText(f"{euro_usd} $")

            #euro-euro
            self.euro_value.setText(f"{self.numerical_value} €")

            #euro-gbp
            euro_gbp = round(self.numerical_value * (self.euro / self.gbp))
            self.gbp_value.setText(f"{euro_gbp} £")


        


def Window():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        * { 
            background-color: #233142; 
            font-size: 20px; 
            color: #e3e3e3;
            font-weight: bold;
        }
    """)

    win = SystemAnalysis()

    win.show()
    sys.exit(app.exec_())

Window()
