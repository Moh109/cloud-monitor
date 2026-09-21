#!/usr/bin/env python3
"""
COSC 3320 - Assignment 1, Question 1
Towers of Hanoi on the graph G = (V, E) with

    V = {Start, A1, A2, A3, A4, Dest}
    E = {(Start,A1), (A1,A2), (A2,A3), (A3,A4), (A4,A1), (A1,Dest)}

A disk may be moved from peg u to peg v only if (u,v) is an edge of G and the
usual Hanoi rule holds (v is empty, or the top disk of v is larger).

Algorithm -- graph-aware Frame-Stewart recursion.  See README.md for the
derivation, the correctness invariant and the complexity analysis.

    TRANSFER(k, src, dst, A):        A = the set of pegs that may be used
      k == 0 : nothing
      k == 1 : walk the disk one edge at a time along a shortest src->dst
               path inside the induced subgraph G[A]
      k >= 2 : pick a spare peg x in A\\{src,dst} and a split 1 <= m < k:
                 TRANSFER(m,     src, x,   A)        park m smallest on x
                 TRANSFER(k - m, src, dst, A\\{x})    move k-m largest
                 TRANSFER(m,     x,   dst, A)        put m smallest back

x and m are chosen by an exact dynamic program over (k, src, dst, A).  Because
|V| = 6 there are only 2**6 = 64 possible peg sets.

Usage:  python3 hanoi_graph.py             solve n = 1..10   (part b)
        python3 hanoi_graph.py 7           solve n = 7
        python3 hanoi_graph.py 1 40        solve n = 1..40
        python3 hanoi_graph.py -s 1 40     move counts only, no move list
"""

import sys
from collections import deque

PEG_NAME = ["Start", "A1", "A2", "A3", "A4", "Dest"]
START, A1, A2, A3, A4, DEST = range(6)
EDGES = [(START, A1), (A1, A2), (A2, A3), (A3, A4), (A4, A1), (A1, DEST)]

NPEG = len(PEG_NAME)
FULL = (1 << NPEG) - 1            # the peg set {Start, A1, A2, A3, A4, Dest}
HEAD = 100                        # moves printed at the head of a long list
TAIL = 100                        # moves printed at the tail of a long list

# exact optima from hanoi_bfs.py, for comparison only
OPTIMUM = {1: 2, 2: 6, 3: 10, 4: 16, 5: 22, 6: 28,
           7: 36, 8: 44, 9: 52, 10: 62, 11: 74}


# --------------------------------------------------------------------- graph

def build_adjacency():
    adj = [set() for _ in range(NPEG)]
    for u, v in EDGES:
        adj[u].add(v)
        adj[v].add(u)
    return adj


ADJ = build_adjacency()


def all_pairs():
    """dist[A][s][t] = length of a shortest s->t path using only pegs of A.
       hop [A][s][t] = the first peg after s on such a path (None if none)."""
    dist = [[[None] * NPEG for _ in range(NPEG)] for _ in range(FULL + 1)]
    hop = [[[None] * NPEG for _ in range(NPEG)] for _ in range(FULL + 1)]
    for A in range(FULL + 1):
        for s in range(NPEG):
            if not A >> s & 1:
                continue
            dist[A][s][s] = 0
            queue = deque([s])
            while queue:                                   # plain BFS in G[A]
                u = queue.popleft()
                for v in ADJ[u]:
                    if A >> v & 1 and dist[A][s][v] is None:
                        dist[A][s][v] = dist[A][s][u] + 1
                        hop[A][s][v] = v if u == s else hop[A][s][u]
                        queue.append(v)
    return dist, hop


DIST, HOP = all_pairs()


# ----------------------------------------------------------- dynamic program

def plan(n):
    """cost[k][A][s][t] -> (moves, spare peg x, split m); the Frame-Stewart DP."""
    cost = [[[[None] * NPEG for _ in range(NPEG)]
             for _ in range(FULL + 1)] for _ in range(n + 1)]

    for A in range(FULL + 1):
        for s in range(NPEG):
            for t in range(NPEG):
                cost[0][A][s][t] = (0, None, None)
                if n >= 1:
                    d = 0 if s == t else DIST[A][s][t]
                    cost[1][A][s][t] = (d, None, None) if d is not None else None

    for k in range(2, n + 1):
        for A in range(FULL + 1):
            for s in range(NPEG):
                if not A >> s & 1:
                    continue
                for t in range(NPEG):
                    if not A >> t & 1:
                        continue
                    if s == t:
                        cost[k][A][s][t] = (0, None, None)
                        continue
                    best = None
                    for x in range(NPEG):
                        if not A >> x & 1 or x in (s, t):
                            continue
                        B = A & ~(1 << x)
                        if DIST[B][s][t] is None:       # x is a cut vertex of G[A]
                            continue
                        for m in range(1, k):
                            parts = (cost[m][A][s][x],
                                     cost[k - m][B][s][t],
                                     cost[m][A][x][t])
                            if any(p is None for p in parts):
                                continue
                            total = sum(p[0] for p in parts)
                            if best is None or total < best[0]:
                                best = (total, x, m)
                    cost[k][A][s][t] = best
    return cost


# ------------------------------------------------------------------- solving

class Board:
    """The six pegs, with every move checked against the rules of the game."""

    def __init__(self, n):
        self.n = n
        self.peg = [[] for _ in range(NPEG)]       # bottom first
        self.peg[START] = list(range(n, 0, -1))    # disk n at the bottom

    def move(self, src, dst):
        if not self.peg[src]:
            raise ValueError(f"{PEG_NAME[src]} is empty")
        disk = self.peg[src][-1]
        if dst not in ADJ[src]:
            raise ValueError(f"({PEG_NAME[src]},{PEG_NAME[dst]}) is not an edge of G")
        if self.peg[dst] and self.peg[dst][-1] < disk:
            raise ValueError(f"disk {disk} onto smaller disk {self.peg[dst][-1]} "
                             f"on {PEG_NAME[dst]}")
        self.peg[dst].append(self.peg[src].pop())
        return disk, src, dst

    def solved(self):
        return (self.peg[DEST] == list(range(self.n, 0, -1))
                and all(not self.peg[p] for p in range(NPEG) if p != DEST))


def transfer(board, cost, k, s, t, A):
    """Generator of legal moves that carries the top k disks from s to t."""
    if k <= 0 or s == t:
        return
    if k == 1:                                     # walk it edge by edge
        cur = s
        while cur != t:
            nxt = HOP[A][cur][t]
            yield board.move(cur, nxt)
            cur = nxt
        return
    entry = cost[k][A][s][t]
    if entry is None:
        raise ValueError(f"no plan for k={k} {PEG_NAME[s]}->{PEG_NAME[t]}")
    _, x, m = entry
    yield from transfer(board, cost, m,     s, x, A)
    yield from transfer(board, cost, k - m, s, t, A & ~(1 << x))
    yield from transfer(board, cost, m,     x, t, A)


def fmt(no, move):
    disk, src, dst = move
    return f"{no:10d}.  disk {disk:<3d}  {PEG_NAME[src]:<5s} -> {PEG_NAME[dst]:<5s}"


def run(n, cost, quiet=False):
    total = cost[n][FULL][START][DEST][0]
    board = Board(n)

    print()
    print("=" * 63)
    line = f" n = {n}   moves = {total}   (lower bound 2n = {2 * n}"
    if n in OPTIMUM:
        line += f",  optimum = {OPTIMUM[n]}"
    print(line + ")")
    print("=" * 63)

    tail = deque(maxlen=TAIL)
    count = 0
    for move in transfer(board, cost, n, START, DEST, FULL):
        count += 1
        if quiet:
            continue
        if total <= HEAD + TAIL or count <= HEAD:
            print(fmt(count, move))
        else:
            tail.append((count, move))

    if not quiet and total > HEAD + TAIL:
        print(f"   ... {total - HEAD - TAIL} moves omitted ...")
        for no, move in tail:
            print(fmt(no, move))

    # the algorithm is only trusted once the board agrees
    assert count == total, f"emitted {count} moves, planned {total}"
    assert board.solved(), "disks are not stacked in order on Dest"
    print(f"  [verified: {count} legal moves, "
          f"all {n} disks stacked in order on Dest]")
    return total


def main(argv):
    args = argv[1:]
    quiet = False
    if args and args[0] == "-s":
        quiet = True
        args = args[1:]
    lo, hi = 1, 10
    if len(args) == 1:
        lo = hi = int(args[0])
    elif len(args) >= 2:
        lo, hi = int(args[0]), int(args[1])
    if lo < 1 or hi < lo:
        sys.exit("usage: hanoi_graph.py [-s] [MIN [MAX]]")

    cost = plan(hi)

    print("Towers of Hanoi on G = (V,E)")
    print("  V = {Start, A1, A2, A3, A4, Dest}")
    print("  E = {(Start,A1), (A1,A2), (A2,A3), (A3,A4), (A4,A1), (A1,Dest)}")

    for n in range(lo, hi + 1):
        run(n, cost, quiet)

    print()
    print("-" * 62)
    print("  n    moves   2n (lower bound)   optimum   3^n-1 (path only)")
    print("-" * 62)
    for n in range(lo, hi + 1):
        moves = cost[n][FULL][START][DEST][0]
        opt = OPTIMUM.get(n, "?")
        print(f"{n:3d} {moves:8d} {2 * n:12d} {opt:>15} {3 ** n - 1:17d}")


if __name__ == "__main__":
    main(sys.argv)
