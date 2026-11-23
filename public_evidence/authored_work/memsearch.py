"""Shortest path over serial-data schedules: SDF butterfly on time bit p costs
2^p words (and cycles); exchanging time bits i<j costs 2^j-2^i (Garrido's
elementary bit exchange).  Index bits n5..n0 must be processed in that order
(radix-2 precedence); n_j becomes k_(5-j).  Goal: natural output, k_i at bit i.
"""
import heapq
import itertools

NB = 6


def search():
    start = (tuple(range(NB)), 0)       # pos -> logical bit (j means n_j / k_(5-j))
    goal_perm = tuple(5 - i for i in range(NB))   # position i must hold logical 5-i
    dist = {start: 0}
    prev = {}
    pq = [(0, start)]
    while pq:
        d, (perm, done) = heapq.heappop(pq)
        if d > dist[(perm, done)]:
            continue
        if done == NB and perm == goal_perm:
            path = []
            s = (perm, done)
            while s in prev:
                s, op = prev[s]
                path.append(op)
            return d, path[::-1]
        nxt = []
        if done < NB:
            logical = 5 - done
            p = perm.index(logical)
            nxt.append((d + (1 << p), (perm, done + 1), f'BF n{logical}@bit{p}'))
        for i, j in itertools.combinations(range(NB), 2):
            q = list(perm)
            q[i], q[j] = q[j], q[i]
            nxt.append((d + (1 << j) - (1 << i), (tuple(q), done), f'swap({i},{j})'))
        for nd, ns, op in nxt:
            if nd < dist.get(ns, 1 << 30):
                dist[ns] = nd
                prev[ns] = ((perm, done), op)
                heapq.heappush(pq, (nd, ns))


if __name__ == '__main__':
    cost, path = search()
    print('minimum words =', cost)
    print(path)
