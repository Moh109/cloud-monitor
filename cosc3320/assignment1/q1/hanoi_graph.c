/*
 * COSC 3320 - Assignment 1, Question 1
 * Towers of Hanoi on the graph G = (V,E) with
 *     V = { Start, A1, A2, A3, A4, Dest }
 *     E = { (Start,A1), (A1,A2), (A2,A3), (A3,A4), (A4,A1), (A1,Dest) }
 *
 * A disk may be moved from peg u to peg v only if (u,v) is an edge of G and the
 * usual Hanoi rule holds (v is empty, or the top disk of v is larger).
 *
 * Algorithm: graph-aware Frame-Stewart recursion.  See README.md for the
 * derivation, the correctness invariant and the complexity analysis.
 *
 *     TRANSFER(k, src, dst, A):        A = set of pegs that may be used
 *       k = 0 : nothing
 *       k = 1 : walk the disk along a shortest src->dst path inside G[A]
 *       k > 1 : pick spare x in A\{src,dst} and split 1 <= m < k, then
 *                 TRANSFER(m,   src, x,   A)
 *                 TRANSFER(k-m, src, dst, A\{x})
 *                 TRANSFER(m,   x,   dst, A)
 *
 * x and m are chosen by an exact dynamic program over (k, src, dst, A); since
 * |V| = 6 there are only 2^6 = 64 possible peg sets.
 *
 * Build: gcc -O2 -Wall -o hanoi_graph hanoi_graph.c
 * Usage: ./hanoi_graph            solve n = 1..10
 *        ./hanoi_graph N          solve n = N
 *        ./hanoi_graph MIN MAX    solve n = MIN..MAX
 *        ./hanoi_graph -s MIN MAX move counts only, no move list
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NPEG 6
#define FULL ((1 << NPEG) - 1)
#define INF  (~0ULL >> 1)
#define HEAD 100                 /* moves printed at the head of a long list */
#define TAIL 100                 /* moves printed at the tail of a long list */

enum { START = 0, A1 = 1, A2 = 2, A3 = 3, A4 = 4, DEST = 5 };
static const char *NAME[NPEG] = { "Start", "A1", "A2", "A3", "A4", "Dest" };

/* ------------------------------------------------------------------ graph - */

static int adj[NPEG][NPEG];

static void build_graph(void)
{
    static const int E[][2] = {
        { START, A1 }, { A1, A2 }, { A2, A3 }, { A3, A4 }, { A4, A1 }, { A1, DEST }
    };
    memset(adj, 0, sizeof adj);
    for (size_t i = 0; i < sizeof E / sizeof E[0]; i++) {
        adj[E[i][0]][E[i][1]] = 1;
        adj[E[i][1]][E[i][0]] = 1;
    }
}

/* dist[A][s][t] : length of a shortest s->t path using only pegs of the set A.
 * hop [A][s][t] : the first peg after s on such a path.                      */
static int dist[1 << NPEG][NPEG][NPEG];
static int hop [1 << NPEG][NPEG][NPEG];

static void all_pairs(void)
{
    for (int A = 0; A <= FULL; A++)
        for (int s = 0; s < NPEG; s++) {
            for (int t = 0; t < NPEG; t++) { dist[A][s][t] = -1; hop[A][s][t] = -1; }
            if (!(A >> s & 1)) continue;
            int q[NPEG], qh = 0, qt = 0;                     /* plain BFS */
            dist[A][s][s] = 0; q[qt++] = s;
            while (qh < qt) {
                int u = q[qh++];
                for (int v = 0; v < NPEG; v++)
                    if (adj[u][v] && (A >> v & 1) && dist[A][s][v] < 0) {
                        dist[A][s][v] = dist[A][s][u] + 1;
                        hop [A][s][v] = (u == s) ? v : hop[A][s][u];
                        q[qt++] = v;
                    }
            }
        }
}

/* ------------------------------------------------------- dynamic program - */

static unsigned long long *cost;     /* cost[k][A][s][t] = # moves            */
static signed char        *spare;    /* the peg x chosen                      */
static int                *split;    /* the split m chosen                    */

static size_t idx(int k, int A, int s, int t)
{
    return (((size_t)k * (FULL + 1) + A) * NPEG + s) * NPEG + t;
}

static void plan(int n)
{
    size_t cells = idx(n + 1, 0, 0, 0);
    cost  = malloc(cells * sizeof *cost);
    spare = malloc(cells * sizeof *spare);
    split = malloc(cells * sizeof *split);
    if (!cost || !spare || !split) { fprintf(stderr, "out of memory\n"); exit(1); }

    for (int A = 0; A <= FULL; A++)
        for (int s = 0; s < NPEG; s++)
            for (int t = 0; t < NPEG; t++) {
                cost[idx(0, A, s, t)] = 0;
                if (n >= 1)
                    cost[idx(1, A, s, t)] =
                        (s == t) ? 0 : (dist[A][s][t] < 0 ? INF : (unsigned long long)dist[A][s][t]);
            }

    for (int k = 2; k <= n; k++)
        for (int A = 0; A <= FULL; A++)
            for (int s = 0; s < NPEG; s++) {
                if (!(A >> s & 1)) continue;
                for (int t = 0; t < NPEG; t++) {
                    if (!(A >> t & 1)) continue;
                    if (s == t) { cost[idx(k, A, s, t)] = 0; continue; }
                    unsigned long long best = INF;
                    int bx = -1, bm = -1;
                    for (int x = 0; x < NPEG; x++) {
                        if (!(A >> x & 1) || x == s || x == t) continue;
                        int B = A & ~(1 << x);
                        if (dist[B][s][t] < 0) continue;      /* x is a cut vertex */
                        for (int m = 1; m < k; m++) {
                            unsigned long long a = cost[idx(m,     A, s, x)];
                            unsigned long long b = cost[idx(k - m, B, s, t)];
                            unsigned long long c = cost[idx(m,     A, x, t)];
                            if (a == INF || b == INF || c == INF) continue;
                            if (a + b + c < best) { best = a + b + c; bx = x; bm = m; }
                        }
                    }
                    cost [idx(k, A, s, t)] = best;
                    spare[idx(k, A, s, t)] = (signed char)bx;
                    split[idx(k, A, s, t)] = bm;
                }
            }
}

/* --------------------------------------------------- board + move output - */

static int  *peg[NPEG];              /* peg[p][0..hgt[p]-1], bottom first     */
static int   hgt[NPEG];
static long long nmove;              /* moves emitted so far                  */
static int   quiet;                  /* -s : print counts only                */
static long long total;              /* total moves of the current run        */

struct rec { int disk, from, to; };
static struct rec ring[TAIL];        /* circular buffer with the last moves   */

static void line(long long no, struct rec r)
{
    printf("%10lld.  disk %-3d  %-5s -> %-5s\n", no, r.disk, NAME[r.from], NAME[r.to]);
}

static void emit(int from, int to)
{
    if (hgt[from] == 0) {
        fprintf(stderr, "ILLEGAL: %s is empty\n", NAME[from]); exit(1);
    }
    int d = peg[from][hgt[from] - 1];
    if (!adj[from][to]) {
        fprintf(stderr, "ILLEGAL: (%s,%s) is not an edge\n", NAME[from], NAME[to]); exit(1);
    }
    if (hgt[to] > 0 && peg[to][hgt[to] - 1] < d) {
        fprintf(stderr, "ILLEGAL: disk %d onto smaller disk %d on %s\n",
                d, peg[to][hgt[to] - 1], NAME[to]); exit(1);
    }
    hgt[from]--;
    peg[to][hgt[to]++] = d;
    nmove++;

    if (quiet) return;
    struct rec r = { d, from, to };
    if (total <= HEAD + TAIL || nmove <= HEAD) line(nmove, r);
    else ring[nmove % TAIL] = r;                 /* remember, print at the end */
}

/* ------------------------------------------------------------- transfer - */

static void transfer(int k, int s, int t, int A)
{
    if (k <= 0 || s == t) return;
    if (k == 1) {                                /* walk it edge by edge */
        int cur = s;
        while (cur != t) { int nx = hop[A][cur][t]; emit(cur, nx); cur = nx; }
        return;
    }
    int x = spare[idx(k, A, s, t)];
    int m = split[idx(k, A, s, t)];
    if (x < 0) { fprintf(stderr, "no plan for k=%d %s->%s\n", k, NAME[s], NAME[t]); exit(1); }
    transfer(m,     s, x, A);
    transfer(k - m, s, t, A & ~(1 << x));
    transfer(m,     x, t, A);
}

/* ------------------------------------------------------------------ main - */

static long long optimum[] = {          /* exhaustive BFS, see hanoi_bfs.c */
    0, 2, 6, 10, 16, 22, 28, 36, 44, 52, 62, 74
};
#define NOPT ((int)(sizeof optimum / sizeof optimum[0]))

static void run(int n)
{
    for (int p = 0; p < NPEG; p++) { peg[p] = malloc((size_t)n * sizeof(int)); hgt[p] = 0; }
    for (int d = n; d >= 1; d--) peg[START][hgt[START]++] = d;   /* n at the bottom */

    total = (long long)cost[idx(n, FULL, START, DEST)];
    nmove = 0;

    printf("\n===============================================================\n");
    printf(" n = %d   moves = %lld   (lower bound 2n = %d", n, total, 2 * n);
    if (n < NOPT) printf(",  optimum = %lld", optimum[n]);
    printf(")\n");
    printf("===============================================================\n");

    transfer(n, START, DEST, FULL);

    if (!quiet && total > HEAD + TAIL) {
        printf("   ... %lld moves omitted ...\n", total - HEAD - TAIL);
        for (long long i = total - TAIL + 1; i <= total; i++) line(i, ring[i % TAIL]);
    }

    /* the algorithm is only trusted once the board agrees */
    if (nmove != total) { fprintf(stderr, "move count mismatch\n"); exit(1); }
    if (hgt[DEST] != n) { fprintf(stderr, "Dest does not hold all disks\n"); exit(1); }
    for (int i = 0; i < n; i++)
        if (peg[DEST][i] != n - i) { fprintf(stderr, "Dest is not sorted\n"); exit(1); }
    for (int p = 0; p < NPEG; p++)
        if (p != DEST && hgt[p] != 0) { fprintf(stderr, "%s not empty\n", NAME[p]); exit(1); }
    printf("  [verified: %lld legal moves, all %d disks stacked in order on Dest]\n", nmove, n);

    for (int p = 0; p < NPEG; p++) free(peg[p]);
}

int main(int argc, char **argv)
{
    int lo = 1, hi = 10, a = 1;
    if (a < argc && strcmp(argv[a], "-s") == 0) { quiet = 1; a++; }
    if (a < argc) lo = hi = atoi(argv[a++]);
    if (a < argc) hi = atoi(argv[a++]);
    if (lo < 1 || hi < lo) { fprintf(stderr, "usage: %s [-s] [MIN [MAX]]\n", argv[0]); return 1; }

    build_graph();
    all_pairs();
    plan(hi);

    printf("Towers of Hanoi on G = (V,E)\n");
    printf("  V = {Start, A1, A2, A3, A4, Dest}\n");
    printf("  E = {(Start,A1), (A1,A2), (A2,A3), (A3,A4), (A4,A1), (A1,Dest)}\n");

    for (int n = lo; n <= hi; n++) run(n);

    printf("\n--------------------------------------------------------------\n");
    printf("  n    moves   2n (lower bound)   optimum   3^n-1 (path only)\n");
    printf("--------------------------------------------------------------\n");
    for (int n = lo; n <= hi; n++) {
        unsigned long long p3 = 1;
        for (int i = 0; i < n; i++) p3 *= 3;
        printf("%3d %8llu %12d ", n, cost[idx(n, FULL, START, DEST)], 2 * n);
        if (n < NOPT) printf("%15lld ", optimum[n]); else printf("%15s ", "?");
        printf("%17llu\n", p3 - 1);
    }
    free(cost); free(spare); free(split);
    return 0;
}
