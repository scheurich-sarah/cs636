#include <cassert>
#include <iostream>
#include "csr.h"

using std::cout;
using std::endl;

// this needs kernel.cpython

void run_bfs(graph_t& g, vid_t root)
{
    csr_t* csr = &g.csr;
    csr_t* csc = &g.csc;
    
    cout << "csr.get_vcount = " << csr->get_vcount() << endl; 
    cout << "csr.get_ecount = " << csr->get_ecount() << endl; 
    cout << "degree of node 1 = " << csr->get_degree(1) << endl; 
    //TODO
    // all the logic will go here
    // just implement top down
		
    cout << "in bfs.cpp: root = " << root << endl; 
    //print bfs tree here
    //i.e. how many vertex in each level
}
