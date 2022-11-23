from generator import generateAllEvents
import dataReader as dr
import event
import matplotlib.pyplot as plt
import numpy as np


# Show the distribution of car arrivals
def testCarArrivals():
    # Generate the events
    hoursAmount = 24 * 14

    arrival_fractions, charging_volume_distributions, connection_time_distributions, solar_availability_distributions = dr.readCSVs()
    eventsQueue = generateAllEvents(arrival_fractions, charging_volume_distributions,
                                    connection_time_distributions, solar_availability_distributions, timeLength=hoursAmount)

    # Get all the arrival times
    carArrivalTimes = []
    while (not eventsQueue.empty()):
        a = eventsQueue.get()  # get current event
        if a.eventType == "carArrives":
            carArrivalTimes.append(a.time)

    # Plot the arrival times in a histogram
    plt.hist(np.array(carArrivalTimes) / 3600, density=True, bins=hoursAmount)
    plt.show()


# Calculate average connection time
def testCarConnectionTimes():
    # Generate the events
    arrival_fractions, charging_volume_distributions, connection_time_distributions, solar_availability_distributions = dr.readCSVs()
    eventsQueue = generateAllEvents(arrival_fractions, charging_volume_distributions,
                                    connection_time_distributions, solar_availability_distributions)

    #Get the connection times
    carConnectionTimes = []
    while (not eventsQueue.empty()):
        a = eventsQueue.get()  # get current event
        if a.eventType == "carArrives":
            carConnectionTimes.append(a.data.connectionTime)
    carConnectionTimes = np.array(carConnectionTimes)
    print("Mean", np.mean(carConnectionTimes) / 3600)
    print("Max", np.max(carConnectionTimes) / 3600)


def main():
    testCarConnectionTimes()
        


if __name__ == "__main__":
    main()
