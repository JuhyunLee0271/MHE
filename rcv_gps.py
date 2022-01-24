from PyQt5.QtCore import QThread, pyqtSlot
import serial, os
import serial.tools.list_ports

"""
RCV_GPS(QThread): GPS Reciever Thread used in the PyQt5 GUI Program
    - GPS Receiver needs to be connected to USB port (Map through VID:PID, @targetId)
    - Parse the 'time', 'speed', 'heading', 'latitude', 'longitude', 'num_sats' every second using the RMC, GGA of the GPS GNSS dataset
    - Result is stored at the designated location (@self.file_path)
    - To use, self.thread.start() after self.thread = RCV_GPS() in the main window
"""
class RCV_GPS(QThread):

    def __init__(self, parent=None):
        print("RCV_GPS init")
        super().__init__()
        self.main = parent
        self.exists_ports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
        self.ser_port = None
        self.date = None

        self.temp = dict()
        self.time = '0.0'
        self.speed = '0.0'
        self.latitude = '0.0'
        self.longitude = '0.0'
        self.heading = '0.0'
        self.num_sats = 0

        self.file_path = None
        self.file_ = None
        self.date = None
        self.isLive = True
        self.isRecording_GPS = False

        if not os.path.exists('./IMU_data/'):
            os.makedirs('./IMU_data/')

        targetId = "VID:PID=1546:01A7" # GNSS reciver GPS620
        
        for port in self.exists_ports:
            if targetId in port[2]:
                try:
                    self.ser_port = serial.Serial(port[0], 9600)
                    self.isLive = True
                    break
                except:
                    pass
                
        print(f"RCV_GPS's PORT: {self.ser_port}")
        
        # Connection Error signal
        if self.ser_port == None or not self.ser_port.isOpen():
            print("GPS Connection Error!")
            self.isLive = False

    def run(self):
        while self.isLive == True:     
            if self.ser_port.inWaiting() > 0 :
                line = self.ser_port.readline().decode('utf-8')
                
                NMEA_Type = line[3:6] # RMC, VTG, GGA, GSA, GSV, GLL ...
                contents = line.split(',')
            
                # Use RMC, GGA to get 'time', 'speed', 'heading', 'latitude', 'longitude', 'num_sats' from GPS Dataset
                if NMEA_Type in ["RMC", "GGA"]: 
                    
                    self.temp[NMEA_Type] = contents
                    if self.temp.get('RMC') and self.temp.get('GGA'):
                        if self.temp.get('RMC'):
                            if self.temp['RMC'][1] != "":
                                self.time = self.temp['RMC'][1][:self.temp['RMC'][1].find('.')].zfill(6) # e.g. 073814
                            if self.temp['RMC'][7] != "":
                                self.speed = str(float(self.temp['RMC'][7])*1.852) # knots -> km/h 
                            if self.temp['RMC'][8] != "":
                                self.heading = self.temp['RMC'][8]
                
                        if self.temp.get('GGA'):         
                            if self.temp['GGA'][2] != "":
                                self.latitude = str((float(self.temp['GGA'][2]) / 100.0)) + "°" + self.temp['GGA'][3]                
                            if self.temp['GGA'][4] != "":
                                self.longitude = str((float(self.temp['GGA'][4]) / 100.0)) + "°" + self.temp['GGA'][5]
                            self.num_sats = int(self.temp['GGA'][7])
                                                
                        if self.isRecording_GPS:
                            self.file_.write("\n%s,%s,%s,%s,%d,%s" % (self.time, self.speed, self.latitude, self.longitude, self.num_sats, self.heading))
                                                
                        self.temp.clear()
                        self.time = "0.0"
                        self.speed = "0.0"
                        self.latitude = "0.0"
                        self.longitude = "0.0"
                        self.heading = "0.0"
                        self.num_sats = 0
                    else:
                        continue
                else:
                    continue
    
    @pyqtSlot(list)
    # @args = [filename, date]
    def startRecord(self, args):
        if self.isLive == True :
            self.isRecording_GPS = True
            
            self.date = args[1]
            if not os.path.exists('./IMU_data/'):
                os.makedirs('./IMU_data/')    

            if args[0] == "":
                self.file_path = ('./IMU_data/' + self.date + '_GPS.csv')
            else:
                self.file_path = ('./IMU_data/' + self.date + '_' + args[0] + '_GPS.csv')
            self.file_ = open(self.file_path, 'a')
            self.file_.write("time(h/m/s),speed(km/h),latitude,longitude,num_sats,heading(°)")

    @pyqtSlot()
    def stopRecord(self):
        self.isRecording_GPS = False
        self.temp.clear()
        self.file_.close()
        self.quit()
        self.wait(100)