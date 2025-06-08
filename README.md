# Memory Leak Detector & Performance Optimizer

A Python application that demonstrates various Design and Analysis of Algorithms (DAA) concepts through system performance monitoring and optimization.

## Algorithm Implementations

### 1. Divide and Conquer
- Process graph construction using recursive divide and conquer approach
- Memory usage calculation through hierarchical decomposition

### 2. Graph Algorithms
- Depth-First Search (DFS) for memory leak detection
- Cycle detection in process dependency graphs
- Strongly Connected Components analysis

### 3. Dijkstra's Algorithm
- Finding critical paths in process dependencies
- Performance bottleneck identification

### 4. Dynamic Programming
- Memoization for memory usage calculations
- Caching of process relationships
- Optimization of repeated computations

### 5. Greedy Techniques
- Process optimization suggestions
- Resource allocation optimization
- Performance improvement recommendations

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

## Features

1. Memory Leak Detection
   - Cycle detection in process graphs
   - Memory impact analysis
   - Critical cycle identification

2. Performance Optimization
   - Critical path analysis
   - Resource usage tracking
   - Optimization suggestions

3. Real-time Monitoring
   - Dynamic graph updates
   - Performance metrics visualization
   - Resource usage trends

## Project Structure

```
.
├── algorithms/
│   ├── memory_graph.py      # Memory leak detection algorithms
│   └── performance_optimizer.py  # Performance optimization algorithms
├── ui/
│   ├── theme_manager.py     # UI theme management
│   └── custom_widgets.py    # Custom UI components
└── app.py                   # Main application
```

## Algorithm Complexity Analysis

1. Memory Leak Detection
   - Time Complexity: O(V + E) for DFS
   - Space Complexity: O(V) for visited set

2. Performance Optimization
   - Time Complexity: O((V + E) log V) for Dijkstra's
   - Space Complexity: O(V) for priority queue

Where V is the number of processes and E is the number of connections between them.
