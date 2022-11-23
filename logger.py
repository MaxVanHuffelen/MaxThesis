path = "./logs/log.txt"

def clearLog():
    file = open(path,"w")
    file.close()

def logEvent(currEvent):
    logging = "Event: {eventType} at time {eventTime} with data {data}"
    message = logging.format(eventType=currEvent.eventType, eventTime=currEvent.time, data=currEvent.data)
    logMessage(message)
    
def logMessage(message):
    with open(path, "a") as myfile:     
        myfile.write(message + "\n")
