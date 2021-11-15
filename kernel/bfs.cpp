#include <cassert>
#include <chrono>
#include <iostream>
#include "csr.h"
#include "omp.h"
#include <queue>

using std::cout;
using std::endl;
using namespace std::chrono;

// this needs kernel.cpython

void run_bfs(graph_t& g, vid_t root)
{
    auto start = high_resolution_clock::now();
    // 	& in params means youre passing it a reference
    // 	to a param, which uses original object instead
    // 	of a copy, so you can change original object value

    // pointers of type csr_t
    csr_t* csr = &g.csr;
    csr_t* csc = &g.csc;
    // vid_t object
    vid_t test_idx = 999;
    
    // a->b member b of object pointed to by a aka (*a).b
    // a.b member b of objected a
    /* For initial checks 
    cout << "csr.get_vcount = " << csr->get_vcount() << endl; 
    cout << "g.get_vcount = " << g.get_vcount() << endl; 
    cout << "csr.get_ecount = " << csr->get_ecount() << endl; 
    cout << "g.get_edge_count = " << g.get_edge_count() << endl; 
    cout << "degree of node 1 = " << csr->get_degree(test_idx) << endl; 
    
    vid_t* n = csr->get_nebrs();
    cout << "n[5] = " << n[5] << endl;

    // can use either of these mechanisms to access what you need
    cout << "offset for vertex 999 = " << csr->get_offset(999) << endl;
    vid_t* o = csr->get_offset_ptr();
    cout << "offset for vertex 999 = " << o[test_idx] << endl; 
    */

    //TODO
    // all the logic will go here
    // just implement top down

    // get the offset and nebrs
    vid_t* offset = csr->get_offset_ptr();
    vid_t* nebrs = csr->get_nebrs_ptr();
    
    // array for tracking vertices level labels
    // start all levels at infinity
    int array_size = (int) csr->get_vcount();
    //cout << "array size = "<< array_size<< endl;
    int label_array [array_size]; 
    //cout << "size of label_array " << sizeof(label_array)/sizeof(label_array[0]) << endl;
    // init array values to 255
    for (int i = 0; i<array_size; i++) { label_array[i] = 255; }
    //cout << "label array post init = "<< *label_array<< endl;//prints first elem 
    // mark the start node level label as 0
    label_array[root] = 0;
    //cout << "label array post add root = "<< *label_array<< endl;//prints first elem 
    
    // create a queue of ints for tracking progress
    queue<vid_t> frontier;
    //cout << "fontier empty? "<< frontier.empty()<< endl; //returns 1 (True)
    // add the chosen root to the queue
    frontier.push(root);	
    //cout << "root added frontier.size "<< frontier.size() << endl; //returns 1
    
    
    // process items in the queue until there are no more
    while (!frontier.empty()) {
	vid_t current_vertex = frontier.front();
	frontier.pop(); // takes first elem out
	//cout<<"current vertex is "<< current_vertex << endl;
	// explore neighbors of current node
        // get starting location of node's neighbors from offset
        vid_t start_idx = offset[current_vertex];
	//cout<<"start idx = "<< start_idx << endl;
        vid_t end_idx = offset[current_vertex + 1];
	//cout<<"end idx = "<< end_idx << endl;
        // get the neighbors of current node by using starting location of
        // it's neighbors and starting location of next node's neighbors
        
	// loop through neighbors
        for (int i= start_idx; i < end_idx; i++) {
	    vid_t neb = nebrs[i];
            if (label_array[neb] > label_array[current_vertex] + 1) {
                label_array[neb] = label_array[current_vertex] + 1;
                frontier.push(neb);
	    }
	}
    }

    //cout << "frontier queue size = "<< frontier.size()<< endl;
    // loop through and print label array
    //cout << "printing label array " << endl;
    int max_level = 0;
    for(int i = 0; i < array_size; i++){
	//cout <<"index = "<<i<<" value = "<< label_array[i]<< endl;
	if (label_array[i] > max_level){ max_level = label_array[i];}
    }

    cout << "root = " << root << endl; 
    //print bfs tree here
    //i.e. how many vertex in each level

    // create array to track levels
    int level_array[max_level+1] = {0};
    for(int i = 0; i < array_size; i++){
	level_array[label_array[i]]++;
    }

    //print the array 
    for(int i = 0; i <= max_level; i++){
	cout<< "level "<< i << ": "<< level_array[i]<< " vertices"<< endl;
    }
    auto stop = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(stop-start);
    cout << "single thread frontier queue based BFS takes " << duration.count() << endl;
}

// parallelized implementation
// going to try with status array
void run_bfs_mt(graph_t& g, vid_t root)
{
    cout<<"running parallelized bfs"<<endl;
    auto start1 = high_resolution_clock::now();
    // pointers of type csr_t
    csr_t* csr = &g.csr;
    csr_t* csc = &g.csc;

    // get the offset and nebrs
    vid_t* offset = csr->get_offset_ptr();
    vid_t* nebrs = csr->get_nebrs_ptr();
    
    // create status array
    // level = visited
    // current level = frontier
    // 255 = unvisited
    // start all levels at infinity
    int array_size = (int) csr->get_vcount();
    //cout << "array size = "<< array_size<< endl;
    vid_t status_array [array_size]; 
    // init all values in array to 255
    for (int i=0; i<array_size; i++) {status_array[i] = 255;}

    // mark the start node level label as 0
    status_array[root] = 0;

    // create a thread for each vertex
    //omp_set_num_threads((int) array_size);

    // track the current level
    vid_t current_level = 0;
    vid_t frontier = 0;
	    
    //bool done = false;
    while(frontier < array_size-1){
	    #pragma omp parallel for shared(frontier)
	    for (int i = 0; i < array_size; i++){
		if (status_array[i] == current_level){
		    // node is in frontier, set level then find neighbors
		    // get starting location of node's neighbors from offset
		    vid_t start_idx = offset[i];
		    vid_t end_idx = offset[i + 1];
		
		    // loop through neighbors
		    for (int j= start_idx; j < end_idx; j++) {
			vid_t neb = nebrs[j];

			
		        #pragma omp critical
			{
			if (status_array[neb] > current_level + 1) {
			    status_array[neb] = current_level + 1;
			    // update something shared frontier variable
			    frontier ++;
			    //cout<<" frontier = "<< frontier<< endl;
			}
			}
		    }
		}
	    }
	    /* this is making things slow
	    // need to find a shared variable implementation
	    done = true;
	    for (int i = 0; i< array_size; i++) {
		    if (status_array[i] == 255){
			    done = false;
			    break;
		    }
	    }
	    */
	    current_level ++;
	    //cout<<"new current level = "<<current_level<<endl;
    }
    // loop through and print status array
    //cout << "printing label array " << endl;
    int max_level = 0;
    for(int i = 0; i < array_size; i++){
	//cout <<"index = "<<i<<" value = "<< label_array[i]<< endl;
	if (status_array[i] > max_level){ max_level = status_array[i];}
    }

    cout << "root = " << root << endl; 
    //print bfs tree here
    //i.e. how many vertex in each level

    // create array to track levels
    int level_array[max_level+1] = {0};
    for(int i = 0; i < array_size; i++){
	level_array[status_array[i]]++;
    }

    //print the array 
    for(int i = 0; i <= max_level; i++){
	cout<< "level "<< i << ": "<< level_array[i]<< " vertices"<< endl;
    }

    auto stop1 = high_resolution_clock::now();
    auto duration1 = duration_cast<microseconds>(stop1-start1);
    cout << "multi thread status array BFS takes " << duration1.count() << endl;
}
