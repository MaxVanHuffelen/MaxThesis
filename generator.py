from multiprocessing import connection
import numpy as np
from queue import PriorityQueue
import dataReader as dr
import event

class Car():
    carParksVisited = None
    timeStartCharging = None
    parkingPlaceID = None
    
    def __init__(self, chargingVolume, connectionTime, parkingPlaceID, carID):
        self.chargingVolume = chargingVolume
        self.connectionTime = connectionTime
        self.parkingPlaceID = parkingPlaceID
        self.carParksVisited = []
        self.amountCharged = 0
        self.carID = carID
        self.carArrivalTime = None

    def __repr__(self):
        return f'Car ID: {self.carID}, chargingVolume: {self.chargingVolume}, connectionTime: {self.connectionTime} parkingPlace: {self.parkingPlaceID}, amountCharged: {self.amountCharged}, carParksVisited: {self.carParksVisited}, arrivalTime: {self.carArrivalTime}'

def generateCar(charging_volume_distributions, connection_time_distributions, carID):
    charging_volumes, charging_probabilities = zip(*charging_volume_distributions)
    connection_times, connection_probabilities = zip(*connection_time_distributions)
    charging_volumes, charging_probabilities, connection_times, connection_probabilities = np.array(charging_volumes), np.array(charging_probabilities), np.array(connection_times), np.array(connection_probabilities)
    
    chargingVolume = np.random.choice(charging_volumes, p=(charging_probabilities/sum(charging_probabilities)))
    min_connection_time_hours = int(chargingVolume/(6*0.7)) #minimum connection time in hours

    connectionTime_hours = np.random.choice(connection_times[min_connection_time_hours:], p=(connection_probabilities[min_connection_time_hours:]/sum(connection_probabilities[min_connection_time_hours:])))
    connectionTime = max(connectionTime_hours * 3600 + np.random.choice(3600), 1 + int(chargingVolume * 3600/(6*0.7)))
    
    randomParkingPlaceID = generateParkingPlace()

    # print(f'generated car with charging volume: {chargingVolume}, connection time: {connectionTime} seconds / {connectionTime/3600} hours')
    return Car(chargingVolume=chargingVolume, connectionTime=connectionTime, parkingPlaceID=randomParkingPlaceID, carID=carID)

def generateSolarValue(timeOfDay, solar_availability_distributions, season='summer'):
    # returns a randomly generated value for available power from a solar panel array at the specified time of day in the specified season (summer/winter)
    timeOfDay = timeOfDay%24
    if season=='summer':
        solar_power = solar_availability_distributions[timeOfDay][2] * 200
    else:
        solar_power = solar_availability_distributions[timeOfDay][1] * 200
    value = np.random.normal(solar_power, 0.15*solar_power)
    #print(f'generated solar power, value: {value}')
    return value 

def generateParkingPlace(already_visited_places = []):
    #Could be improved later
    while(True):
        randomPlace = np.random.choice([1, 2, 3, 4, 5, 6, 7],
                                        p=[0.15, 0.15, 0.15, 0.2, 0.15, 0.1, 0.1])

        parkingPlaceID = str(randomPlace)

        if parkingPlaceID not in already_visited_places:
            return parkingPlaceID



def generateAllEvents(arrival_fractions, charging_volume_distributions, connection_time_distributions, solar_availability_distributions, average_daily_cars=750, timeLength = 24, season='summer'):
    # N.B. timeLength input is in HOURS not in seconds

    generatedEvents = PriorityQueue()

    carID = 0
    # Generate car arrivals
    for t in range(timeLength):
        allMoments = np.random.poisson(average_daily_cars*arrival_fractions[t%24][1]/3600, size=3600)
        newCarsIndices = np.where(allMoments>0)[0] #use this to find the indices in the array where the value is nonzero (i.e. one or more cars arrive)
        for time in newCarsIndices:
            #print(f'Generating car at time {t*3600+time}')
            for i in range(allMoments[time]):
                # Loop is needed in case two cars arrive the very same second.
                generatedEvents.put(event.Event(time=t*3600+time, eventType="carArrives", data=((generateCar(charging_volume_distributions, connection_time_distributions, carID) ) ) ) )
                carID += 1
                    

    # Generate solar events (extend +70 hours as that is how long cars can continue being present)
    for t in range(timeLength+70):
        generatedEvents.put(event.Event(time=t*3600,eventType="solarUpdate", data=((generateSolarValue(t%24, solar_availability_distributions, season) ) ) ) )
    
    #add Simulation end
    generatedEvents.put(event.Event(time = 3600*timeLength, eventType="endSimulation", data=()))
    
    return generatedEvents


if __name__ == "__main__":
    arrival_fractions, charging_volume_distributions, connection_time_distributions, solar_availability_distributions = dr.readCSVs()

    eventsQueue = generateAllEvents(arrival_fractions, charging_volume_distributions, connection_time_distributions, solar_availability_distributions)
    
    # find how many events there are in the queue (for some reason the class PriorityQueue has no len or size attributes :/ )
    i = 0
    while (not eventsQueue.empty()):
        a= eventsQueue.get() #throw away one event
        i+= 1
    print(f'the total amount of generated events is: {i}')