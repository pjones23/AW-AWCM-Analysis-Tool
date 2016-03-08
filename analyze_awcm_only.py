'''
Created on Mar 6, 2016

@author: perron
'''
from __builtin__ import True

from sys import argv
from os import path
from time import strptime, strftime, gmtime
from calendar import timegm
from cgi import log

awcmSyncsInMessage = []
awcmSyncsAfterMessage = []
timeBetweenSyncs = []
awcmSyncMessages = 0
awcmSyncPayloads = 0
awcmCommands = 0
failedCommands = 0
meanSyncsAfterMessage = 0
mostSyncsAfterMessage = []
leastSyncsAfterMessage = []
meanSyncsInMessage = 0
mostSyncsInMessage = []
leastSyncsInMessage = []
meanTimeBetweenSyncs = 0
mostTimeBetweenSyncs = []
leastTimeBetweenSyncs = []

totalConnectionFails = 0
totalConnectionResets = 0
connectionResetLogs = []
connectionResetsDuringTimeBetweenMessages = dict()



def getEpochTime(messageDateTime):
    messageDate = messageDateTime[0] + "-2016"
    messageTime = messageDateTime[1]
    combinedDateTime = messageDate + " " + messageTime
    #ex: 03-06-2016 14:42:43.303
    timeStruct = strptime(combinedDateTime, "%m-%d-%Y %H:%M:%S.%f")
    timeInSeconds = timegm(timeStruct)
    return timeInSeconds

def extractIPAddress(beaconLine):
    if "IpAddress" not in beaconLine:
        return None
    ip = None
    beaconSplit = beaconLine.split(",")
    for info in beaconSplit:
        if "IpAddress" in info:
            ip = info.split(":")[1].strip("\"")
            break
    
    return ip

'''
Read in the file and copy out the necessary lines for analysis
'''        

def importAWCMLog(awcmLogFile):
    global awcmSyncsInMessage
    global awcmSyncsAfterMessage
    global failedCommands
    global awcmSyncMessages
    global awcmSyncPayloads
    global awcmCommands
    global timeBetweenSyncs
    
    tempSyncsAfterMessage = 0
    processingMessage = False
    
    previousAWCMTime = None
    currentIP = "None"
    
    connectionFails = 0
    global totalConnectionFails
    connectionResets = 0
    global totalConnectionResets
    global connectionResetLogs
    global connectionResetsDuringTimeBetweenMessages
    
    log = awcmLogFile.readline()
    while log is not None and log != "": #The first line (index 0) is the heading
        if "Incoming AWCM message" in log and "SYNC" in log:
            awcmSyncPayloads+=1
            syncCommandsInMessage = log.count("SYNC")
            awcmSyncsInMessage.append(syncCommandsInMessage)
            awcmSyncMessages+=syncCommandsInMessage
            processingMessage = True
            # calculate time info. Previous should be null only on 1st one
            messageSplit = log.split(" ")
            messageTime = getEpochTime([messageSplit[0], messageSplit[1]])
            
            if previousAWCMTime is None:
                previousAWCMTime = messageTime
                connectionResetsDuringTimeBetweenMessages[previousAWCMTime] = [connectionFails, connectionResets, previousAWCMTime, messageTime]
            else:
                timeSinceLastSince = messageTime - previousAWCMTime
                timeBetweenSyncs.append(timeSinceLastSince)
                connectionResetsDuringTimeBetweenMessages[timeSinceLastSince] = [connectionFails, connectionResets, previousAWCMTime, messageTime]
                previousAWCMTime = messageTime
            
            connectionFails = 0
            connectionResets = 0
        elif "Sending AWCM Sync broadcast" in log:
            awcmCommands+=1
            tempSyncsAfterMessage+=1
            if processingMessage:
                awcmSyncsAfterMessage.append(tempSyncsAfterMessage)
                tempSyncsAfterMessage = 0
                processingMessage = False
        elif "BeaconEntity: Beacon Message" in log:
            #update ip
            ip = extractIPAddress(log)
            if ip is not None:
                currentIP = ip
        elif "Connection reset by peer" in log:
            connectionResets+=1
            totalConnectionResets+=1
            connectionResetString = "IP: " + currentIP + " " + log
            connectionResetLogs.append(connectionResetString)
        elif "3 consecutive failed connection attempts" in log:
            connectionFails+=1
            totalConnectionFails+=1
            connectionFailedString = "IP: " + currentIP + " " + log
            connectionResetLogs.append(connectionFailedString)
                
        
        log = awcmLogFile.readline()


def processAWCMInterations():
    global awcmSyncsAfterMessage
    global meanSyncsAfterMessage
    global mostSyncsAfterMessage
    global leastSyncsAfterMessage
    
    global awcmSyncsInMessage
    global meanSyncsInMessage
    global mostSyncsInMessage
    global leastSyncsInMessage
    
    global timeBetweenSyncs
    global meanTimeBetweenSyncs
    global mostTimeBetweenSyncs
    global leastTimeBetweenSyncs
    
    awcmSyncsAfterMessage.sort()
    meanSyncsAfterMessage = sum(awcmSyncsAfterMessage)/len(awcmSyncsAfterMessage)
    leastSyncsAfterMessage = awcmSyncsAfterMessage[0:20]
    mostSyncsAfterMessage = awcmSyncsAfterMessage[len(awcmSyncsAfterMessage)-20:len(awcmSyncsAfterMessage)]
    
    awcmSyncsInMessage.sort()
    meanSyncsInMessage = sum(awcmSyncsInMessage)/len(awcmSyncsInMessage)
    leastSyncsInMessage = awcmSyncsInMessage[0:20]
    mostSyncsInMessage = awcmSyncsInMessage[len(awcmSyncsInMessage)-20:len(awcmSyncsInMessage)]
    
    timeBetweenSyncs.sort()
    meanTimeBetweenSyncs = sum(timeBetweenSyncs)/len(timeBetweenSyncs)
    leastTimeBetweenSyncs = timeBetweenSyncs[0:20]
    mostTimeBetweenSyncs = timeBetweenSyncs[len(timeBetweenSyncs)-20:len(timeBetweenSyncs)]

if __name__ == '__main__':
    #global companies
    srcFile = None
    destFile = None
    if(len(argv) < 2):
        print("No arguments supplied. Quitting program.")
        exit()
    else:
        #Only use src file and print outout
        srcFile = argv[1]
    
    if not path.isfile(srcFile):
        print("Source file is not valid. Quitting program")
        exit()
    
    awcmLogFile = open(srcFile, mode='r')
    importAWCMLog(awcmLogFile)
    processAWCMInterations()
    awcmLogFile.close()
    
    # print statistics
    '''
    Statistics
    awcmSyncMessages
    awcmCommands
    failedCommands
    mean awcmSyncsAfterMessage
    mostSyncsAfterMessage
    leastSyncsAfterMessage
    mean awcmSyncsInMessage
    mostSyncsInMessage
    leastSyncsInMessage
    mean TimeBetweenSyncs
    mostTimeBetweenSyncs
    leastTimeBetweenSyncs
    '''
   
    print "AWCM sync message received: ", awcmSyncMessages
    print "Commands queued by AWCM messages: ", awcmCommands
    print "Failed commands: ", failedCommands
    print "Total Connection Fails", totalConnectionFails
    print "Total Peer Resets", totalConnectionResets
    
    print "Average syncs after message: ", meanSyncsAfterMessage
    print "Most syncs after message"
    mostSyncsAfterMessage.reverse()
    for syncs in mostSyncsAfterMessage:
        print syncs, " syncs"
    print "least syncs after message"
    for syncs in leastSyncsAfterMessage:
        print syncs, " syncs"
        
    print "Average syncs per message: ", meanSyncsInMessage
    print "Most syncs in message"
    mostSyncsInMessage.reverse()
    for syncs in mostSyncsInMessage:
        print syncs, " syncs"
    print "least syncs in message"
    for syncs in leastSyncsInMessage:
        print syncs, " syncs"
    
    print "Average time between messages: ", strftime('%H:%M:%S', gmtime(meanTimeBetweenSyncs))
    print "Most time between message"
    mostTimeBetweenSyncs.reverse()
    for time in mostTimeBetweenSyncs:
        print strftime('%H:%M:%S', gmtime(time))
    print "least time between messages"
    for time in leastTimeBetweenSyncs:
        print strftime('%H:%M:%S', gmtime(time))
        
    for failedConnection in connectionResetLogs:
        print failedConnection
        
    