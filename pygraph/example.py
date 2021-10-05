import queue
import numpy as np
import collections
import pygraph as pg

import datetime

def memoryview_to_np(memview, nebr_dt):
    arr = np.array(memview, copy=False)
    #a = arr.view(nebr_dt).reshape(nebr_reader.get_degree())
    a = arr.view(nebr_dt)
    return a;

#simple plain CSR 
def test_csr():   
    '''CSR = compressed sparse row
    storage structure comprises vertex table and edge table
    1. Push based programming
    2. Trying to store the out neighbors of each vertex
    3. Top down '''
    outdir = ""
    # user should specify
    num_sources = 1 
    num_threads = 2 
    # initializes graph
    graph  = pg.init(1,1, outdir, num_sources, num_threads) # Indicate one pgraph, and one vertex type
    
    tid0 = graph.init_vertex_type(1000, True, "gtype"); # initiate the vertex type
    # edges have a source vertex with a specified dtype
    edge_dt = np.dtype([('src', np.int32), ('dst', np.int32)])
    flags = pg.enumGraph.eUdir;
    # property graph where we will ingest data
    pgraph = graph.create_schema(flags, tid0, "friend", edge_dt); #initiate the pgraph
    
    # input file
    ifile = "smallworld.txt";
    dd = np.zeros(1024, edge_dt); 
    edge_count = 0;
    with open(ifile) as f:
        for line in f: # read rest of lines
            x = line.split();
            #print(x);
            if x[0] != "#": 
                dd[edge_count] = (x[0], x[1]);
                edge_count += 1;
                if (edge_count == 1024):
                    pgraph.add_edges(dd, 1024); # You can call this API many times, if needed
                    edge_count = 0;

    # inaccruate print('edge count = ', edge_count);
    # can add edges when the buffer is full
    pgraph.add_edges(dd, edge_count); # You can call this API many times, if needed
    pgraph.wait(); # required for the time-being. You cannot add edges after this API.
   

    # creates 4 arrays: two offset and two neighbor
    offset_csr1, offset_csc1, nebrs_csr1, nebrs_csc1 = pg.create_csr_view(pgraph);
    # conversion: this is why it's important to know the dtype
    offset_dt = np.dtype([('offset', np.int32)])
    # if need to speficy edge weights
    csr_dt =  np.dtype([('dst', np.int32)])

    offset_csr = memoryview_to_np(offset_csr1, offset_dt);
    offset_csc = memoryview_to_np(offset_csc1, offset_dt);
    nebrs_csr  = memoryview_to_np(nebrs_csr1, csr_dt);
    nebrs_csc  = memoryview_to_np(nebrs_csc1, csr_dt);

    # length is 1001
    # lists the place in memory where the node at that index begins
    # storing it's neighbors
    #print('offset_csr list len = ', len(offset_csr.tolist()));
    #print(', values = \n', offset_csr.tolist());
    # shows neighbors of each node recorded in small world
    # e.g node 0 has neighboras 1, 2, 3, 4, 996, 997, 998, 999
    # e.g node 1 has neighboras 0, 2, 3, 4, 5, 996, 997, 998
    # lists all edges from perspective of both nodes, so length is
    # double the number of edges in the graph
    #print('nebrs_csr list len = ', len(nebrs_csr.tolist()));
    #print(', values =\n', nebrs_csr.tolist());
    # to get the degree of each node, just need offset list
    offset_list = [val[0] for val in offset_csr.tolist()]
    offset_list_shift = offset_list.copy()
    offset_list_shift.pop(0) # remove 0 offset, first value
    offset_list.pop()
    node_degrees = [(v2 - v1) for v1, v2 in zip(offset_list, offset_list_shift)]
    #print('node degrees = ', node_degrees)
    return pgraph


def run_bfs(a_pygraph, start_node):
    ''' do breadth first search by looping through the offset
    and neighbor array of a pygraph. The output should be
    an array that provides the number of nodes at each level
    starting from any node
    args:
        a_pygraph: a gaph of type pygraph (from pygraph library) 
        start_node: integer representing the node to start from'''

    # use pygraph functions demonstrated in test_csr to get graph
    # in csr formatinfo
    # creates 4 arrays: two offset and two neighbor
    offset_csr1, offset_csc1, nebrs_csr1, nebrs_csc1 = pg.create_csr_view(pgraph);
    # conversion: this is why it's important to know the dtype
    offset_dt = np.dtype([('offset', np.int32)])
    # if need to speficy edge weights
    csr_dt =  np.dtype([('dst', np.int32)])
    
    offset_csr = memoryview_to_np(offset_csr1, offset_dt);
    offset_csr_list = [val[0] for val in offset_csr.tolist()]
    nebrs_csr  = memoryview_to_np(nebrs_csr1, csr_dt);
    nebrs_csr_list =  [val[0] for val in nebrs_csr.tolist()]
    
    # array for tracking vertices level labels
    # start all levels at infinity
    array_size = len(offset_csr_list) - 1
    label_array = np.ones(array_size, dtype=np.int8) * 255
    # for tracking vertices to visit
    # can use status array where: (U = unvisited, V = visited, F = frontier)
    # or use a queue to track the frontier
    frontier_q = queue.Queue()
    #print('init fontier empty?', frontier_q.empty()) # should return True

    # mark the start node level label as 0
    label_array[start_node] = 0  
    # add start nodes to frontier queue
    # begin traversing the graph from start_node
    frontier_q.put(start_node)
    #print('frontier queue size = ', frontier_q.qsize()) # should return 1
    
    # begin putting and getting from the queue
    while frontier_q.empty() == False:
        current_vertex = frontier_q.get()
        #print('current vertex is', current_vertex)
        # explore neighbors of current node
        # get starting location of node's neighbors from offset
        start_idx = offset_csr_list[current_vertex]
        end_idx = offset_csr_list[current_vertex + 1]
        # get the neighbors of current node by using starting location of
        # it's neighbors and starting location of next node's neighbors
        current_nebrs = nebrs_csr_list[start_idx : end_idx] # end not inclusive
        # change level label of nebrs and add to queue
        for neb in current_nebrs:
            if label_array[neb] > label_array[current_vertex] + 1:
                label_array[neb] = label_array[current_vertex] + 1
                frontier_q.put(neb)
            else:
                pass

    #print('frontier queue size = ', frontier_q.qsize()) # should return 1
    #print('frontier queue ' , frontier_q)
    #print('label array ' , label_array.tolist())
    
    # aggregate over the labels to accumulate like levels
    count_levels = np.bincount(label_array)
    for lev, count in enumerate(count_levels):
        print('Level {}: {} nodes'.format(lev, count))

def test_lanl_graph_python():
    
    ''' comprehensive property graph that can store many things like 
    source, time, duration, and size in bytes'''
    edge_dt = np.dtype([('src', np.int32), ('dst', np.int32), 
                       ('time', np.int32),
                       ('duration', np.int32),
                       ('protocol', np.int32),
                       ('src_port', np.int16),
                       ('dst_port', np.int16),
                       ('src_Packets', np.int32),
                       ('dst_packets', np.int32),
                       ('src_Bytes', np.int32),
                       ('dst_Bytes', np.int32)
                      ])
    nebr_dt = np.dtype([('dst', np.int32), 
                       ('time', np.int32),
                       ('duration', np.int32),
                       ('protocol', np.int32),
                       ('src_port', np.int16),
                       ('dst_port', np.int16),
                       ('src_Packets', np.int32),
                       ('dst_packets', np.int32),
                       ('src_Bytes', np.int32),
                       ('dst_Bytes', np.int32)
    ])
    
    flags = pg.enumGraph.eUdir;
    outdir = ""
    graph  = pg.init(1,1, outdir, 1, 4) # Indicate one pgraph, and one vertex type
    tid0 = graph.init_vertex_type(31142, False, "gtype"); # initiate the vertex type
    pgraph = graph.create_schema(flags, tid0, "friend", edge_dt); #initiate the pgraph
   
    ifile = "/home/datalab/data/lanl17/nf_day-02.csv"; # test.csv;
    
    dd = np.zeros(10000, edge_dt); 
    edge_count = 0;
    start = datetime.datetime.now()
    with open(ifile) as f:
        for line in f: # read rest of lines
            x = line.split(",");
            #print(x);
            if x[0] != "#":
                src_id = graph.add_vertex(x[2], tid0);
                dst_id = graph.add_vertex(x[3], tid0);
                #print(x[2], x[3], src_id, dst_id)
                dd[edge_count] = (src_id, dst_id, x[0], x[1], x[4], x[5], x[6], x[7], x[8], x[9], x[10]);
                edge_count += 1;
            if(edge_count == 10000):
                pgraph.add_edges(dd, edge_count);
                edge_count = 0
    pgraph.add_edges(dd, edge_count);
    
    pgraph.wait(); # You can't call add_edges() after wait(). The need of it will be removed in future.
    end = datetime.datetime.now()
    diff = end - start;
    print("graph creation time = ", diff)
    

if __name__=="__main__":
    pgraph = test_csr();
    #test_lanl_graph_python();
    
    # initialize pygraph
    outdir = ""
    # user should specify
    num_sources = 1 
    num_threads = 2 
    
    # run bfs passing the pgraph created from the file and start node 0
    run_bfs(pgraph, 0)
