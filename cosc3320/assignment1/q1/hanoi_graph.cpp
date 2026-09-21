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
 * Build: g++ -O2 -Wall -std=c++17 -o hanoi_graph_cpp hanoi_graph.cpp
 * Run  : ./hanoi_graph_cpp        then type the number of disks when prompted
 *        echo "1 2 3 4 5 6 7 8 9 10 0" | ./hanoi_graph_cpp     (part b in one go)
 */

#include <iostream>
#include <iomanip>
#include <vector>
#include <deque>
#include <array>
#include <limits>
#include <map>

using namespace std;

const int NPEG = 6;
const int FULL = (1 << NPEG) - 1;
const long long INF = numeric_limits<long long>::max() / 4;
const int HEAD = 100;                    // moves printed at the head of a long list
const int TAIL = 100;                    // moves printed at the tail of a long list

enum { START = 0, A1 = 1, A2 = 2, A3 = 3, A4 = 4, DEST = 5 };
const char *NAME[NPEG] = { "Start", "A1", "A2", "A3", "A4", "Dest" };

// exact optima from hanoi_bfs.cpp / hanoi_bfs.py, for comparison only
const map<int, long long> OPTIMUM = {
    {1,2},{2,6},{3,10},{4,16},{5,22},{6,28},{7,36},{8,44},{9,52},{10,62},{11,74}
};

// ----------------------------------------------------------------- graph ---

static bool adjacent[NPEG][NPEG];

static void build_graph()
{
    const int E[][2] = {
        { START, A1 }, { A1, A2 }, { A2, A3 }, { A3, A4 }, { A4, A1 }, { A1, DEST }
    };
    for (auto &e : E) adjacent[e[0]][e[1]] = adjacent[e[1]][e[0]] = true;
}

// dist[A][s][t] : length of a shortest s->t path using only the pegs of set A
// hop [A][s][t] : the first peg after s on such a path
static int dist[1 << NPEG][NPEG][NPEG];
static int hop [1 << NPEG][NPEG][NPEG];

static void all_pairs()
{
    for (int A = 0; A <= FULL; A++)
        for (int s = 0; s < NPEG; s++) {
            for (int t = 0; t < NPEG; t++) { dist[A][s][t] = -1; hop[A][s][t] = -1; }
            if (!(A >> s & 1)) continue;
            deque<int> q;                                        // plain BFS
            dist[A][s][s] = 0; q.push_back(s);
            while (!q.empty()) {
                int u = q.front(); q.pop_front();
                for (int v = 0; v < NPEG; v++)
                    if (adjacent[u][v] && (A >> v & 1) && dist[A][s][v] < 0) {
                        dist[A][s][v] = dist[A][s][u] + 1;
                        hop [A][s][v] = (u == s) ? v : hop[A][s][u];
                        q.push_back(v);
                    }
            }
        }
}

// ------------------------------------------------------ dynamic program ---

struct Step { long long cost = INF; int spare = -1; int split = -1; };

static vector<Step> table;               // table[idx(k,A,s,t)]
static int planned = -1;                 // largest n the table was built for

static size_t idx(int k, int A, int s, int t)
{
    return (((size_t)k * (FULL + 1) + A) * NPEG + s) * NPEG + t;
}

static void plan(int n)
{
    if (n <= planned) return;
    table.assign(idx(n + 1, 0, 0, 0), Step{});

    for (int A = 0; A <= FULL; A++)
        for (int s = 0; s < NPEG; s++)
            for (int t = 0; t < NPEG; t++) {
                table[idx(0, A, s, t)].cost = 0;
                if (n >= 1)
                    table[idx(1, A, s, t)].cost =
                        (s == t) ? 0 : (dist[A][s][t] < 0 ? INF : dist[A][s][t]);
            }

    for (int k = 2; k <= n; k++)
        for (int A = 0; A <= FULL; A++)
            for (int s = 0; s < NPEG; s++) {
                if (!(A >> s & 1)) continue;
                for (int t = 0; t < NPEG; t++) {
                    if (!(A >> t & 1)) continue;
                    Step &cell = table[idx(k, A, s, t)];
                    if (s == t) { cell.cost = 0; continue; }
                    for (int x = 0; x < NPEG; x++) {
                        if (!(A >> x & 1) || x == s || x == t) continue;
                        int B = A & ~(1 << x);
                        if (dist[B][s][t] < 0) continue;     // x is a cut vertex
                        for (int m = 1; m < k; m++) {
                            long long a = table[idx(m,     A, s, x)].cost;
                            long long b = table[idx(k - m, B, s, t)].cost;
                            long long c = table[idx(m,     A, x, t)].cost;
                            if (a >= INF || b >= INF || c >= INF) continue;
                            if (a + b + c < cell.cost)
                                cell = Step{ a + b + c, x, m };
                        }
                    }
                }
            }
    planned = n;
}

// --------------------------------------------------- board + move output ---

struct Move { int disk, from, to; };

static vector<vector<int>> peg;          // peg[p] bottom first
static long long nmove, total;
static deque<pair<long long, Move>> tailbuf;

static void print_move(long long no, const Move &m)
{
    cout << setw(10) << no << ".  disk " << left << setw(3) << m.disk
         << "  " << setw(5) << NAME[m.from] << " -> " << setw(5) << NAME[m.to]
         << right << "\n";
}

static void emit(int from, int to)
{
    if (peg[from].empty()) { cerr << "ILLEGAL: " << NAME[from] << " is empty\n"; exit(1); }
    int d = peg[from].back();
    if (!adjacent[from][to]) {
        cerr << "ILLEGAL: (" << NAME[from] << "," << NAME[to] << ") is not an edge\n"; exit(1);
    }
    if (!peg[to].empty() && peg[to].back() < d) {
        cerr << "ILLEGAL: disk " << d << " onto smaller disk " << peg[to].back()
             << " on " << NAME[to] << "\n"; exit(1);
    }
    peg[from].pop_back();
    peg[to].push_back(d);
    nmove++;

    Move m{ d, from, to };
    if (total <= HEAD + TAIL || nmove <= HEAD) print_move(nmove, m);
    else {
        tailbuf.push_back({ nmove, m });                 // keep only the last TAIL
        if ((int)tailbuf.size() > TAIL) tailbuf.pop_front();
    }
}

// ------------------------------------------------------------ transfer ---

static void transfer(int k, int s, int t, int A)
{
    if (k <= 0 || s == t) return;
    if (k == 1) {                                        // walk it edge by edge
        int cur = s;
        while (cur != t) { int nx = hop[A][cur][t]; emit(cur, nx); cur = nx; }
        return;
    }
    const Step &st = table[idx(k, A, s, t)];
    if (st.spare < 0) {
        cerr << "no plan for k=" << k << " " << NAME[s] << "->" << NAME[t] << "\n"; exit(1);
    }
    transfer(st.split,     s, st.spare, A);
    transfer(k - st.split, s, t,        A & ~(1 << st.spare));
    transfer(st.split,     st.spare, t, A);
}

// ----------------------------------------------------------------- run ---

static void run(int n)
{
    plan(n);
    peg.assign(NPEG, {});
    for (int d = n; d >= 1; d--) peg[START].push_back(d);   // disk n at the bottom

    total = table[idx(n, FULL, START, DEST)].cost;
    nmove = 0;
    tailbuf.clear();

    cout << "\n" << string(63, '=') << "\n";
    cout << " n = " << n << "   moves = " << total << "   (lower bound 2n = " << 2 * n;
    auto it = OPTIMUM.find(n);
    if (it != OPTIMUM.end()) cout << ",  optimum = " << it->second;
    cout << ")\n" << string(63, '=') << "\n";

    transfer(n, START, DEST, FULL);

    if (total > HEAD + TAIL) {
        cout << "   ... " << total - HEAD - TAIL << " moves omitted ...\n";
        for (auto &e : tailbuf) print_move(e.first, e.second);
    }

    // the algorithm is only trusted once the board agrees
    if (nmove != total) { cerr << "move count mismatch\n"; exit(1); }
    if ((int)peg[DEST].size() != n) { cerr << "Dest does not hold all disks\n"; exit(1); }
    for (int i = 0; i < n; i++)
        if (peg[DEST][i] != n - i) { cerr << "Dest is not sorted\n"; exit(1); }
    for (int p = 0; p < NPEG; p++)
        if (p != DEST && !peg[p].empty()) { cerr << NAME[p] << " not empty\n"; exit(1); }

    cout << "  [verified: " << nmove << " legal moves, all " << n
         << " disks stacked in order on Dest]\n";
}

// ---------------------------------------------------------------- main ---

int main()
{
    build_graph();
    all_pairs();

    cout << "Towers of Hanoi on G = (V,E)\n";
    cout << "  V = {Start, A1, A2, A3, A4, Dest}\n";
    cout << "  E = {(Start,A1), (A1,A2), (A2,A3), (A3,A4), (A4,A1), (A1,Dest)}\n";

    vector<pair<int, long long>> done;

    for (;;) {
        cout << "\nEnter the number of disks n (0 to quit): " << flush;

        int n;
        if (!(cin >> n)) {                       // end of input, or a non-number
            if (cin.eof()) { cout << "\n"; break; }
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cout << "  please type a whole number.\n";
            continue;
        }
        if (n == 0) break;
        if (n < 0)  { cout << "  n must be positive.\n"; continue; }
        if (n > 60) { cout << "  n is too large; please use n <= 60.\n"; continue; }

        run(n);
        done.push_back({ n, total });
    }

    if (!done.empty()) {
        cout << "\n" << string(62, '-') << "\n";
        cout << "  n    moves   2n (lower bound)   optimum   3^n-1 (path only)\n";
        cout << string(62, '-') << "\n";
        for (auto &e : done) {
            cout << setw(3) << e.first << setw(9) << e.second << setw(13) << 2 * e.first;
            auto it = OPTIMUM.find(e.first);
            if (it != OPTIMUM.end()) cout << setw(16) << it->second;
            else                     cout << setw(16) << "?";
            unsigned long long p3 = 1;
            for (int i = 0; i < e.first && i < 40; i++) p3 *= 3;
            cout << setw(18) << p3 - 1 << "\n";
        }
    }
    return 0;
}
