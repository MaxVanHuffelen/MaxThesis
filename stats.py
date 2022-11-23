
from ast import Assert
from distutils.filelist import findall
from math import sqrt
import numpy as np
import performanceMeasures

def writeTable(data, file, param):
    with open(f'./tables/{file}', 'a') as myfile:
        myfile.write('\\begin{table}[H]\n\t\\centering\n\t\\caption{Paired confidence intervals of ' + str(param) + '}\n\t\\begin{tabular}{c|' + 'c'*(len(data[0])-1) + '}\n')
        hline = True 
        for line in data:
            newline = ""
            for element in line:
                if type(element) == str:
                    newline += f" & {element}"
                else:
                    low, high = element
                    newline += f" & ({round(float(low), 2)}, {round(float(high), 2)})"
            if hline:
                newline += ' \\\\ \\hline \n'
                hline = False
            else:
                newline += " \\\\ \n" 
            myfile.write(newline[3:])
        myfile.write("\t \\end{tabular}\n\t\\label{tab:paired confidence intervals of " + str(param) +'}\n\\end{table}\n\n')

def emptyList(h,w):
    lst = []
    for i in range(h):
        lst.append([None]*w)
    return lst

def findAllPairedConfidenceIntervals(cases, file = 'tables.txt', params = ["maximum delay", "average delay", "percentage of cars with a delay", "maximum load on cable 0", "fraction of time cable 0 is overloaded", "fraction of time cable 0 is blacked out", "maximum load on cable 4", "fraction of time cable 4 is overloaded", "fraction of time cable 4 is blacked out", "percentage of arriving cars that are not served", "average number of daily non-served cars"]):
    resultsDict = {}
    for case in cases:
        print(f'finding {case} measures')
        if case not in resultsDict:
            resultsDict[case] = {}

        resultsDict[case]["maximum delay"], resultsDict[case]["average delay"], resultsDict[case]["percentage of cars with a delay"] = findDelays(case)
        cable0, cable1, cable2, cable3, cable4, cable5, cable6, cable7, cable8 = findCableLoads(case)
        resultsDict[case]['maximum load on cable 0'], resultsDict[case]['fraction of time cable 0 is overloaded'], resultsDict[case]['fraction of time cable 0 is blacked out'] = cable0
        resultsDict[case]["maximum load on cable 1"], resultsDict[case]["fraction of time cable 1 is overloaded"], resultsDict[case]["fraction of time cable 1 is blacked out"] = cable1
        resultsDict[case]["maximum load on cable 2"], resultsDict[case]["fraction of time cable 2 is overloaded"], resultsDict[case]['fraction of time cable 2 is blacked out'] = cable2
        resultsDict[case]['maximum load on cable 3'], resultsDict[case]['fraction of time cable 3 is overloaded'], resultsDict[case]['fraction of time cable 3 is blacked out'] = cable3
        resultsDict[case]['maximum load on cable 4'], resultsDict[case]['fraction of time cable 4 is overloaded'], resultsDict[case]['fraction of time cable 4 is blacked out'] = cable4
        resultsDict[case]['maximum load on cable 5'], resultsDict[case]['fraction of time cable 5 is overloaded'], resultsDict[case]['fraction of time cable 5 is blacked out'] = cable5
        resultsDict[case]['maximum load on cable 6'], resultsDict[case]['fraction of time cable 6 is overloaded'], resultsDict[case]['fraction of time cable 6 is blacked out'] = cable6
        resultsDict[case]['maximum load on cable 7'], resultsDict[case]['fraction of time cable 7 is overloaded'], resultsDict[case]['fraction of time cable 7 is blacked out'] = cable7
        resultsDict[case]['maximum load on cable 8'], resultsDict[case]['fraction of time cable 8 is overloaded'], resultsDict[case]['fraction of time cable 8 is blacked out'] = cable8
        resultsDict[case]['percentage of arriving cars that are not served'], resultsDict[case]['average number of daily non-served cars'] =  findNonServiced(case)

    amountCases = len(cases)
    for param in params:
        print(f'creating {param} table')
        allConfidenceIntervals = emptyList(amountCases+1, amountCases+1)
        allConfidenceIntervals[0][0] = ' '
        for i in range(amountCases):
            #write column/row headers
            allConfidenceIntervals[i+1][0] = cases[i]
            allConfidenceIntervals[0][i+1] = cases[i]
            for j in range(amountCases):
                case1 = cases[i]
                case2 = cases[j]
                allConfidenceIntervals[i+1][j+1] = get_paired_confidence_interval(resultsDict[case1][param], resultsDict[case2][param])
        writeTable(allConfidenceIntervals, file=file, param=param)

def s2(xs):
    average = sum(xs)/len(xs)
    diffs2 = sum([(x-average)**2 for x in xs])
    return diffs2 / (len(xs) - 1)

def get_paired_confidence_interval(xs1, xs2):
    assert len(xs1) == len(xs2) 
    n = len(xs1)
    z = [xs2[i] - xs1[i] for i in range(n)]
    z_bar = sum(z) / n
    s_z2 = sum([(z_j - z_bar)**2 for z_j in z]) / (n - 1)
    t = 2.262 # for n=10, alpha = 0.05 
    plusminus = t * sqrt(s_z2/n)
    return (z_bar - plusminus, z_bar + plusminus)


def readFile(path):

    returnTimestamps = []
    returnDataPoints = []    

    timestamps = []
    dataPoints = []
    with open(path, "r") as file:
        lines = file.readlines()

        for line in lines[1:]:
            if(line[0] == '-'):
                # print("Results of new simulation")
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


def findDelays(root):
    with open(f"./{root}/delays.txt", "r") as file:
        lines = file.readlines()


    allData = []
    currSimulationData = []
    for line in lines[1:]:
        if line[0] == '-':
            allData.append(currSimulationData)
            currSimulationData = []
        else:
            currSimulationData.append(float(line.split(',')[1].strip()))
    # Max delay, Average delay, percentage with delay
    results = ([],[],[])
    for parsed in allData:
        parsed = np.array(parsed)
        results[0].append(np.max(parsed)) # max delay
        results[1].append(np.mean(parsed)) # average delay
        results[2].append(100 * parsed[parsed!=0.0].shape[0] / parsed.shape[0]) # percentage delayed
    return results 

def findCableLoads(root):
    allTimestamps, allCablePower = readFile(f'./{root}/powerDensity.txt')
    
    #[max, % overload, % blackout] for each cable
    results = (([],[],[]), ([],[],[]), ([],[],[]), ([],[],[]), ([],[],[]), ([],[],[]), ([],[],[]), ([],[],[]), ([],[],[]))
    for simulationIndex in range(len(allTimestamps)):
        timesteps = allTimestamps[simulationIndex]
        cablePower = allCablePower[simulationIndex]
        cablePower = np.array(cablePower).T

        finalTimestep = timesteps[-1]
        firstTimeStep = timesteps[0]
        for i in range(9):
            maxValue = max(cablePower[i])
    
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
            atLeast10 /= (finalTimestep - firstTimeStep)
            max10 /= (finalTimestep - firstTimeStep)
            noOverload /= (finalTimestep - firstTimeStep)

            assert abs(atLeast10 + max10 + noOverload - 1.0) < 0.01

            results[i][0].append(maxValue)
            results[i][1].append(max10)
            results[i][2].append(atLeast10)
    return results 

def findNonServiced(root, simLength=10*86400, cutStart = 2*86400, cutEnd = 1*86400):
    with open(f"./{root}/serviced.txt", "r") as file:
        lines = file.readlines()
    # % non serviced, average daily non serviced
    results = ([],[])

    totalServed = 0
    totalNonServed = 0
    for line in lines:
        if (line[0] == "-") and (totalServed + totalNonServed > 0):
            results[0].append(100*totalNonServed/(totalNonServed + totalServed))
            results[1].append(86400*totalNonServed/(simLength-cutStart - cutEnd))
            totalNonServed = 0
            totalServed = 0
        elif line[0].isdigit():
            timeStamp, isServed = line.split(',')
            timeStamp = int(timeStamp)
            isServed = isServed.strip()
            if cutStart < timeStamp < simLength - cutEnd:
                if isServed.lower() == "served":
                    totalServed += 1
                elif isServed.lower() == "notserved":
                    totalNonServed += 1
                else:
                    raise AssertionError
        

    return results 

findAllPairedConfidenceIntervals(cases = ['base','base-summer-1-2-6-7', 'base-summer-6-7','base-winter-1-2-6-7','base-winter-6-7'], file='base-different-solars.txt')
findAllPairedConfidenceIntervals(cases = ['ELFS','ELFS-summer-1-2-6-7','ELFS-summer-6-7','ELFS-winter-1-2-6-7','ELFS-winter-6-7'], file='ELFS-different-solars.txt')
findAllPairedConfidenceIntervals(cases = ['FCFS','FCFS-summer-1-2-6-7','FCFS-summer-6-7','FCFS-winter-1-2-6-7','FCFS-winter-6-7'], file='FCFS-different-solars.txt')
findAllPairedConfidenceIntervals(cases = ['base', 'FCFS','ELFS'], file = 'different-no-solar.txt')
findAllPairedConfidenceIntervals(cases = ['base-summer-1-2-6-7','FCFS-summer-1-2-6-7', 'ELFS-summer-1-2-6-7'], file = 'different-summer-1-2-6-7.txt')
findAllPairedConfidenceIntervals(cases = ['base-summer-6-7','FCFS-summer-6-7','ELFS-summer-6-7'], file = 'different-summer-6-7.txt')
findAllPairedConfidenceIntervals(cases = ['base-winter-1-2-6-7','FCFS-winter-1-2-6-7', 'ELFS-winter-1-2-6-7'], file = 'different-winter-1-2-6-7.txt')
findAllPairedConfidenceIntervals(cases = ['base-winter-6-7','FCFS-winter-6-7','ELFS-winter-6-7'], file = 'different-winter-6-7.txt')