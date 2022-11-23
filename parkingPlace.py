import queue

class ParkingPlace():
    maxNumberCharginStations: int
    currSolarEnergy: float

    def __init__(self, maxNumberCharginStations, ID):
        self.maxNumberCharginStations = maxNumberCharginStations
        self.currentlyParked = {}
        self.currentlyCharging = {}
        self.ID = ID

        self.queue = None

    def startCharging(self, car):
        assert len(self.currentlyCharging) + 1 <= len(self.currentlyParked)
        self.currentlyCharging[car] = True

    def stopCharging(self, car):
        assert len(self.currentlyCharging) > 0
        
        if car not in self.currentlyCharging:
            print("CAR", car)
            print(self.currentlyCharging)
        
        assert car in self.currentlyCharging


        del self.currentlyCharging[car]

    def arriveAtCharger(self, car):
        assert len(self.currentlyParked) <= self.maxNumberCharginStations
        self.currentlyParked[car] = True

    def leaveCharger(self, car):
        assert len(self.currentlyParked)
        assert car in self.currentlyParked
        del self.currentlyParked[car]

    def setSolarPower(self, newVal):
        self.currSolarEnergy = newVal
        return

    def isFull(self):
        return self.maxNumberCharginStations == len(self.currentlyParked)

#Creates the parking places, using strings for the IDS
def createParkingPlaces(chargingStrategy):
    chargingStationAmounts = [60, 80, 60, 70, 60, 60, 50]
    parkingPlaces = {}
    for index in range(7):
        parkingPlaceIndex = str(index+1)
        parkingPlaces[parkingPlaceIndex] = ParkingPlace(maxNumberCharginStations=chargingStationAmounts[index], ID=parkingPlaceIndex)

        if chargingStrategy == "FCFS":
            parkingPlaces[parkingPlaceIndex].queue = queue.Queue()

    return parkingPlaces
