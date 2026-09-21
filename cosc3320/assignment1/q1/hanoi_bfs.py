#!/usr/bin/env python3
"""
COSC 3320 - Assignment 1, Question 1 : verification tool.

Exhaustive breadth-first search over the whole state space, to obtain the EXACT
minimum number of moves and so measure how good hanoi_graph.py is.

A configuration of n disks is the vector (p_1, ..., p_n) of the pegs the disks
sit on, encoded as an n-digit base-6 number, so the state space has exactly 6**n
states.  The search runs backwards from the goal (every disk on Dest); moves are
reversible, so the distance it finds for the start state is the optimum.

Time Theta(n * 6**n), space Theta(6**n).  This is a checker, not the algorithm
of part (a) -- it is only practical for small n (n = 10 needs a 60 MB table and
a few minutes in Python; the C version in hanoi_bfs.c reaches n = 12).

Usage:  python3 hanoi_bfs.py [NMAX]        (default 8)
"""

import sys
from time import perf_counter

PEG_NAME = ["Start", "A1", "A2", "A3", "A4", "Dest"]
START, A1, A2, A3, A4, DEST = range(6)
EDGES = [(START, A1), (A1, A2), (A2, A3), (A3, A4), (A4, A1), (A1, DEST)]
NPEG = len(PEG_NAME)

ADJ = [[] for _ in range(NPEG)]
for _u, _v in EDGES:
    ADJ[_u].append(_v)
    ADJ[_v].append(_u)

UNSEEN = 0xFF


def optimum(n):
    """Exact minimum number of moves to carry n disks from Start to Dest."""
    pw = [6 ** i for i in range(n + 1)]
    goal = 6 ** n - 1                      # 555...5 in base 6 = every disk on Dest
    start = 0                              # 000...0                = every disk on Start

    dist = bytearray([UNSEEN]) * (6 ** n)
    dist[goal] = 0
    frontier = [goal]
    depth = 0

    while frontier and dist[start] == UNSEEN:
        nxt = []
        for s in frontier:
            top = [None] * NPEG
            t = s
            pos = []
            for _ in range(n):
                pos.append(t % 6)
                t //= 6
            for k in range(n - 1, -1, -1):     # smallest disk wins each peg
                top[pos[k]] = k

            for p in range(NPEG):
                dk = top[p]
                if dk is None:
                    continue
                step = pw[dk]
                for q in ADJ[p]:
                    tq = top[q]
                    if tq is not None and tq < dk:      # a smaller disk is in the way
                        continue
                    ns = s + (q - p) * step
                    if dist[ns] == UNSEEN:
                        dist[ns] = depth + 1
                        nxt.append(ns)
        frontier = nxt
        depth += 1

    return dist[start]


def main(argv):
    nmax = int(argv[1]) if len(argv) > 1 else 8

    print("  n   states (6^n)   optimal moves    seconds")
    print("-" * 49)
    for n in range(1, nmax + 1):
        t0 = perf_counter()
        best = optimum(n)
        print(f"{n:3d} {6 ** n:14d} {best:15d} {perf_counter() - t0:10.2f}")
        sys.stdout.flush()


if __name__ == "__main__":
    main(sys.argv)
