
import parkingPlace
import shutil

#Create the initial state with some variables
def createInitialState(chargingStrategy = 'base', parkingPlacesWithPanelsID = []):
    state = {}
    state["parkingPlaceIDs"] = ["1", "2", "3", "4", "5", "6", "7"]
    state["parkingPlacesWithPanelsID"] = parkingPlacesWithPanelsID
    state["parkingPlaces"] = parkingPlace.createParkingPlaces(chargingStrategy)
    state["carsCharged"] = 0
    state["carsUnableCharged"] = 0
    state["carsAtFullParking"] = 0
    state["chargingStrategy"] = chargingStrategy #This should be 'base', 'price-driven', 'FCFS' or 'ELFS'
    state["cableLoads"] = [0] * 9

    if chargingStrategy == 'ELFS':
        state["priorityList"] = []

    assert state["chargingStrategy"] in {'base', 'price-driven', 'FCFS', 'ELFS'}
    for parkingPlaceID in state["parkingPlacesWithPanelsID"]:
        assert parkingPlaceID in state["parkingPlaceIDs"]

    return state

# Clear the files in order to use them for this simulation
def clearPerformanceFiles():
    file = open('./performances/parkingDensity.txt',"w")
    file.close()

    file = open('./performances/chargingDensity.txt',"w")
    file.close()

    file = open('./performances/powerDensity.txt',"w")
    file.close()

    file = open('./performances/delays.txt',"w")
    file.close()

    file = open('./performances/serviced.txt',"w")
    file.close()


def movePerformanceFiles(newRoot):
    shutil.move('./performances/parkingDensity.txt', f'./{newRoot}/parkingDensity.txt')
    shutil.move('./performances/powerDensity.txt', f'./{newRoot}/powerDensity.txt')
    shutil.move('./performances/chargingDensity.txt', f'./{newRoot}/chargingDensity.txt')
    shutil.move('./performances/delays.txt', f'./{newRoot}/delays.txt')
    shutil.move('./performances/serviced.txt', f'./{newRoot}/serviced.txt')
    # shutil.move('./performances/misc.txt', f'./{newRoot}/misc.txt')

# Store the data for the timesteps
def storeDataPerTimestep(currTimestamp, state):

    if(currTimestamp < 2 * 24 * 3600):
        return

    if(currTimestamp > 9 * 24 * 3600):
        return


    parkingIDS = state["parkingPlaceIDs"]
    allcurrentlyParked = [len(state["parkingPlaces"][currID].currentlyParked) for currID in parkingIDS]
    allcurrentlyCharging = [len(state["parkingPlaces"][currID].currentlyCharging) for currID in parkingIDS]
    allPowerDrawn = state["cableLoads"]

    #Append the data to files
    with open('./performances/parkingDensity.txt', "a") as myfile:     
        myfile.write(str(currTimestamp) + "," + ",".join(map(str,allcurrentlyParked)) + "\n")

    with open('./performances/chargingDensity.txt', "a") as myfile:     
        myfile.write(str(currTimestamp) + "," + ",".join(map(str,allcurrentlyCharging)) + "\n")

    with open('./performances/powerDensity.txt', "a") as myfile:  
        myfile.write(str(currTimestamp) + "," + ",".join(map(str,allPowerDrawn)) + "\n")

    
def storeServiced(currTimestamp, servedOrNot):

    if(currTimestamp < 2 * 24 * 3600):
        return

    if(currTimestamp > 9 * 24 * 3600):
        return

    with open('./performances/serviced.txt', "a") as myfile:     
        myfile.write(str(currTimestamp) + "," + servedOrNot + "\n")

def storeDelay(currTimestamp, delay):
    
    if(currTimestamp < 2 * 24 * 3600):
        return

    if(currTimestamp > 9 * 24 * 3600):
        return
    
    with open('./performances/delays.txt', "a") as myfile:     
        myfile.write(str(currTimestamp) + "," + str(delay) + "\n")


def storeSimulationHeader(i):
    #Append the data to files
    with open('./performances/parkingDensity.txt', "a") as myfile:     
        myfile.write("-----Simulation " + str(i) + "-----" + "\n")

    with open('./performances/chargingDensity.txt', "a") as myfile:     
        myfile.write("-----Simulation " + str(i) + "-----" + "\n")

    with open('./performances/powerDensity.txt', "a") as myfile:     
        myfile.write("-----Simulation " + str(i) + "-----" + "\n")

    with open('./performances/delays.txt', "a") as myfile:     
        myfile.write("-----Simulation " + str(i) + "-----" + "\n")

    with open('./performances/serviced.txt', "a") as myfile:     
        myfile.write("-----Simulation " + str(i) + "-----" + "\n")

#Print the results after the simulation
def printResults(currState):
    print(currState["carsCharged"], "cars were charged")
    print(currState["carsUnableCharged"], "cars were unable to be charged")
    print(currState["carsAtFullParking"], "times cars arrived at a full parking place")