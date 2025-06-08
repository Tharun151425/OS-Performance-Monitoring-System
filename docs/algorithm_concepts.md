# Design and Analysis of Algorithms - Comprehensive Guide

## Unit I: Basic Algorithmic Strategies

### 1. Brute Force
Brute force is the simplest and most straightforward problem-solving technique. It involves systematically checking all possible candidates for the solution.

#### Selection Sort
- **Concept**: Repeatedly finds the minimum element from the unsorted portion and puts it at the beginning
- **Time Complexity**: O(n²)
- **Space Complexity**: O(1)
- **Implementation**:
```python
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i+1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
```

#### Bubble Sort
- **Concept**: Repeatedly steps through the list, compares adjacent elements and swaps them if they are in wrong order
- **Time Complexity**: O(n²)
- **Space Complexity**: O(1)
- **Implementation**:
```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
```

## Unit II: Advanced Algorithmic Strategies

### 1. Divide and Conquer
Breaks down a problem into smaller subproblems, solves them, and then combines the solutions.

#### Merge Sort
- **Concept**: Divides array into two halves, recursively sorts them, and merges sorted halves
- **Time Complexity**: O(n log n)
- **Space Complexity**: O(n)
- **Implementation**:
```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
        
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

#### Quick Sort
- **Concept**: Selects a 'pivot' element and partitions array around it
- **Time Complexity**: Average O(n log n), Worst O(n²)
- **Space Complexity**: O(log n)
- **Implementation**:
```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)
```

#### Strassen's Matrix Multiplication
- **Concept**: Reduces number of multiplications in matrix multiplication from 8 to 7
- **Time Complexity**: O(n^2.807)
- **Implementation**:
```python
def strassen_multiply(A, B):
    n = len(A)
    if n == 1:
        return [[A[0][0] * B[0][0]]]
    
    # Split matrices into quadrants
    mid = n // 2
    a11 = [row[:mid] for row in A[:mid]]
    a12 = [row[mid:] for row in A[:mid]]
    a21 = [row[:mid] for row in A[mid:]]
    a22 = [row[mid:] for row in A[mid:]]
    
    b11 = [row[:mid] for row in B[:mid]]
    b12 = [row[mid:] for row in B[:mid]]
    b21 = [row[:mid] for row in B[mid:]]
    b22 = [row[mid:] for row in B[mid:]]
    
    # Compute the 7 products
    p1 = strassen_multiply(add_matrices(a11, a22), add_matrices(b11, b22))
    p2 = strassen_multiply(add_matrices(a21, a22), b11)
    p3 = strassen_multiply(a11, subtract_matrices(b12, b22))
    p4 = strassen_multiply(a22, subtract_matrices(b21, b11))
    p5 = strassen_multiply(add_matrices(a11, a12), b22)
    p6 = strassen_multiply(subtract_matrices(a21, a11), add_matrices(b11, b12))
    p7 = strassen_multiply(subtract_matrices(a12, a22), add_matrices(b21, b22))
    
    # Compute the quadrants of the result
    c11 = add_matrices(subtract_matrices(add_matrices(p1, p4), p5), p7)
    c12 = add_matrices(p3, p5)
    c21 = add_matrices(p2, p4)
    c22 = add_matrices(subtract_matrices(add_matrices(p1, p3), p2), p6)
    
    # Combine the quadrants into a single matrix
    C = [[0] * n for _ in range(n)]
    for i in range(mid):
        for j in range(mid):
            C[i][j] = c11[i][j]
            C[i][j + mid] = c12[i][j]
            C[i + mid][j] = c21[i][j]
            C[i + mid][j + mid] = c22[i][j]
    
    return C
```

### 2. Decrease and Conquer

#### Insertion Sort
- **Concept**: Builds final sorted array one item at a time
- **Time Complexity**: O(n²)
- **Space Complexity**: O(1)
- **Implementation**:
```python
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i-1
        while j >= 0 and arr[j] > key:
            arr[j+1] = arr[j]
            j -= 1
        arr[j+1] = key
    return arr
```

#### Depth First Search (DFS)
- **Concept**: Explores as far as possible along each branch before backtracking
- **Time Complexity**: O(V + E)
- **Implementation**:
```python
def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    visited.add(start)
    
    for next in graph[start] - visited:
        dfs(graph, next, visited)
    return visited
```

#### Breadth First Search (BFS)
- **Concept**: Explores all vertices at present depth before moving to vertices at next depth level
- **Time Complexity**: O(V + E)
- **Implementation**:
```python
from collections import deque

def bfs(graph, start):
    visited = set([start])
    queue = deque([start])
    
    while queue:
        vertex = queue.popleft()
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited
```

#### Topological Sorting
- **Concept**: Linear ordering of vertices such that for every directed edge u→v, u comes before v
- **Time Complexity**: O(V + E)
- **Implementation**:
```python
def topological_sort(graph):
    visited = set()
    stack = []
    
    def dfs(vertex):
        visited.add(vertex)
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                dfs(neighbor)
        stack.append(vertex)
    
    for vertex in graph:
        if vertex not in visited:
            dfs(vertex)
    
    return stack[::-1]
```

## Unit III: Advanced Techniques

### 1. Transform and Conquer

#### Heapsort
- **Concept**: Builds a heap and repeatedly extracts the maximum element
- **Time Complexity**: O(n log n)
- **Implementation**:
```python
def heapify(arr, n, i):
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)

def heap_sort(arr):
    n = len(arr)
    
    # Build max heap
    for i in range(n//2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # Extract elements
    for i in range(n-1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    
    return arr
```

### 2. String Matching Algorithms

#### Horspool's Algorithm
- **Concept**: Simplified version of Boyer-Moore algorithm
- **Time Complexity**: O(mn) worst case, but usually much better in practice
- **Implementation**:
```python
def horspool(text, pattern):
    n = len(text)
    m = len(pattern)
    
    # Build bad match table
    bad_match = {}
    for i in range(m-1):
        bad_match[pattern[i]] = m - 1 - i
    
    # Search
    i = m - 1
    while i < n:
        k = 0
        while k < m and pattern[m-1-k] == text[i-k]:
            k += 1
        if k == m:
            return i - m + 1
        i += bad_match.get(text[i], m)
    return -1
```

## Unit IV: Optimization Techniques

### 1. Dynamic Programming

#### 0/1 Knapsack
- **Concept**: Maximizes value while keeping weight under limit
- **Time Complexity**: O(nW)
- **Implementation**:
```python
def knapsack(values, weights, capacity):
    n = len(values)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(values[i-1] + dp[i-1][w-weights[i-1]], dp[i-1][w])
            else:
                dp[i][w] = dp[i-1][w]
    
    return dp[n][capacity]
```

### 2. Greedy Algorithms

#### Dijkstra's Algorithm
- **Concept**: Finds shortest paths from source to all vertices
- **Time Complexity**: O(V²) with matrix, O((V+E)logV) with min-heap
- **Implementation**:
```python
def dijkstra(graph, start):
    distances = {vertex: float('infinity') for vertex in graph}
    distances[start] = 0
    unvisited = set(graph.keys())
    
    while unvisited:
        current = min(unvisited, key=lambda vertex: distances[vertex])
        if distances[current] == float('infinity'):
            break
            
        for neighbor, weight in graph[current].items():
            distance = distances[current] + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                
        unvisited.remove(current)
    
    return distances
```

#### Prim's Algorithm
- **Concept**: Finds minimum spanning tree
- **Time Complexity**: O(V²)
- **Implementation**:
```python
def prims(graph):
    n = len(graph)
    selected = [False] * n
    selected[0] = True
    edges = 0
    mst = []
    
    while edges < n - 1:
        minimum = float('infinity')
        x = y = 0
        
        for i in range(n):
            if selected[i]:
                for j in range(n):
                    if not selected[j] and graph[i][j]:
                        if minimum > graph[i][j]:
                            minimum = graph[i][j]
                            x, y = i, j
        
        mst.append((x, y, graph[x][y]))
        selected[y] = True
        edges += 1
    
    return mst
```

## Unit V: Advanced Problem-Solving Techniques

### 1. Backtracking

#### N-Queens Problem
- **Concept**: Places N queens on NxN chessboard so no two queens threaten each other
- **Time Complexity**: O(N!)
- **Implementation**:
```python
def is_safe(board, row, col, n):
    # Check row on left side
    for j in range(col):
        if board[row][j] == 1:
            return False
    
    # Check upper diagonal on left side
    for i, j in zip(range(row, -1, -1), range(col, -1, -1)):
        if board[i][j] == 1:
            return False
    
    # Check lower diagonal on left side
    for i, j in zip(range(row, n, 1), range(col, -1, -1)):
        if board[i][j] == 1:
            return False
    
    return True

def solve_nqueens(n):
    board = [[0 for x in range(n)] for y in range(n)]
    
    def solve_util(col):
        if col >= n:
            return True
        
        for i in range(n):
            if is_safe(board, i, col, n):
                board[i][col] = 1
                if solve_util(col + 1):
                    return True
                board[i][col] = 0
        
        return False
    
    if solve_util(0) == False:
        return None
    return board
```

### Additional Important Algorithms

#### Tarjan's Algorithm (for Strongly Connected Components)
- **Concept**: Finds strongly connected components in directed graph
- **Time Complexity**: O(V + E)
- **Implementation**:
```python
def tarjan_scc(graph):
    index_counter = [0]
    index = {}  # node -> index
    lowlink = {}  # node -> lowest index reachable
    stack = []
    on_stack = set()
    scc_list = []
    
    def strongconnect(node):
        index[node] = index_counter[0]
        lowlink[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack.add(node)
        
        # Consider successors of node
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
            scc_list.append(scc)
    
    for node in graph:
        if node not in index:
            strongconnect(node)
    
    return scc_list
```

### Key Concepts in Complexity Theory

#### P, NP, NP-Complete, and NP-Hard
- **P**: Problems solvable in polynomial time
- **NP**: Problems verifiable in polynomial time
- **NP-Complete**: Problems that are both in NP and as hard as any NP problem
- **NP-Hard**: Problems at least as hard as NP problems (might not be in NP)

Common NP-Complete Problems:
1. Traveling Salesman Problem
2. Boolean Satisfiability (SAT)
3. Subset Sum
4. Graph Coloring
5. Hamiltonian Cycle 