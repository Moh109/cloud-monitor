/*
 * COSC 3320 - Assignment 1, Question 1 : verification tool.
 *
 * Exhaustive breadth-first search over the whole state space, to obtain the
 * EXACT minimum number of moves and so measure how good hanoi_graph.c is.
 *
 * A configuration of n disks is the vector (p_1,...,p_n) of the pegs the disks
 * sit on, encoded as an n-digit base-6 number, so the state space has exactly
 * 6^n states.  BFS runs backwards from the goal (every disk on Dest); moves are
 * reversible, so the distance it computes for the start state is the optimum.
 *
 * Time  Theta(n * 6^n),  space Theta(6^n).  Practical only up to n = 12 or so:
 * this is a checker, not the algorithm of part (a).
 *
 * Build: gcc -O2 -Wall -o hanoi_bfs hanoi_bfs.c
 * Usage: ./hanoi_bfs [NMAX]        (default 11; n = 12 needs ~5 GB)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define NPEG 6
enum { START = 0, DEST = 5 };

/* adjacency of G, -1 terminated */
static const int ADJ[NPEG][5] = {
    {  1, -1, -1, -1, -1 },   /* Start */
    {  0,  2,  4,  5, -1 },   /* A1    */
    {  1,  3, -1, -1, -1 },   /* A2    */
    {  2,  4, -1, -1, -1 },   /* A3    */
    {  3,  1, -1, -1, -1 },   /* A4    */
    {  1, -1, -1, -1, -1 }    /* Dest  */
};

int main(int argc, char **argv)
{
    int nmax = argc > 1 ? atoi(argv[1]) : 11;

    printf("  n   states (6^n)   optimal moves\n");
    printf("-----------------------------------\n");

    for (int n = 1; n <= nmax; n++) {
        uint64_t pw[16]; pw[0] = 1;
        for (int i = 1; i <= n; i++) pw[i] = pw[i - 1] * 6;
        uint64_t nstate = pw[n];
        uint64_t goal   = nstate - 1;            /* 555...5 in base 6 = all Dest */

        uint8_t *dist = malloc(nstate);
        if (!dist) { fprintf(stderr, "cannot allocate %llu bytes for n=%d\n",
                             (unsigned long long)nstate, n); return 1; }
        memset(dist, 0xFF, nstate);

        size_t ccap = 1024, ncap = 1024, clen = 0, nlen;
        uint32_t *cur = malloc(ccap * sizeof *cur);
        uint32_t *nxt = malloc(ncap * sizeof *nxt);

        dist[goal] = 0;
        cur[clen++] = (uint32_t)goal;

        for (int d = 0; clen && dist[0] == 0xFF; d++) {
            nlen = 0;
            for (size_t i = 0; i < clen; i++) {
                uint64_t s = cur[i], t = s;
                int pos[16], top[NPEG] = { -1, -1, -1, -1, -1, -1 };
                for (int k = 0; k < n; k++) { pos[k] = (int)(t % 6); t /= 6; }
                for (int k = n - 1; k >= 0; k--) top[pos[k]] = k;   /* smallest wins */

                for (int p = 0; p < NPEG; p++) {
                    int dk = top[p];
                    if (dk < 0) continue;
                    for (int j = 0; ADJ[p][j] >= 0; j++) {
                        int q = ADJ[p][j];
                        if (top[q] >= 0 && top[q] < dk) continue;   /* smaller on top */
                        uint64_t ns = s + (uint64_t)(q - p) * pw[dk];
                        if (dist[ns] != 0xFF) continue;
                        dist[ns] = (uint8_t)(d + 1);
                        if (nlen == ncap) { ncap *= 2; nxt = realloc(nxt, ncap * sizeof *nxt); }
                        nxt[nlen++] = (uint32_t)ns;
                    }
                }
            }
            uint32_t *sw = cur; cur = nxt; nxt = sw;
            size_t sc = ccap; ccap = ncap; ncap = sc;
            clen = nlen;
        }

        printf("%3d %14llu %15d\n", n, (unsigned long long)nstate, dist[START]);
        fflush(stdout);
        free(dist); free(cur); free(nxt);
    }
    return 0;
}
