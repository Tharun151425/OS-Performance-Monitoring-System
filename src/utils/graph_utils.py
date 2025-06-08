import networkx as nx
from typing import Dict, List, Set, Tuple

def tarjan(graph: Dict[int, List[int]]) -> List[List[int]]:
    """
    Implements Tarjan's algorithm to find strongly connected components.
    
    Args:
        graph: Dictionary representing adjacency list where keys are PIDs
        
    Returns:
        List of lists, where each inner list contains PIDs in an SCC
    """
    index_counter = [0]
    index = {}  # node -> index
    lowlink = {}  # node -> lowlink value
    stack = []
    on_stack = set()  # nodes currently on stack
    sccs = []
    
    def strongconnect(node: int):
        index[node] = index_counter[0]
        lowlink[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack.add(node)
        
        # Consider successors of node
        if node in graph:
            for successor in graph[node]:
                if successor not in index:
                    # Successor has not yet been visited
                    strongconnect(successor)
                    lowlink[node] = min(lowlink[node], lowlink[successor])
                elif successor in on_stack:
                    # Successor is in stack and hence in the current SCC
                    lowlink[node] = min(lowlink[node], index[successor])
        
        # If node is a root node, pop the stack and generate an SCC
        if lowlink[node] == index[node]:
            scc = []
            while True:
                successor = stack.pop()
                on_stack.remove(successor)
                scc.append(successor)
                if successor == node:
                    break
            sccs.append(scc)
    
    for node in graph:
        if node not in index:
            strongconnect(node)
            
    return sccs

def dfs_tree(graph: Dict[int, List[int]], start_node: int) -> Tuple[Dict[int, List[int]], Dict[int, int]]:
    """
    Performs DFS to generate a tree view starting from a given node.
    
    Args:
        graph: Dictionary representing adjacency list
        start_node: Starting node for DFS
        
    Returns:
        Tuple of (tree as adjacency list, node depths)
    """
    tree = {}
    depths = {}
    visited = set()
    
    def dfs(node: int, depth: int = 0):
        visited.add(node)
        depths[node] = depth
        tree[node] = []
        
        if node in graph:
            for neighbor in graph[node]:
                if neighbor not in visited:
                    tree[node].append(neighbor)
                    dfs(neighbor, depth + 1)
    
    dfs(start_node)
    return tree, depths

def calculate_bfs_distances(graph: Dict[int, List[int]], root: int) -> Dict[int, int]:
    """
    Calculates BFS distances from root node to all other nodes.
    
    Args:
        graph: Dictionary representing adjacency list
        root: Root node to start BFS from
        
    Returns:
        Dictionary mapping nodes to their distances from root
    """
    distances = {root: 0}
    queue = [(root, 0)]
    visited = {root}
    
    while queue:
        node, dist = queue.pop(0)
        if node in graph:
            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[neighbor] = dist + 1
                    queue.append((neighbor, dist + 1))
    
    return distances 