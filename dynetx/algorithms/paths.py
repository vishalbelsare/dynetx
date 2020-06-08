import networkx as nx
import itertools

__author__ = 'Giulio Rossetti'
__license__ = "BSD-Clause-2"
__email__ = "giulio.rossetti@gmail.com"

__all__ = ['time_respecting_paths', 'all_time_respecting_paths', 'annotate_paths', 'path_duration', 'path_length']


def __temporal_dag(G, u, v, start=None, end=None):
    """
        Creates a rooted temporal DAG assuming interaction chains of length 1 within each network snapshot.

        Parameters
        ----------
        G : a DynGraph or DynDiGraph object
        u : a node id
        v : a node id
        start : temporal id to start searching
        end : temporal id to conclude the search

        Returns
        --------
        DAG: a directed graph
        sources: source node ids
        targets: target node ids

        Examples
        --------

    """
    ids = G.temporal_snapshots_ids()
    tid_type = type(ids[0])
    node_type = type(u)

    # correcting missing values
    if end is None:
        end = ids[-1]

    if start is None:
        start = ids[0]

    if start < min(ids) or start > end or end > max(ids) or start > max(ids):
        raise ValueError(f"The specified interval {[start, end]} is not a proper subset of the network timestamps "
                         f"{[min(ids), max(ids)]}.")

    # adjusting temporal window
    start = list(map(lambda i: i >= start, ids)).index(True)
    end = end if end == ids[-1] else list(map(lambda i: i > end, ids)).index(True)
    ids = ids[start:end]

    # creating empty DAG
    DG = nx.DiGraph()
    DG.add_node(u)
    active = {u: None}
    sources, targets = {}, {}

    for tid in ids:
        to_remove = []
        to_add = []
        for an in active:
            neighbors = {f"{n}_{tid}": None for n in G.neighbors(node_type(str(an).split("_")[0]), tid)}
            if f"{v}_{tid}" in neighbors:
                targets[f"{v}_{tid}"] = None

            if len(neighbors) == 0 and an != u:
                to_remove.append(an)

            for n in neighbors:
                if isinstance(an, node_type):
                    if not isinstance(an, str) or (isinstance(an, str) and '_' not in an):
                        an = f"{an}_{tid}"
                        sources[an] = None

                DG.add_edge(an, n)
                to_add.append(n)

        for n in to_add:
            active[n] = None

        for rm in to_remove:
            del active[rm]

    return DG, list(sources), list(targets), node_type, tid_type


def time_respecting_paths(G, u, v, start=None, end=None):
    """
        Computes all the simple time respecting paths among u and v within [start, stop].
        It assumes interaction chains of length 1 within each network snapshot.

        Parameters
        ----------
        G : a DynGraph or DynDiGraph object
        u : a node id
        v : a node id
        start : temporal id to start searching
        end : temporal id to conclude the search

        Returns
        --------
        paths: a list of paths, each one expressed as a list of timestamped interactions

        Examples
        --------

    """
    DAG, sources, targets, n_type, t_type = __temporal_dag(G, u, v, start, end)

    pairs = [(x, y) for x in sources for y in targets]

    paths = []
    for pair in pairs:
        path = list(nx.all_simple_paths(DAG, pair[0], pair[1]))

        for p in path:
            pt = []
            for first, second in zip(p, p[1:]):
                u, _ = first.split("_")
                v, t = second.split("_")
                pt.append((n_type(u), n_type(v), t_type(t)))
            paths.append(pt)
    return paths


def all_time_respecting_paths(G, start=None, end=None):
    """
        Computes all the simple paths among network node pairs.
        It assumes interaction chains of length 1 within each network snapshot.

        Parameters
        ----------
        G : a DynGraph or DynDiGraph object
        start : temporal id to start searching
        end : temporal id to conclude the search

        Returns
        --------
        paths: a dictionary <(u,v), paths>

        Examples
        --------

    """
    res = {}
    for u, v in itertools.permutations(list(G.nodes()), 2):
        paths = list(time_respecting_paths(G, u, v, start, end))
        if len(paths) > 0:
            res[(u, v)] = paths
    return res

def annotate_paths(paths):
    """
        Annotate a set of paths identifying peculiar types of paths.

        shortest: topological shortest paths
        fastest: paths that have minimal duration
        foremost: first paths that reach the destination
        shortest fastest: minimum length path among minimum duration ones
        fastest shortest: minimum duration path among minimum length ones

        Parameters
        ----------
        paths : a list of paths

        Returns
        --------
        annotated: a dictionary identifying shortest, fastest, foremost, fastest_shortest and shortest_fastest paths.

        Examples
        --------

    """
    annotated = {"shortest": None, "fastest": None, "shortest_fastest": None,
                 "fastest_shortest": None, "foremost": None}

    min_to_reach = None
    shortest = None
    fastest = None

    for path in paths:
        length = path_length(path)
        duration = path_duration(path)
        reach = path[-1][-1]

        if shortest is None or length < shortest:
            shortest = length
            annotated['shortest'] = [path]
        elif length == shortest:
            annotated['shortest'].append(path)

        if fastest is None or duration < fastest:
            fastest = duration
            annotated['fastest'] = [path]
        elif duration == fastest:
            annotated['fastest'].append(path)

        if min_to_reach is None or reach < min_to_reach:
            min_to_reach = reach
            annotated['foremost'] = [path]
        elif reach == min_to_reach:
            annotated['foremost'].append(path)

    fastest_shortest = {tuple(path): path_duration(path) for path in annotated['shortest']}
    minval = min(fastest_shortest.values())
    fastest_shortest = list(filter(lambda x: fastest_shortest[x] == minval, fastest_shortest))

    shortest_fastest = {tuple(path): path_length(path) for path in annotated['fastest']}
    minval = min(shortest_fastest.values())
    shortest_fastest = list(filter(lambda x: shortest_fastest[x] == minval, shortest_fastest))

    annotated['fastest_shortest'] = [list(p) for p in fastest_shortest]
    annotated['shortest_fastest'] = [list(p) for p in shortest_fastest]

    return annotated


def path_length(path):
    """
        Parameters
        ----------
        path : a path

        Returns
        --------
        length: the number of interactions composing the path

        Examples
        --------

    """
    return len(path)


def path_duration(path):
    """
        Parameters
        ----------
        path : a path

        Returns
        --------
        duration: the duration of the path

        Examples
        --------

    """
    return path[-1][-1] - path[0][-1]
