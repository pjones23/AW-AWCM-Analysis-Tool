'''
Created on Mar 7, 2016

@author: perron
'''
from __builtin__ import True

from sys import argv
from os import path
from time import strptime, strftime, gmtime
from calendar import timegm

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

commandsPosted = 0
commandsExecuted = 0
commandsCompleted = 0
timeToDequeue = []
meanTimeToDequeue = 0
mostTimeToDequeue = []
leastTimeToDequeue = []
timeToExecute = []
meanTimeToExecute = 0
mostTimeToExecute = []
leastTimeToExecute = []
timeToComplete = []
meanTimeToComplete = 0
mostTimeToComplete = []
leastTimeToComplete = []

queuedIds = []
executingIds = []
completedIds = []

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

def extractRunnableUUID(line):
    if "id:" not in line:
        return None
    splitLine = line.split(" ")
    uuid = None
    for wordIndex in range(len(splitLine)-1):
        if "id:" in splitLine[wordIndex]:
            uuid = splitLine[wordIndex+1].strip()
            break
            
    return uuid

def extractMilliseconds(line):
    if "milliseconds" not in line:
        return None
    splitLine = line.split(" ")
    millisecond = None
    for word in splitLine[::-1]:
        try:
            millisecond = int(word.strip())
            break
        except ValueError:
            millisecond = None
            
    return millisecond

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
    
    global timeToDequeue
    global timeToExecute
    global timeToComplete
    
    global queuedIds
    global executingIds
    global completedIds
    
    tempSyncsAfterMessage = 0
    processingMessage = False
    previousAWCMTime = None
    currentIP = "None"
    
    awcmSyncQueue = 0
    commandQueue = 0
    executingCheckForCommands = False
    finishedCommand = False
    global commandsPosted
    global commandsExecuted
    global commandsCompleted
    
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
            else:
                timeSinceLastSince = messageTime - previousAWCMTime
                timeBetweenSyncs.append(timeSinceLastSince)
                previousAWCMTime = messageTime
        elif "Sending AWCM Sync broadcast" in log:
            awcmCommands+=1
            awcmSyncQueue+=1
            tempSyncsAfterMessage+=1
            if processingMessage:
                awcmSyncsAfterMessage.append(tempSyncsAfterMessage)
                tempSyncsAfterMessage = 0
                processingMessage = False
        elif "posting check for commands runnable" in log and awcmSyncQueue > 0:
            runnableUUID = extractRunnableUUID(log)
            if(runnableUUID is not None):
                queuedIds.append(runnableUUID)
            awcmSyncQueue-=1
            commandQueue+=1
            commandsPosted+=1
        elif "Scheduler.checkForCommands: command runnable" in log and "entered" in log and executingCheckForCommands and not finishedCommand:
            # This means something went wrong and a previous command did not finish
            failedCommands+=1
            runnableUUID = extractRunnableUUID(log)
            if(runnableUUID is not None):
                if runnableUUID in queuedIds:
                    queuedIds.remove(runnableUUID)
                executingIds.append(runnableUUID)
        elif "Scheduler.checkForCommands: command runnable" in log and "entered" in log and commandQueue > 0:
            commandQueue-=1
            executingCheckForCommands = True
            runnableUUID = extractRunnableUUID(log)
            if(runnableUUID is not None):
                if runnableUUID in queuedIds:
                    queuedIds.remove(runnableUUID)
                executingIds.append(runnableUUID)
        elif "time took to dequeue" in log and len(executingIds) > 0:
            logMillisecond = extractMilliseconds(log)
            if(logMillisecond is not None):
                timeToDequeue.append(logMillisecond)
        elif "time to execute command runnable" in log and len(executingIds) > 0:
            logMillisecond = extractMilliseconds(log)
            if(logMillisecond is not None):
                timeToExecute.append(logMillisecond)
        elif "Scheduler.checkForCommands: command runnable" in log and "exited" in log and executingCheckForCommands:
            executingCheckForCommands = False
            finishedCommand = True
            commandsExecuted+=1
            runnableUUID = extractRunnableUUID(log)
            if(runnableUUID is not None):
                if runnableUUID in executingIds:
                    executingIds.remove(runnableUUID)
                completedIds.append(runnableUUID)
        elif "Scheduler.checkForCommands: Command Queue Callback" in log and finishedCommand:
            finishedCommand = False
            commandsCompleted+=1
            logMillisecond = extractMilliseconds(log)
            if(logMillisecond is not None):
                timeToComplete.append(logMillisecond)
                
            runnableUUID = extractRunnableUUID(log)
            if(runnableUUID is not None):
                if runnableUUID in completedIds:
                    completedIds.remove(runnableUUID)
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
    
    global timeToDequeue
    global meanTimeToDequeue
    global mostTimeToDequeue
    global leastTimeToDequeue
    
    global timeToExecute
    global meanTimeToExecute
    global mostTimeToExecute
    global leastTimeToExecute
    
    global timeToComplete
    global meanTimeToComplete
    global mostTimeToComplete
    global leastTimeToComplete
    
    topNum = 20
    
    awcmSyncsAfterMessage.sort()
    meanSyncsAfterMessage = sum(awcmSyncsAfterMessage)/len(awcmSyncsAfterMessage)
    leastSyncsAfterMessage = awcmSyncsAfterMessage[0:topNum]
    mostSyncsAfterMessage = awcmSyncsAfterMessage[len(awcmSyncsAfterMessage)-topNum:len(awcmSyncsAfterMessage)]
    
    awcmSyncsInMessage.sort()
    meanSyncsInMessage = sum(awcmSyncsInMessage)/len(awcmSyncsInMessage)
    leastSyncsInMessage = awcmSyncsInMessage[0:topNum]
    mostSyncsInMessage = awcmSyncsInMessage[len(awcmSyncsInMessage)-topNum:len(awcmSyncsInMessage)]
    
    timeBetweenSyncs.sort()
    meanTimeBetweenSyncs = sum(timeBetweenSyncs)/len(timeBetweenSyncs)
    leastTimeBetweenSyncs = timeBetweenSyncs[0:topNum]
    mostTimeBetweenSyncs = timeBetweenSyncs[len(timeBetweenSyncs)-topNum:len(timeBetweenSyncs)]
    
    timeToDequeue.sort()
    meanTimeToDequeue = sum(timeToDequeue)/len(timeToDequeue)
    leastTimeToDequeue = timeToDequeue[0:topNum]
    mostTimeToDequeue = timeToDequeue[len(timeToDequeue)-topNum:len(timeToDequeue)]
    
    timeToExecute.sort()
    meanTimeToExecute = sum(timeToExecute)/len(timeToExecute)
    leastTimeToExecute = timeToExecute[0:topNum]
    mostTimeToExecute = timeToExecute[len(timeToExecute)-topNum:len(timeToExecute)]
    
    timeToComplete.sort()
    meanTimeToComplete = sum(timeToComplete)/len(timeToComplete)
    leastTimeToComplete = timeToComplete[0:topNum]
    mostTimeToComplete = timeToComplete[len(timeToComplete)-topNum:len(timeToComplete)]

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
    commandsPosted
    commandsExecuted
    commandsCompleted
    queuedIds
    executingIds
    completedIds
    mean awcmSyncsAfterMessage
    mostSyncsAfterMessage
    leastSyncsAfterMessage
    mean awcmSyncsInMessage
    mostSyncsInMessage
    leastSyncsInMessage
    mean TimeBetweenSyncs
    mostTimeBetweenSyncs
    leastTimeBetweenSyncs
    meanTimeToDequeue
    mostTimeToDequeue
    leastTimeToDequeue
    timeToExecute
    meanTimeToExecute
    mostTimeToExecute
    leastTimeToExecute
    timeToComplete
    meanTimeToComplete
    mostTimeToComplete
    leastTimeToComplete
    '''
   
    print "AWCM sync message received: ", awcmSyncMessages
    print "Commands queued by AWCM messages: ", awcmCommands
    print "Failed commands: ", failedCommands
    print "Commands posted by scheduler", commandsPosted
    print "Commands executed", commandsExecuted
    print "Commands completed", commandsCompleted
    print "Commands left in queued ", len(queuedIds)
    print "Commands left in executing ", len(executingIds)
    print "Commands left in completed ", len(completedIds)
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
        
    print "Average dequeue time: ", meanTimeToDequeue, " ms"
    print "Most dequeue time"
    mostTimeToDequeue.reverse()
    for time in mostTimeToDequeue:
        print time, " ms"
    print "least dequeue time"
    for time in leastTimeToDequeue:
        print time, " ms"
        
    print "Average execution time: ", meanTimeToExecute, " ms"
    print "Most execution time"
    mostTimeToExecute.reverse()
    for time in mostTimeToExecute:
        print time, " ms"
    print "least execution time"
    for time in leastTimeToExecute:
        print time, " ms"
        
    print "Average completion time: ", meanTimeToComplete, " ms"
    print "Most completion time"
    mostTimeToComplete.reverse()
    for time in mostTimeToComplete:
        print time, " ms"
    print "least completion time"
    for time in leastTimeToComplete:
        print time, " ms"
        
    for failedConnection in connectionResetLogs:
        print failedConnection
        
