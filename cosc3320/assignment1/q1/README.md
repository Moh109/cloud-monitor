# COSC 3320 — Assignment 1, Question 1
## Towers of Hanoi on the graph `G = (V, E)`

```
V = { Start, A1, A2, A3, A4, Dest }
E = { (Start,A1), (A1,A2), (A2,A3), (A3,A4), (A4,A1), (A1,Dest) }
```

A disk may be moved from peg `u` to peg `v` only when `(u,v) ∈ E` **and** the
usual Hanoi rule holds (`v` is empty, or the top disk of `v` is larger).

---

## 1(a) — The algorithm, and its time and space complexity

### Step 1: read the structure of the graph

| peg | neighbours |
|------|-----------------------|
| Start | A1 |
| A1 | Start, A2, A4, Dest |
| A2 | A1, A3 |
| A3 | A2, A4 |
| A4 | A1, A3 |
| Dest | A1 |

```
          Start           Dest
               \         /
                \       /
                 (  A1  )
                /        \
             (A2)        (A4)
                \        /
                 (  A3  )
```

Three facts drive everything:

1. **`A1` is a cut vertex, and `Start` and `Dest` are pendant vertices hanging
   off it.** Deleting `A1` splits `G` into `{Start}`, `{Dest}` and the path
   `A2–A3–A4`. Therefore *every* disk must travel `Start → A1 → Dest`.
2. **`G` is triangle-free** (`A1A2A3A4` is a 4-cycle, and `Start`, `Dest` are
   leaves). No three pegs are mutually adjacent, so the classical 3-peg
   `2ⁿ − 1` algorithm never applies directly to any triple of pegs.
3. `d(Start,Dest) = 2`, but `d(Start,A3) = d(Dest,A3) = 3` — `A3` is the awkward
   peg, reachable only *through* `A2` or `A4`.

### Step 2: a lower bound

By fact 1 every disk needs at least two moves, so for any algorithm

> **T(n) ≥ 2n.**

A sharper structural consequence: at the moment the largest disk leaves `Start`
it must land on `A1`, so `A1` is empty and the other `n−1` disks are parked on
`{A2, A3, A4, Dest}`; at the moment it moves `A1 → Dest`, `Dest` must be empty.
So the whole problem is *park the n−1 smaller disks inside the 4-cycle, walk the
biggest disk across, unpark*. Since `Start` and `Dest` are symmetric (both
pendant at `A1`), the unparking phase can always be taken to be the parking
phase run backwards with `Start` and `Dest` exchanged.

A naive solution follows immediately: ignore `A2, A3, A4` and use only the path
`Start–A1–Dest`. That is "three-in-a-row" Hanoi and costs **3ⁿ − 1** moves
(59 048 for `n = 10`). We can do enormously better by using the 4-cycle.

### Step 3: the algorithm — graph-aware Frame–Stewart

Let `A ⊆ V` be the set of pegs currently allowed.

```
TRANSFER(k, src, dst, A):                    # move the top k disks src -> dst
    if k == 0:  return
    if k == 1:  walk the disk one edge at a time along a shortest
                src -> dst path inside the induced subgraph G[A]
    else:
        choose a spare peg  x ∈ A \ {src, dst}  and a split  1 ≤ m < k
        TRANSFER(m,     src, x,   A)          # park the m smallest on x
        TRANSFER(k - m, src, dst, A \ {x})    # move the k-m largest, avoiding x
        TRANSFER(m,     x,   dst, A)          # put the m smallest back on top
```

Top-level call: `TRANSFER(n, Start, Dest, V)`.

**Correctness.** Invariant: whenever `TRANSFER(k, src, dst, A)` is entered,
every peg of `A` is either empty or carries only disks *larger* than all `k`
disks being moved, and every peg outside `A` carries only *smaller* disks.
The invariant holds at the top level, and each of the three recursive calls
preserves it — step 2 removes `x` from `A` precisely because `x` now holds the
`m` smallest disks. Under the invariant the `k = 1` case is legal: the disk may
be pushed onto any peg of `A`, so any path of `G[A]` is walkable. Induction on
`k` gives correctness.

**Choosing `x` and `m`.** They are picked by an exact dynamic program, not by a
guess. Since `|V| = 6` there are only `2⁶ = 64` peg sets:

```
C[0][src][dst][A] = 0
C[1][src][dst][A] = dist_{G[A]}(src, dst)                       (BFS in G[A])
C[k][src][dst][A] = min over x ∈ A\{src,dst}, 1 ≤ m < k of
                      C[m][src][x][A] + C[k-m][src][dst][A\{x}] + C[m][x][dst][A]
```

This is the Frame–Stewart recursion generalised from "p pegs" to "an arbitrary
graph of pegs": the peg set shrinks *and* the cost of a single move depends on
the distance inside the surviving subgraph.

### Step 4: complexity

Let `T(n) = C[n][Start][Dest][V]` be the number of moves, and let `p = |V| = 6`
(a constant).

**Number of moves.** The first values are

```
n     :  1   2   3   4   5   6   7   8   9  10  11  12 ...  20 ...   40 ...  100
T(n)  :  2   6  10  16  22  30  38  46  56  70  84  98 ... 254 ... 1130 ... 11142
```

Fitting the computed values up to `n = 200` gives `log₂ T(n) / n^(1/3) ≈ 2.8–3.0`,
i.e.

> **T(n) = 2^Θ(n^(1/3))** — super-polynomial, but *sub-exponential*.

This is the expected shape: for `p` fully-connected pegs Frame–Stewart gives
`2^Θ(n^(1/(p-2)))`, and this graph behaves like roughly five usable pegs because
`A3` sits two hops from the hub. It is bounded below by `2n` and is dramatically
smaller than the `3ⁿ − 1` of the path-only solution.

**Time.** Filling the DP table costs `O(n² · p³ · 2^p) = O(n²)` for constant `p`;
generating the answer costs `Θ(T(n))` because `TRANSFER` does `O(1)` work per
move emitted. Total

> **Time = Θ(n² + T(n)) = Θ(T(n))** for all but very small `n`.

**Space.** The DP table has `n · p² · 2^p = Θ(n)` entries; the recursion depth of
`TRANSFER` is at most `n` (each call strictly decreases `k`); the peg contents
need `Θ(n)` words and are only needed for printing/validating.

> **Space = Θ(n) auxiliary** (plus `Θ(T(n))` only if you choose to *store* the
> whole move list instead of streaming it, as the program does).

### Step 5: how good is it?

`hanoi_bfs.c` searches the entire state space (all `6ⁿ` configurations) by BFS
and returns the true optimum. Comparing:

| n | 2n (lower bound) | **this algorithm** | true optimum | path-only `3ⁿ−1` |
|---|---|---|---|---|
| 1 | 2 | **2** | 2 | 2 |
| 2 | 4 | **6** | 6 | 8 |
| 3 | 6 | **10** | 10 | 26 |
| 4 | 8 | **16** | 16 | 80 |
| 5 | 10 | **22** | 22 | 242 |
| 6 | 12 | **30** | 28 | 728 |
| 7 | 14 | **38** | 36 | 2 186 |
| 8 | 16 | **46** | 44 | 6 560 |
| 9 | 18 | **56** | 52 | 19 682 |
| 10 | 20 | **70** | 62 | 59 048 |
| 11 | 22 | **84** | 74 | 177 146 |

The algorithm is **optimal for n ≤ 5** and stays within **13.5 %** of the optimum
through `n = 11`, while using `Θ(n)` space instead of the `Θ(6ⁿ)` that exhaustive
search needs.

---

## 1(b) — Implementation

### Files

The program is given in **Python** and in **C**; both implement exactly the same
algorithm and produce byte-identical move lists.

| file | purpose |
|---|---|
| `hanoi_graph.py` | the algorithm of part (a); prints every move |
| `hanoi_bfs.py` | exhaustive BFS, exact optimum, used only to check part (a) |
| `hanoi_graph.c`, `hanoi_bfs.c` | the same two programs in C (faster: BFS reaches `n = 12`) |
| `Makefile` | `make`, `make run`, `make verify` for the C versions |
| `output/hanoi_n1_to_n10.txt` | the required output for `n = 1 … 10` |
| `output/bfs_optimum.txt` | the optimum table for `n = 1 … 11` |

### Build and run

```sh
python3 hanoi_graph.py            # n = 1..10, every move printed   (part b)
python3 hanoi_graph.py 7          # just n = 7
python3 hanoi_graph.py 1 40       # n = 1..40
python3 hanoi_graph.py -s 1 40    # move counts only
python3 hanoi_bfs.py 8            # exact optima, n = 1..8

make && ./hanoi_graph             # the C version, same output
./hanoi_bfs 11                    # exact optima, n = 1..11 (~40 s, 360 MB)
```

Every move is printed as

```
         5.  disk 3    Start -> A1
```

The program **validates each move as it makes it** (the pegs must be adjacent in
`G`, the disk must be on top of its peg, and it may not land on a smaller disk)
and checks at the end that all `n` disks are stacked in order on `Dest` and every
other peg is empty. If a move list is longer than 200 moves it prints the first
100 and the last 100 with a `... k moves omitted ...` marker, as the assignment
allows.

### Results for n = 1 … 10

All ten move lists are short enough to print in full; they are in
`output/hanoi_n1_to_n10.txt`.

```
  n    moves   2n (lower bound)   optimum   3^n-1 (path only)
  1        2            2               2                 2
  2        6            4               6                 8
  3       10            6              10                26
  4       16            8              16                80
  5       22           10              22               242
  6       30           12              28               728
  7       38           14              36              2186
  8       46           16              44              6560
  9       56           18              52             19682
 10       70           20              62             59048
```

For example `n = 3` (10 moves — optimal):

```
 1.  disk 1   Start -> A1        6.  disk 3   A1    -> Dest
 2.  disk 1   A1    -> A2        7.  disk 2   A4    -> A1
 3.  disk 2   Start -> A1        8.  disk 2   A1    -> Dest
 4.  disk 2   A1    -> A4        9.  disk 1   A2    -> A1
 5.  disk 3   Start -> A1       10.  disk 1   A1    -> Dest
```

You can see the structure of part (a) in it: disks 1 and 2 are parked inside the
4-cycle (on `A2` and `A4`), disk 3 walks `Start → A1 → Dest`, and then the
parking phase is replayed backwards into `Dest`.
