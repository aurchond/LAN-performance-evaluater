import random
import collections
import numpy as np





# generates 1 random variable value at time
def gen_exp_rv(lambda_var):
    uniform = random.random()

    # create exponential random variable using inverse method
    x = -(1 / lambda_var) * np.log(1 - uniform)
    return x


# generate the exponential backoff
def gen_exp_backoff(i):
    # assign transmission rate to be 1Mbps
    R = 1E6
    rand = random.randint(0, (2 ** i)-1)
    wait_time = (rand * 512) / R
    return wait_time
  
        
# pregenerate the packet arrival times
def pregen_arrivals(T, lambda_var):
    # make a queue of packets to be processed
    pkt_timestamps = collections.deque()

    # used to sum up the arrival times
    total_t_arrival = 0

    # generate all arrival events and add them up; 
    # if this sum is greater than T, we've generated all the packets we can for the simulation
    while total_t_arrival <= T:
        # get rvs for inter-arrival time and length of packet -> L is mean length of packets
        # calculate service time from given C
        t_arrival = gen_exp_rv(lambda_var)
        total_t_arrival = total_t_arrival + t_arrival

        # generate packet arrival
        pkt_timestamps.append(total_t_arrival)

    return pkt_timestamps


# return the node with the lowest arrival time of its first packet
def get_sending_node(nodes):
    # keep a list of arrival times for the first packet in each node's queue
    first_packets_tuple = []

    for i in range(len(nodes)):
        if (len(nodes[i].pkts) != 0):
            # record the arrival time of the 1st packet in each queue, store in a tuple
            first_packets_tuple.append((i, nodes[i].pkts[0]))

    # we have no more packets to send, send an error
    if len(first_packets_tuple) == 0:
        return -1

    else:
        # choose which node gets to be the sender based on which packet arrived first
        sender_node_tuple = min(first_packets_tuple, key=lambda x: x[1])
        return sender_node_tuple[0] 
    
# NOTE: in this function we're updating colliding_node
# we call this function on the receiver multiple times then once on the sender
# the last parameter is only of importance if we're calling this function on the receiver
def check_num_collisions(node, current_t_prop, sending_node_arrival):
    L = 1500
    R = 1E6
    t_trans = L / R

    # iterate the number of collisions on this node
    node.num_coll += 1

    # we have exceeded the maximum allowable number of collisions for this node
    if (node.num_coll > 10):
        
        # reset the number of collision for this node
        node.num_coll = 0

        if (len(node.pkts) == 1):
            # we can't drop anymore packets after this one so we return
            node.pkts.popleft()
            return

        # get the arrival time for the first packet then drop that packet
        arrival_time_dropped = node.pkts[0] 
        node.pkts.popleft()
        
        # set the next packet's arrival time to be the dropped packet's arrival time and the transmission time
        node.pkts[0] = arrival_time_dropped + t_trans

        # go through the remaining packets in the queue and make sure they don't arrive arrive before the first 
        node.check_remaining_packets()

    # number of collisions is less than 10
    else:
        # enter exponential backoff
        exp_backoff = gen_exp_backoff(node.num_coll)

        if (node.is_sender == 1):
            # set new arrival time of packet 1 using it's current arrival time
            node.pkts[0] += current_t_prop + exp_backoff
            
            # go through the remaining packets in the queue and make sure they don't arrive arrive before the first 
            node.check_remaining_packets()

        # set wait time for receiver
        else:
            # set new arrival time of packet 1, using specifically the arrival time of the sender
            node.pkts[0] = sending_node_arrival + current_t_prop + exp_backoff
            
            # go through the remaining packets in the queue and make sure they don't arrive arrive before the first 
            node.check_remaining_packets()
            
