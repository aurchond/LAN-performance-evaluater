import CSMAHelper

import time
import numpy as np
from matplotlib import pyplot

# list of nodes coincides with list of packet lists
class Node:
    def __init__(self, num, pkts, num_coll, is_sender):
        self.num = num # this is the index of the node in the list of nodes
        self.pkts = pkts # arrival times of all packets in the queue
        self.num_coll = num_coll  # num_collisions of FRONT PACKET
        self.is_sender = is_sender
    
    # check all of the remaining packets after the first one to see if they arrive before it
    def check_remaining_packets(self):
        for i in range(1, len(self.pkts)):
                # updating packets behind the current one so that they don't arrive before the new arrival time of packet
                if (self.pkts[i] < self.pkts[0]):
                    self.pkts[i] = self.pkts[0]

                # all packets from here onwards are already after the new arrival time of packet 1
                else:
                    break

def get_packet_stats(nodes, sender_node_number):

    # links are 10 m apart
    d = 10
    # assign signal speed
    s = (2 / 3) * (300000000)
    t_prop = d / s

    # assign length to be 2000 bits
    L = 1500
    # assign transmission rate to be 1Mbps
    R = 1E6
    t_trans = L/R

    # list of all nodes (i.e. their index) we collide with
    coll_list = []
    
    sender_node = nodes[sender_node_number]

    ######################## COLLISION, BUSY CHECKING ############################

    # go through all nodes
    for node_num in range(len(nodes)):
        node = nodes[node_num]

        # make sure it's not the same node as the sender node and make sure it's packet queue isn't empty
        if (node_num != sender_node.num and len(node.pkts) != 0):
            current_t_prop = abs(sender_node.num - node_num) * t_prop

            # check collision condition
            if (node.pkts[0] <= (sender_node.pkts[0] + current_t_prop)):
                # clarify that the node is not a sender (aka its a receiver),
                # there is a different case within check_num_collisions() for receivers 
                node.is_sender = 0
                # call with receiving node
                CSMAHelper.check_num_collisions(node, current_t_prop, sender_node.pkts[0])
                coll_list.append(node_num)
              
            # check busy condition
            elif (sender_node.pkts[0] + current_t_prop) < node.pkts[0] < (sender_node.pkts[0] + current_t_prop + t_trans):
                # set the first packet of the current node to the last bit of the sending node
                node.pkts[0] = sender_node.pkts[0] + current_t_prop + t_trans
                
                # check the arrival times of all other packets to see if they should change too
                for i in range(1, len(node.pkts)):
                    if (sender_node.pkts[0] + current_t_prop) < node.pkts[i] < (sender_node.pkts[0] + current_t_prop + t_trans):
                        # it needs to arrive when the bus is free again
                        node.pkts[i] = sender_node.pkts[0] + current_t_prop + t_trans
                    else:
                        break

    # if we had any collisions, do the exponential backoff time and all updating for the sending node
    if (len(coll_list) > 0):
        dist_diff_list = []

        # go through all collisions to find furthest one from the sender node
        for j in range(len(coll_list)):
            diff = abs(sender_node.num - j)
            dist_diff_list.append(diff)

        max_d = max(dist_diff_list)

        # the maximum propagation time is based on the distance from the furthest receiver
        max_t_prop = max_d * t_prop
        # clarify that this node is a sender since this is used in check_num_collisions()
        sender_node.is_sender = 1
        CSMAHelper.check_num_collisions(sender_node, max_t_prop, 0)
        # return the number of transmitted packets (i.e. packets that touch the medium at all)
        # this will be the sender node and all of the nodes it collided with
        num_trans = 1 + len(coll_list)

        # return the # of transmitted packets, # of successful packets
        raw_return_data = [num_trans, 0]
        return raw_return_data


    ################# SUCCESS CHECKING ###################
    # was able to get out of while loop and not have collisions with ANY nodes

    # we are transmitting the last packet in the queue
    if (len(sender_node.pkts) == 1):
        # reset the number of collisions in this case
        sender_node.num_coll = 0
        # pop off the last packet left in the queue
        sender_node.pkts.popleft()
        # return the # of transmitted packets, # of successful packets
        raw_return_data = [1, 1]
        return raw_return_data
    
    # check if we need to push back the arrival time of the second packet in the queue
    elif (sender_node.pkts[1] < sender_node.pkts[0] + t_trans):
        sender_node.pkts[1] = sender_node.pkts[0] + t_trans

        # go through the rest of the packets in the queue
        for i in range(2, len(sender_node.pkts)):
            # check and update packets behind the second packet so they don't arrive early
            if (sender_node.pkts[i] < sender_node.pkts[0] + t_trans):
                sender_node.pkts[i] = sender_node.pkts[0] + t_trans

            else:
                break

    # drop sender packet
    sender_node.pkts.popleft()

    # reset num of collisions for a node once it successfully transmits a pkt
    sender_node.num_coll = 0

    # print("done: success")
    # return the # of transmitted packets, # of successful packets
    raw_return_data = [1, 1]
    return raw_return_data


def implement_csma(N, arrival_rate):
    # define a simulation time
    T = 10

    # make a list of all our nodes
    nodes = []
    
    # create Deque queues for each node
    for n in range(N):
        pkts = CSMAHelper.pregen_arrivals(T, arrival_rate)
        nodes.append(Node(n, pkts, 0, 0))

    num_succ_transmissions = 0
    num_total_transmissions = 0

    # set up all our time variables
    start_time = time.time()
    elapsed_time = 0

    # call the main csma protocol function which returns the
    while elapsed_time <= T:
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        # get the minimum arrival time from the first packet of all nodes
        sending_node = CSMAHelper.get_sending_node(nodes)
        # print("min_node_ind: ", min_node_ind)

        # we are done simulating since all packets have been dropped or delivered
        if (sending_node < 0):
            break
        
        # call the main csma protocol function, which returns the raw data for later use
        raw_data = get_packet_stats(nodes, sending_node)

        # the two stats
        num_total_transmissions = num_total_transmissions + raw_data[0]
        num_succ_transmissions = num_succ_transmissions + raw_data[1]


    # first slot is efficiency, second slot is throughput
    # throughput is num of successful transmissions * frame length divided by simulation time
    cooked_data = [num_succ_transmissions/num_total_transmissions, ((num_succ_transmissions*1500)/T)/1E6]
    return cooked_data


if __name__ == '__main__':
    x_axis = np.arange(20, 120, 20)

    a_values = [7, 10, 20]

    # processed_data = implement_csma(10, 7)

    # declare the throughput list
    throughput_all_points = []

    # go through arrival times
    for a in a_values:
        # reset our list of efficiency for each new value of a
        efficiency_points = []
        throughput_points = []

        # go through different numbers of nodes
        for n in x_axis:
            
            # call implement_csma with with the different values of a and n
            processed_data = implement_csma(n, a)

            efficiency = processed_data[0]
            throughput = processed_data[1]

            efficiency_points.append(efficiency)
            throughput_points.append(throughput)

        # add the throughput points list to the list of lists
        throughput_all_points.append(throughput_points)

        pyplot.scatter(x_axis, efficiency_points)
        pyplot.plot(x_axis, efficiency_points, label=('Arrival rate = ' + str(a)))

    pyplot.xlabel("N")
    pyplot.ylabel("Efficiency, eff")
    pyplot.title("Efficiency of Persistent CSMA/CD Protocol (eff) vs. N")
    pyplot.legend(loc='upper right')
    pyplot.savefig('358lab2_Q1a')

    # clear the plot to add the throughput
    pyplot.clf()

    #### GRAPHING THROUGHPUT #######

    pyplot.scatter(x_axis, throughput_all_points[0])
    pyplot.plot(x_axis, throughput_all_points[0], label=("Arrival rate = 7"))

    pyplot.scatter(x_axis, throughput_all_points[1])
    pyplot.plot(x_axis, throughput_all_points[1], label=("Arrival rate = 10"))

    pyplot.scatter(x_axis, throughput_all_points[2])
    pyplot.plot(x_axis, throughput_all_points[2], label=("Arrival rate = 20"))

    pyplot.xlabel("N")
    pyplot.ylabel("Throughput, tp (Mbps)")
    pyplot.title("Throughput of Persistent CSMA/CD Protocol (tp) vs. N")
    pyplot.legend(loc='lower right')
    pyplot.savefig('358lab2_Q1b' )

