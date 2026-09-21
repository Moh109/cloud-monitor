CC     = gcc
CFLAGS = -O2 -Wall -Wextra

all: hanoi_graph hanoi_bfs

hanoi_graph: hanoi_graph.c
	$(CC) $(CFLAGS) -o $@ $<

hanoi_bfs: hanoi_bfs.c
	$(CC) $(CFLAGS) -o $@ $<

# part (b): the moves for n = 1..10
run: hanoi_graph
	./hanoi_graph 1 10 | tee output/hanoi_n1_to_n10.txt

# optimality check against exhaustive search
verify: hanoi_bfs
	./hanoi_bfs 11 | tee output/bfs_optimum.txt

clean:
	rm -f hanoi_graph hanoi_bfs

.PHONY: all run verify clean
