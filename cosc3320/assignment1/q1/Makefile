CC       = gcc
CXX      = g++
CFLAGS   = -O2 -Wall -Wextra
CXXFLAGS = -O2 -Wall -Wextra -std=c++17

all: hanoi_graph hanoi_bfs hanoi_graph_cpp

hanoi_graph: hanoi_graph.c
	$(CC) $(CFLAGS) -o $@ $<

hanoi_bfs: hanoi_bfs.c
	$(CC) $(CFLAGS) -o $@ $<

# C++ version: reads n from cin
hanoi_graph_cpp: hanoi_graph.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

# part (b): the moves for n = 1..10
run: hanoi_graph
	./hanoi_graph 1 10 | tee output/hanoi_n1_to_n10.txt

# optimality check against exhaustive search
verify: hanoi_bfs
	./hanoi_bfs 11 | tee output/bfs_optimum.txt

clean:
	rm -f hanoi_graph hanoi_bfs hanoi_graph_cpp

.PHONY: all run verify clean
