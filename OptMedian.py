import networkx as nx
import osmnx as ox
import geopy
import random
import os
import time
from itertools import combinations
import queue
from threading import Thread
from multiprocessing import Process, Queue, Value
from geopy.geocoders import Nominatim
import requests
import matplotlib.cm as cm
import matplotlib.colors as colors


config = True

if config:
    ox.config(use_cache=True, log_console=True)
    ox.__version__
    config = False

#This is the Solver Portion of the Algorithm. This takes the top of the
#Queue and finds the cost for that particular combination of facilities
def solver(inqueue, outqueue, graph, nodes, ty, cur_opt):
    #print("Thread Started")

    #Set up the starting variables
    graph = nx.MultiDiGraph(graph)
    nodes = nx.nodes(graph)
    loc_mn = int(999999999999999999999999999999)
    #print(loc_mn)
    #Main Processing Loop
    while True:
        #Get the top element of the queue
        proc = list(inqueue.get(True, None))
        #print(proc)
        #If No more elements in queue
        if proc[0] == "Exit":
            #Propagate the exit through to the calculator
            outqueue.put(["Exit"])
            #print("Thread Exited")
            break

        #Make a clean answer object
        ans = [[], []]

        ans[0] = proc
        #print(ans[0])
        #If the local variable is smaller than the shared set the local to shared
        if loc_mn < cur_opt.value:
            loc_mn = cur_opt.value

        # p-Median is false
        if ty == False:
            #Set the sum to 0
            sm = int(0)
            #For each Node
            for y in nodes:
                fu = 0
                #Initialize the max to some large value
                mn = int(999999999999999999999999999999)
                #For each facility
                for x in range(0, len(proc)):
                    try:
                        #Get the shortest path between the facilities
                        p = int(nx.shortest_path_length(graph, proc[x], y))
                        #print(p)
                        #Get the smallest value among facilites
                        if int(p) < int(mn):
                                mn = int(p)
                    except:
                        #If no facility can be reached then it does not contribute to the cost
                        fu = fu + 1
                        if fu == len(proc):
                            mn = 0
                        #print("Could Not Get Shortest Path")

                #Sum the current costs
                sm = sm + mn
                #print(sm)
                #If sum is larger than local minumu
                if int(sm) > loc_mn:
                    sm = int(loc_mn) + 1
                    #Stop calculating
                    #print("This should never happen the first time round")
                    break
                #print(sm)
            #Set answer component equal to sum
            #print(sm)
            #Catch-All for cases where the facility is unreachable
            if sm == 0:
                sm = loc_mn
            ans[1] = sm
            #print(ans)

        #p-Center is true
        else:
            #set current max to 0
            mx = 0
            #for each node
            for y in nodes:
                fu = 0
                #set local x to a large value
                lx = int(999999999999999999999999999999)
                #for each facility
                for x in range(0, len(proc)):
                    try:
                        #get the shortest path between the two
                        p = int(nx.shortest_path_length(graph, proc[x], y))
                        #print(p)
                        #get shortest path to closest facility
                        if int(p) < int(lx):
                            lx = int(p)
                    except:
                        #Set up exceptions for no path to all facilities
                        fu = fu + 1
                        if fu == len(proc):
                            lx = 0
                        #print("Could Not Get Shortest Path")
                #Get the largest value
                if lx > mx:
                        mx = lx
                #If larger than current minimum,
                if int(mx) > int(loc_mn):
                    mx = int(loc_mn) + 1
                    #stop calculating
                    break
            # Catch-All for cases where the facility is unreachable
            if mx == 0:
                mx = loc_mn + 1
            ans[1] = mx

        #if current answer is smaller than local minimum
        if int(ans[1]) < int(loc_mn):
            loc_mn = int(ans[1])
        #print(ans[1])

        #If the current answer is better than the global
        if ans[1] < cur_opt.value:
            #Set global to current
            cur_opt.value = ans[1]
        #Put the solution in the checking queue
        outqueue.put(ans)

#This just acts to process the output of the queues and store the best solution
def value(inqueue, outqueue, fac, n):
    q = int(0)
    x = int(0)
    nn = int(n)
    print(nn)
    small = int(999999999999999999)
    while int(x) < int(fac):
        proc = inqueue.get(True, None)
        #print(proc)
        q = q + 1
        print(q, "/", nn)
        print(small)
        if proc[0] == "Exit":
            x = x + 1
            if x == fac:
                break

        if q == int(nn):
            break
        try:
            if proc[1] < small:
                small = int(proc[1])
                print(small)
                solution = proc[0]
        except:
            break

    vault = [[], []]
    vault[0] = solution
    vault[1] = small
    outqueue.put(vault)


def main():
    if __name__ == '__main__':
        #Set up the user inputs
        CITY_STR = input("Enter the City: ")
        prob_type = input("Enter the Problem type: (c: center, m: median ")
        num_fac = int(input("Enter the p-value: "))
        num_thr = int(input("Enter the number of threads: "))

        pt = 3
        if(prob_type == 'c'):
            pt = True
        elif prob_type == 'm':
            pt = False

        if pt == 3:
            print("Not a Valid Problem Type")
            return -1

        #Set up the global queues
        sendqueue = Queue()
        recqueue = Queue()
        valqueue = Queue()

        #print(num_fac)
        #Get graph
        G = ox.graph_from_place(CITY_STR, network_type='all')
        #Generate list of nodes
        nodes = list(nx.nodes(G))
        print("Generated Graph")

        #Initialize global optimum
        current_optimum = Value('i')

        #Initialize threads
        threads = []
        for x in range(0, int(num_thr) - 1):
            if __name__ == '__main__':
                t = Process(target=solver, args=(sendqueue, recqueue, G, nodes, pt, current_optimum))
                t.start()
                threads.append(t)

        if __name__ == '__main__':
            out = Process(target = value, args = (recqueue, valqueue, (int(num_thr)-1), int(len(nodes)**int(num_fac)) ))
            out.start()

        print("Created Solver Threads")

        start = time.time()

        #Get the iterator of combinations
        data = combinations(nodes, num_fac)

        #Send each combination to the queue
        for x in data:
            sendqueue.put(x)

        #Send the exit messages
        for x in range(0, int(num_thr) - 1):
            sendqueue.put(["Exit"])

        #Wait on optimal solution
        while True:
            sol = valqueue.get(True, None)
            print(sol)
            break

        #Rejoin threads
        for x in threads:
            x.join()
        out.join()

        end = time.time()
        ela = end-start

        print("Time elapsed :", ela, " seconds")

        #Print out details of optimal solution
        print("Found Optimum Candidate with Cost: ", sol[1])
        print("With Facilities Located At: ")
        attributes = G.nodes.items()
        for x in sol[0]:
            for a in attributes:
                if x == a[0]:
                    # Print out the details of any match
                    print("Node ID: ", x)
                    print("Latitude: ", a[1]['y'])
                    print("Longitude: ", a[1]['x'])
                    lat = a[1]['y']
                    long = a[1]['x']
                    geolocator = Nominatim(user_agent="PyProject", timeout=10)
                    try:
                        # Nominatim tends to timeout a fair bit, so throw this into a try-except block
                        location = geolocator.reverse(lat, long)
                        print("Closest Street Address: ", location.address)
                    except:
                        print("Closest Street Address Could Not be found due to Timeout: Try again later")



main()