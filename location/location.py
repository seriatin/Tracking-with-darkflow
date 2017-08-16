import cv2
import os
import json
import configparser


class Singleton(type):
    _instance = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance[cls]

class Location(object, metaclass=Singleton):
   
    PLACE_NAME_FIELD = 'PLC_NAME'
    PLACE_TOP_FIELD = 'PLC_TOP'
    PLACE_LEFT_FIELD = 'PLC_LEFT'
    PLACE_RIGHT_FIELD = 'PLC_RIGHT'
    PLACE_BOTTOM_FIELD = 'PLC_BOTTOM'

    def __init__(self, FLAGS):
        self.value = 0
        self.FLAGS = FLAGS 
        self.currentFrameId = -1
        self.setLocationConfiguration()

    def setLocationConfiguration(self):
        if self.FLAGS.locationConfig:
            self.config = configparser.ConfigParser()
            self.config.read(self.FLAGS.locationConfig)
            self.setSectionList()

    def setSectionList(self):
        if self.config:
            self.sectionList = self.config.sections()
            self.setSectionInfo()

    def setSectionInfo(self):
        sectionInfo = dict()
        cfg = self.config
        for section in self.sectionList:
            if cfg.has_section(section):
                placeNm = cfg.get(section, Location.PLACE_NAME_FIELD)
                placeNmIn = str(placeNm) + '_In'
                placeNmOut = str(placeNm) + '_Out'
                placeNmCurr = str(placeNm) + '_Curr'
                sectionInfo[placeNmIn] = []
                sectionInfo[placeNmOut] = []
                sectionInfo[placeNmCurr] = []
        self.sectionInfo = sectionInfo

    def getPlaceInfo(self, section):
        place = dict()
        place[Location.PLACE_NAME_FIELD] = self.config.get(section, Location.PLACE_NAME_FIELD)
        place[Location.PLACE_TOP_FIELD] = self.config.get(section, Location.PLACE_TOP_FIELD)
        place[Location.PLACE_LEFT_FIELD] = self.config.get(section, Location.PLACE_LEFT_FIELD)
        place[Location.PLACE_RIGHT_FIELD] = self.config.get(section, Location.PLACE_RIGHT_FIELD)
        place[Location.PLACE_BOTTOM_FIELD] = self.config.get(section, Location.PLACE_BOTTOM_FIELD)
        return place

    def getObjectInfo(self, bbox):
        object = dict()
        object[Location.PLACE_LEFT_FIELD] = int(bbox[0])
        object[Location.PLACE_TOP_FIELD] = int(bbox[1])
        object[Location.PLACE_RIGHT_FIELD] = int(bbox[2])
        object[Location.PLACE_BOTTOM_FIELD] = int(bbox[3])
        return object

    def matchingRectangle(self, plc, obj):
        if (int(plc[Location.PLACE_LEFT_FIELD]) > obj[Location.PLACE_RIGHT_FIELD]):
            return False
        if (int(plc[Location.PLACE_RIGHT_FIELD]) < obj[Location.PLACE_LEFT_FIELD]):
            return False
        if (int(plc[Location.PLACE_TOP_FIELD]) > obj[Location.PLACE_BOTTOM_FIELD]):
            return False
        if (int(plc[Location.PLACE_BOTTOM_FIELD]) < obj[Location.PLACE_TOP_FIELD]):
            return False
        return True 

    def isChangeFrame(self, frameId):
        if ( self.currentFrameId != frameId):
            self.currentFrameId = frameId
            return True
        else:
            return False

    def calculatePerson(self, frameId, track):
        plc = dict()
        obj = self.getObjectInfo(track.to_tlbr())
        changeFrame = self.isChangeFrame(frameId)

        for section in self.sectionList:
            plc = self.getPlaceInfo(section)
            placeNmIn = str(plc[Location.PLACE_NAME_FIELD]) + '_In'
            placeNmOut = str(plc[Location.PLACE_NAME_FIELD]) + '_Out'
            placeNmCurr = str(plc[Location.PLACE_NAME_FIELD]) + '_Curr'

            inCount = self.sectionInfo.get(placeNmIn).count(track.track_id)
            outCount = self.sectionInfo.get(placeNmOut).count(track.track_id)
             
            if ( self.matchingRectangle(plc, obj) ):
                if changeFrame:
                   #self.sectionInfo[placeNmPrev] = self.sectionInfo.get(placeNmCurr)
                   self.sectionInfo[placeNmCurr] = []
                self.sectionInfo.get(placeNmCurr).append(track.track_id)
                if ( inCount - outCount <= 0 ):
                   self.sectionInfo.get(placeNmIn).append(track.track_id)
            else:
                if ( inCount > outCount ):
                   self.sectionInfo.get(placeNmOut).append(track.track_id)

    def drawSectionInfo(self, imgcv):
        plc = dict()
        h, w, _ = imgcv.shape
        thick = int((h + w) // 300)
        for section in self.sectionList:
            plc = self.getPlaceInfo(section)
            placeNmCurr = str(plc[Location.PLACE_NAME_FIELD]) + '_Curr'
            placeNmIn = str(plc[Location.PLACE_NAME_FIELD]) + '_In'
            cv2.rectangle(imgcv, (int(plc[Location.PLACE_LEFT_FIELD]), int(plc[Location.PLACE_TOP_FIELD]))
                               , (int(plc[Location.PLACE_RIGHT_FIELD]), int(plc[Location.PLACE_BOTTOM_FIELD]))
                               , (0, 0, 255), thick // 3) 
            cv2.putText(imgcv, plc[Location.PLACE_NAME_FIELD] + ' Count: ' + str(len(self.sectionInfo.get(placeNmIn)))
                             , (int(plc[Location.PLACE_LEFT_FIELD]), int(plc[Location.PLACE_TOP_FIELD]) - 12)
                             , 0, 1e-3 * h, (0, 0, 255), thick // 6) 
           
    def getCenterPosition(bbox):
        centerX = ( bbox[2] - bbox[0] )
        centerY = ( bbox[3] - bbox[1] )
        return (centerX, centerY)

    def overlayTrackingMoving(self, track):
        x, y = self.getCenterPosition(track.to_tlbr())
        
 
