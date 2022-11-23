from distutils.log import error
import event
import state
import generator
import logger
import showPlots
import performanceMeasures
import time
import numpy as np
# Start the simulation
def startSimulation(eventQueue, chargingStrategy = 'base', parkingPlacesWithPanelsID = []):

    # The eventhandlers allow the events to be mapped to their handlers
    eventHandlers = {"carArrives": handleCarArrivalEvent,
                     "carExpectedStopCharging": handleCarExpectedStopChargingEvent,
                     "carLeaves": handleCarLeavesEvent,
                     "carBeginsCharging": handleCarBeginsChargingEvent,
                     "carStopsCharging": handleCarStopsChargingEvent,
                     "carPlannedLeave": handleCarPlannedLeaves,
                     "solarUpdate": handleSolarUpdateEvent,
                     "endSimulation": handleEndSimulation}
    currState = state.createInitialState(chargingStrategy=chargingStrategy, parkingPlacesWithPanelsID=parkingPlacesWithPanelsID)
    assert currState['chargingStrategy'] in {'base', 'price-driven', 'FCFS', 'ELFS'}

    # The event loop
    startTime = time.time()
    while not eventQueue.empty():

        # Get next event and type
        currEvent = eventQueue.get()
        currEventType = currEvent.eventType

        assert currEventType in eventHandlers
        
        # Some events may schedule new events, schedule those here
        # print(currEvent)
        returnEvents = eventHandlers[currEventType](currEvent, currState)

        if returnEvents is None:
            raise Exception(str(currEvent) + " did not return event list")

        for returnEvent in returnEvents:
            eventQueue.put(returnEvent)

        # Log every event for debugging
        state.storeDataPerTimestep(currEvent.time, currState)
        logger.logEvent(currEvent)

        # End the simulation when we encounter the endSimulation event
        if currEventType == "endSimulation":
            break 

    print("Simulation took", time.time() - startTime, "seconds")
    
    return currState

def handleCarPlannedLeaves(currEvent, currState): 
    currCar = currEvent.data

    chargedSinceLastStart = 0
    if currCar.timeStartCharging:
        chargedSinceLastStart = (6/3600) * (currEvent.time - currCar.timeStartCharging)

    totalCharge = currCar.amountCharged + chargedSinceLastStart
    
    # Is finished charging
    if totalCharge >= currCar.chargingVolume:
        logger.logMessage(f'Car {currCar.carID}, succesfully charged')
        return [event.Event(time=currEvent.time, eventType="carLeaves", data=currCar)]
    # Hasn't finished charging, but is busy charging
    else:
        logger.logMessage(
            f'Car {currCar.carID}, not succesfully charged. ERROR in basecase')
        return [event.Event(time=currEvent.time + (currCar.chargingVolume - totalCharge) / (6/3600), eventType="carPlannedLeave", data=currCar)]


def handleCarBeginsChargingEvent(currEvent, currState):
    currCar = currEvent.data
    
    currParkingPlace = currState["parkingPlaces"][currCar.parkingPlaceID]

    currCar.timeStartCharging = currEvent.time
    currParkingPlace.startCharging(currCar)

    # Update the current loads
    updateCableLoads(currState)

    # Calculate how much time to finish charging without interruption
    return [event.Event(time=currEvent.time + (currCar.chargingVolume - currCar.amountCharged) / (6 / 3600), eventType="carExpectedStopCharging", data=currCar)]

def getOverloadedCableIndices(currState):
    returnIndices = []
    cableLoads = currState["cableLoads"]
    for index in range(len(cableLoads)):
        if cableLoads[index] + 6 > 200:
            returnIndices.append(index)

    return returnIndices

def handleCarStopsChargingEvent(currEvent, currState):
    currCar = currEvent.data

    currParkingPlace = currState["parkingPlaces"][currCar.parkingPlaceID]
    currParkingPlace.stopCharging(currCar)

    # Remove the cableloads
    updateCableLoads(currState)

    # Calculate how much was charged
    currCar.amountCharged += (6/3600) * (currEvent.time - currCar.timeStartCharging)
    currCar.timeStartCharging = None

    if currState['chargingStrategy'] == 'base' or currState['chargingStrategy'] == 'price-driven':
        return []
    elif currState['chargingStrategy'] == 'FCFS':
        nextCar = getNextCarFromQueueFCFS(currState)
        #Start scheduling
        if nextCar is not None:
            return [event.Event(time=currEvent.time, eventType="carBeginsCharging", data=nextCar)]
        else:
            return []
    elif currState['chargingStrategy'] == 'ELFS':
        nextCar = getNextCarFromQueueELFS(currState)
        if nextCar is not None:
            return [event.Event(time=currEvent.time, eventType="carBeginsCharging", data=nextCar)]
        else:
            return []
        

def getNextCarFromQueueELFS(currState):

    #First get which parkingPlace we should queue
    priorityList = currState["priorityList"]
    sortedPriorityList = sorted(priorityList, key=lambda x: x[1])

    for currIndex in range(len(sortedPriorityList)):
        
        currCar, _ = sortedPriorityList[currIndex]
        cableIndices = getCablesIndicesForParkingPlace(currCar.parkingPlaceID, currState)

        # Load not possible
        if not isAdditionalChargePossibleIndices(cableIndices, currState):
            continue
        

        toBeRemoved = sortedPriorityList[currIndex]

        priorityList.remove(toBeRemoved)        
        return currCar

    return None

def getNextCarFromQueueFCFS(currState):

    #First get which parkingPlace we should queue
    parkingPlaces = list(currState["parkingPlaces"].values())
    sortedParkingPlaces = sorted(parkingPlaces, reverse=True, key=lambda x: x.queue.qsize())

    for parkingPlace in sortedParkingPlaces:
        if parkingPlace.queue.qsize() == 0:
            break

        cableIndices = getCablesIndicesForParkingPlace(parkingPlace.ID, currState)

        # Load not possible
        if not isAdditionalChargePossibleIndices(cableIndices, currState):
            continue

        return parkingPlace.queue.get()

    return None





def handleCarArrivalEvent(currEvent, currState):
    currCar = currEvent.data
    currCar.carParksVisited.append(currCar.parkingPlaceID)

    currParkingPlace = currState["parkingPlaces"][currCar.parkingPlaceID]
    if currParkingPlace.isFull():
        return handleCarPlaceFull(currEvent, currState)

    state.storeServiced(currEvent.time, "served")

    currCar.carArrivalTime = currEvent.time
    currParkingPlace.arriveAtCharger(currCar)
    # Use the carBeginsChargingEvent for later addition of the not base cases. Also schedule the planned leave
    if currState['chargingStrategy'] == 'base':
        return [event.Event(time=currEvent.time, eventType="carBeginsCharging", data=currCar),
            event.Event(time=currEvent.time + currCar.connectionTime, eventType="carPlannedLeave", data=currCar)]
    elif currState['chargingStrategy'] == 'price-driven':
        return [event.Event(time=findCheapestTime(currEvent, currState), eventType="carBeginsCharging", data=currCar),
            event.Event(time=currEvent.time + currCar.connectionTime, eventType="carPlannedLeave", data=currCar)]
    elif currState['chargingStrategy'] == 'FCFS' or currState['chargingStrategy'] == 'ELFS':
        if isAdditionalChargePossibleEvent(currEvent, currState): # How to make this happen right away?
            return [event.Event(time=currEvent.time, eventType="carBeginsCharging", data=currCar),
            event.Event(time=currEvent.time + currCar.connectionTime, eventType="carPlannedLeave", data=currCar)]
        else:
            if currState['chargingStrategy'] == 'FCFS':
                currState["parkingPlaces"][currCar.parkingPlaceID].queue.put(currCar)
            else:
                plannedLeave = currCar.carArrivalTime + currCar.connectionTime
                latestStart = plannedLeave - currCar.chargingVolume * 3600 / 6
                priority =  currCar.chargingVolume * 6 / currCar.connectionTime

                currState["priorityList"].append((currCar, priority))
            return [event.Event(time=currEvent.time + currCar.connectionTime, eventType="carPlannedLeave", data=currCar)]


def noCablesOverloaded(currState):
    return isAdditionalChargePossibleIndices(range(len(currState["cableLoads"])), currState)

def isAdditionalChargePossibleIndices(cableIDs, currState):
    for index in cableIDs:
        cableLoads = currState["cableLoads"]
        if cableLoads[index] + 6 > 200:
            return False

    return True

def isAdditionalChargePossibleEvent(currEvent, currState):
    parkingPlaceID = currEvent.data.parkingPlaceID
    cableIDs = getCablesIndicesForParkingPlace(parkingPlaceID, currState)
    
    return isAdditionalChargePossibleIndices(cableIDs, currState)



def updateCableLoads(currState):
    parkingPlaces = currState["parkingPlaces"]
    def calcPowerDrawn(parkingPlaceID):
        return 6 * len(parkingPlaces[parkingPlaceID].currentlyCharging) - parkingPlaces[parkingPlaceID].currSolarEnergy
    d1 = calcPowerDrawn("1")
    d2 = calcPowerDrawn("2")
    d3 = calcPowerDrawn("3")
    d4 = calcPowerDrawn("4")
    d5 = calcPowerDrawn("5")
    d6 = calcPowerDrawn("6")
    d7 = calcPowerDrawn("7")
    
    newCableLoads = [0]*9
    newCableLoads[0] = abs(d1 + d2 + d3)
    newCableLoads[1] = abs(d1)
    newCableLoads[2] = abs(d2)
    newCableLoads[3] = abs(d3)
    newCableLoads[4] = abs(d4 + d5 + d6 + d7)
    newCableLoads[5] = abs(d7)
    newCableLoads[6] = abs(d5 + d6)
    newCableLoads[7] = abs(d5)
    newCableLoads[8] = abs(d6) 
    currState["cableLoads"] = newCableLoads




def getCablesIndicesForParkingPlace(parkingPlaceID, currState):
    if parkingPlaceID == "1":
        return [0, 1]
    if parkingPlaceID == "2":
        return [0, 2]
    if parkingPlaceID == "3":
        return [0, 3]
    if parkingPlaceID == "4":
        return [4]
    if parkingPlaceID == "5":
        return [4, 6, 7]
    if parkingPlaceID == "6":
        return [4, 6, 8]
    if parkingPlaceID == "7":
        return [4, 5]

    raise Exception("Not possible in getCablesIndices")


# NOT AN EVENT, but a helper function for clarity
def findCheapestTime(currEvent, currState):

    def findCost(startTime, duration):
        startTime = startTime % (24*3600)
        endTime = startTime + duration
        cost = 0
        notDone = True 
        while notDone:
            if 0 <= startTime < 8*3600:
                notDone = 8*3600 < endTime 
                cost += 16 * (min(endTime, 8*3600) - startTime) * 6/3600
                startTime = 8*3600
            elif 8*3600 <= startTime < 16*3600:
                notDone = 16*3600 < endTime 
                cost += 18 * (min(endTime, 16*3600) - startTime) * 6/3600
                startTime = 16*3600
            elif 16*3600 <= startTime < 20*3600:
                notDone = 20*3600 < endTime 
                cost += 22 * (min(endTime, 20*3600) - startTime) * 6/3600
                startTime = 20*3600
            elif 20*3600 <= startTime < 24*3600:
                notDone = 24*3600 < endTime 
                cost += 20 * (min(endTime, 24*3600) - startTime) * 6/3600
                startTime = 0
                endTime -= 24*3600
        return cost

    currCar = currEvent.data
    chargingTime = currCar.chargingVolume /(6/3600)
    firstTime = currEvent.time
    lastTime = firstTime + currCar.connectionTime - chargingTime

    timesToCheck = [firstTime, lastTime] 
    generateMoreTimes = True 
    days = firstTime // (24*3600)
    while generateMoreTimes:
        times = [days*24*3600, 
        days*24*3600 + 8*3600, 
        days*24*3600 + 8*3600 - chargingTime, 
        days*24*3600 + 16*3600, 
        days*24*3600 + 16*3600 - chargingTime, 
        days*24*3600 + 20*3600, 
        days*24*3600 + 20*3600 - chargingTime, 
        days*24*3600 + 24*3600 - chargingTime]

        for time in times:
            if firstTime < time < lastTime:
                timesToCheck.append(time)
        if days + 20*3600 > lastTime:
            generateMoreTimes = False 
        days += 1

    lowestCost = currCar.chargingVolume * 22 + 1 #Higher than the highest possible cost
    cheapestStartTime = None

    for time in timesToCheck:
        cost = findCost(time,chargingTime)
        if cost < lowestCost:
            lowestCost = cost
            cheapestStartTime = time

    return cheapestStartTime

# NOT AN EVENT, but an helper function for clarity
def handleCarPlaceFull(currEvent, currState):
    currCar = currEvent.data


    logger.logMessage("Car Place full, moving to another")
    if currEvent.time > 2 * 24 * 3600 and currEvent.time < 9 * 24 * 3600:
        currState["carsAtFullParking"] += 1

    # As specified in assignment, stop visiting
    if len(currCar.carParksVisited) == 3:
        logger.logMessage("Too many Car Places (3) full in a row")
        if currEvent.time > 2 * 24 * 3600 and currEvent.time < 9 * 24 * 3600:
            currState["carsUnableCharged"] += 1

            state.storeServiced(currEvent.time, "notserved")
        return []


    # Get new parking place, and schedule a new event after certain amount of time
    currCar.parkingPlaceID = generator.generateParkingPlace(
        currCar.carParksVisited)

    return [event.Event(time=currEvent.time, eventType="carArrives", data=currCar)]


# Occurs when the car has finished charging
def handleCarLeavesEvent(currEvent, currState):
    currCar = currEvent.data

    currParkingPlace = currState["parkingPlaces"][currCar.parkingPlaceID]
    currParkingPlace.leaveCharger(currCar)

    if currEvent.time > 2 * 24 * 3600 and currEvent.time < 9 * 24 * 3600:
        currState["carsCharged"] += 1

    deltaTime = currEvent.time - currCar.carArrivalTime
    delay = max(0, deltaTime - currCar.connectionTime)

    # if(delay > 0):
    #     print(currEvent.time, currCar)
    state.storeDelay(currEvent.time, delay)

    return []

def handleSolarUpdateEvent(currEvent, currState):

    #Set new values for solar panels
    for currParkingPlaceID in currState["parkingPlaceIDs"]:
        currParkingPlace = currState["parkingPlaces"][currParkingPlaceID]
        if currParkingPlaceID in currState["parkingPlacesWithPanelsID"]:
            currParkingPlace.setSolarPower(currEvent.data)
        else:
            currParkingPlace.setSolarPower(0)

    updateCableLoads(currState)
    return []

def handleCarExpectedStopChargingEvent(currEvent, currState):
    currCar = currEvent.data 
    if currCar.timeStartCharging:
        chargedSinceLastStart = (currEvent.time - currCar.timeStartCharging) * (6/3600)
        if currCar.amountCharged + chargedSinceLastStart >= currCar.chargingVolume:
            return [event.Event(time=currEvent.time, eventType="carStopsCharging", data=currCar)]
        else:
            return [event.Event(time=currEvent.time + (currCar.chargingVolume - currCar.amountCharged - chargedSinceLastStart) / (6 / 3600), eventType="carExpectedStopCharging", data=currCar)]
    return []

def handleEndSimulation(currEvent, currState):
    print("----- ENDING SIMULATION -----")
    print(f'amount of cars serviced: {currState["carsCharged"]}')
    print(f'amount of cars unable to be serviced: {currState["carsUnableCharged"]}')
    print(f'amount of times a car arrived at a full parking place: {currState["carsAtFullParking"]}')


    
    #showPlots.printMaximumCableLoad(currState)
    #showPlots.print10OverloadPercentage(currState)
    return []