'''
Created on Mar 6, 2016

@author: perron
'''
from __builtin__ import True

from sys import argv
from os import path

awcmIterations = []
awcmSyncMessages = 0
awcmCommands = 0
failedCommands = 0
mean = 0
fastestInterations = []
slowestInterations = []


'''
Read in the file and copy out the necessary lines for analysis
'''


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
        

def importAWCMLog(awcmLogFile):
    global awcmIterations
    global failedCommands
    global awcmSyncMessages
    global awcmCommands
    
    awcmSyncQueue = 0
    commandQueue = 0
    executingCheckForCommands = False
    finishedCommand = False
    
    log = awcmLogFile.readline()
    while log is not None and log != "": #The first line (index 0) is the heading
        if "Incoming AWCM message" in log:
            awcmSyncMessages+=1
        if "Sending AWCM Sync broadcast" in log:
            awcmCommands+=1
            awcmSyncQueue+=1
        if "posting check for commands runnable" in log and awcmSyncQueue > 0:
            awcmSyncQueue-=1
            commandQueue+=1
        if "Scheduler.checkForCommands: command runnable  entered" in log and executingCheckForCommands and not finishedCommand:
            # This means something went wrong and a previous command did not finish
            failedCommands+=1
        if "Scheduler.checkForCommands: command runnable  entered" in log and commandQueue > 0:
            commandQueue-=1
            executingCheckForCommands = True
        if "Scheduler.checkForCommands: command runnable  exited" in log and executingCheckForCommands:
            executingCheckForCommands = False
            finishedCommand = True
        if "Scheduler.checkForCommands: Command Queue Callback" in log and finishedCommand:
            finishedCommand = False
            logMillisecond = extractMilliseconds(log)
            if(logMillisecond is not None):
                awcmIterations.append(logMillisecond)
        
        log = awcmLogFile.readline()


def processAWCMInterations():
    global awcmIterations
    global mean
    global fastestInterations
    global slowestInterations
    
    awcmIterations.sort()
    mean = sum(awcmIterations)/len(awcmIterations)
    fastestInterations = awcmIterations[0:20]
    slowestInterations = awcmIterations[len(awcmIterations)-20:len(awcmIterations)]

'''
def writeCompanyFile():
    global companies
    companyFile = open("/Users/perron/Documents/YellowBird/companylist.csv", mode='w')
    for company in companies:
        companyStr = company[0]+","+company[1]+","+company[2]+"\n"
        companyFile.write(companyStr)
    companyFile.close()
'''

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
    mean
    fastestInterations
    slowestInterations
    '''
   
    print "AWCM sync message received: ", awcmSyncMessages
    print "Commands queued by AWCM messages: ", awcmCommands
    print "Failed commands: ", failedCommands
    print "Average execution (from queued to completion): ", mean, " ms"
    print "Fastest executions"
    for time in fastestInterations:
        print time, " ms"
    slowestInterations.reverse()
    print "Slowest executions "
    for time in slowestInterations:
        print time, " ms"
        
    