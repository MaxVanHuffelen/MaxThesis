import matplotlib.pyplot as plt
import numpy as np
import performanceMeasures


def showPlots(currState):
    # showParkingDensity(currState)
    # showChargeDensity(currState)
    # showOverloadDensity(currState)
    return


def readFile(path):

    returnTimestamps = []
    returnDataPoints = []    

    timestamps = []
    dataPoints = []
    with open(path, "r") as file:
        lines = file.readlines()

        for line in lines[1:]:
            if(line[0] == '-'):
                print("Results of new simulation")
                returnTimestamps.append(timestamps)
                returnDataPoints.append(dataPoints)

                timestamps = []
                dataPoints = []
            else:
                tokens = line.split(',')
                tokens = [float(curr) for curr in tokens]
                timestamps.append(tokens[0])
                dataPoints.append(tokens[1:])

    return returnTimestamps, returnDataPoints


def printDelays():
    with open("./performances/delays.txt", "r") as file:
        lines = file.readlines()


    allData = []
    currSimulationData = []
    for line in lines[1:]:
        if line[0] == '-':
            allData.append(currSimulationData)
            currSimulationData = []
        else:
            currSimulationData.append(float(line))
    
    for parsed in allData:
        parsed = np.array(parsed)
        print(parsed)
        print("Minimum delay:", np.min(parsed))
        print("Maximum delay:", np.max(parsed))
        print("Average delay:", np.mean(parsed))
        print("Percentage with delay:", 100 * parsed[parsed!=0.0].shape[0] / parsed.shape[0])
        print("Percentage without delay:", 100 * parsed[parsed==0.0].shape[0] / parsed.shape[0])
        

def showParkingDensity(currState):

    allTimestamps, allData = readFile('./performances/parkingDensity.txt')
    maximumParkingAmount = [currState["parkingPlaces"][currID].maxNumberCharginStations for currID in currState["parkingPlaceIDs"] ]
    
    for simulationIndex in range(len(allTimestamps)):
        timestamps = allTimestamps[simulationIndex]
        data = allData[simulationIndex]

        for i in range(7):
            parkingID = str(i + 1)

            xData = timestamps
            yData = [dataPoint[i] for dataPoint in data]

            plt.plot(xData, yData)
            plt.axhline(y=maximumParkingAmount[i], color='r', linestyle='-')
            
            plt.title("Parking Density for parking place: " + parkingID + " for simulation run: " + str(simulationIndex))
            plt.show()


def showChargeDensity(currState):

    allTimestamps, allData = readFile('./performances/chargingDensity.txt')
    maximumParkingAmount = [currState["parkingPlaces"][currID].maxNumberCharginStations for currID in currState["parkingPlaceIDs"] ]
    
    for simulationIndex in range(len(allTimestamps)):
        timestamps = allTimestamps[simulationIndex]
        data = allData[simulationIndex]
        for i in range(7):
            parkingID = str(i + 1)

            xData = timestamps
            yData = [dataPoint[i] for dataPoint in data]

            plt.plot(xData, yData)
            plt.axhline(y=maximumParkingAmount[i], color='r', linestyle='-')
            plt.title("Charging Density for parking place: " + parkingID + " for simulation run: " + str(simulationIndex))
            plt.show()

def showOverloadDensity(currState):

    allTimestamps, allData = readFile('./performances/powerDensity.txt')

    for simulationIndex in range(len(allTimestamps)):
        timestamps = allTimestamps[simulationIndex]
        data = allData[simulationIndex]
        powerPerCablePerStep = np.array(data).T

        for index in range(powerPerCablePerStep.shape[0]):

            xData = timestamps
            yData = powerPerCablePerStep[index]

            plt.plot(xData, yData)
            plt.axhline(y=200, color='r', linestyle='-')
            plt.title("Used capacity for cable" + str(index)+ " for simulation run: " + str(simulationIndex))
            plt.show()


        xData = timestamps
        yData = powerPerCablePerStep[0] + powerPerCablePerStep[4]
        plt.plot(xData, yData)
        plt.axhline(y=1000, color='r', linestyle='-')
        plt.title("Used capacity for the transformer")
        plt.show()


def printMaximumCableLoad(currState):
    allTimestamps, allCablePower = readFile('./performances/powerDensity.txt')
    
    print(np.array(allCablePower).shape)
    
    for simulationIndex in range(len(allTimestamps)):
        timestamps = allTimestamps[simulationIndex]
        cablePower = allCablePower[simulationIndex]
        cablePower = np.array(cablePower).T

        
        for i in range(9):
            cableName = "cable" + str(i)
            print("Max value for", cableName, "is: ", max(cablePower[i]) + " for simulation run: " + str(simulationIndex))

def print10OverloadPercentage(currState):
    allTimestamps, allCablePower = readFile('./performances/powerDensity.txt')

    for simulationIndex in range(len(allTimestamps)):
        timestamps = allTimestamps[simulationIndex]
        cablePower = allCablePower[simulationIndex]
        cablePower = np.array(cablePower).T

        finalTimestep = timesteps[-1]


        for i in range(9):
            atLeast10 = 0
            max10 = 0
            noOverload = 0

            # Calculate how long the overloads last
            for j in range(len(timesteps) - 1):
                if cablePower[i][j] >= 1.1 * 200:
                    atLeast10 += timesteps[j+1] - timesteps[j]
                elif cablePower[i][j] >= 1 * 200: 
                    max10 += timesteps[j+1] - timesteps[j]
                else:
                    noOverload += timesteps[j+1] - timesteps[j]


            #Divide to get the fraction
            atLeast10 /= finalTimestep
            max10 /= finalTimestep
            noOverload /= finalTimestep
            
            print("For cable", str(i), "at least 10% overload:", atLeast10, "at most 10% overload", max10, "and no overload", noOverload + " for simulation run: " + str(simulationIndex))

            assert abs(atLeast10 + max10 + noOverload - 1.0) < 0.01
