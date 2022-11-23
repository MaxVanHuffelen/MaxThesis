import csv
# import numpy as np

def readCSVs():
    root_path = "." #'D:/University - Utrecht/Q4 Optimization for Sustainability/Optimization-for-sustainability'
    path_arrival_hours = '/data/arrival_hours.csv'
    path_charging_volume = '/data/charging_volume.csv'
    path_connection_time = '/data/connection_time.csv'
    path_solar = '/data/solar.csv'
    
    def readPath(root, path):
        with open(root + path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')

            return [castToValue(row) for row in csv_reader]


    return readPath(root_path, path_arrival_hours), readPath(root_path, path_charging_volume), readPath(root_path, path_connection_time), readPath(root_path, path_solar)

def castToValue(row):
    if len(row) == 2:
        return [int(row[0]), float(row[1])]
    if len(row) == 3:
        return [int(row[0]), float(row[1]), float(row[2])]


if __name__ == "__main__":
    arrival_fractions, charging_volume_distributions, connection_time_distributions, solar_availability_distributions = readCSVs()
    sum = 0
    for i in charging_volume_distributions:
        sum += i[1]
    print(sum)