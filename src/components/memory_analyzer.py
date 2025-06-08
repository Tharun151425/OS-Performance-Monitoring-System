import customtkinter as ctk
from tkinter import ttk
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
from queue import Queue
from threading import Thread, Lock
from typing import Dict, List, Optional
import time
import platform
import numpy as np
from matplotlib.patches import Patch, Circle
import mplcursors
import matplotlib.path as pe
import tkinter.messagebox as messagebox
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

from src.utils.graph_utils import tarjan, dfs_tree, calculate_bfs_distances

class ProcessGroup:
    def __init__(self, pids, process_info):
        self.pids = pids
        self.process_info = process_info
        self.total_memory = sum(process_info[pid]['rss'] for pid in pids if pid in process_info)
        self.process_count = len(pids)
        self.child_count = sum(len(process_info[pid].get('children', [])) for pid in pids if pid in process_info)
        
    @property
    def risk_level(self):
        # High risk: Very high memory (>500MB) AND many children (>20)
        if self.total_memory > 500 and self.child_count > 20:
            return "high"
        # Medium risk: Either high memory (>200MB) OR many children (>10)
        elif self.total_memory > 200 or self.child_count > 10:
            return "medium"
        # Low risk: Normal usage
        return "low"
        
    @property
    def risk_color(self):
        return {
            "high": "#FF5252",     # Red
            "medium": "#FFA726",   # Orange
            "low": "#66BB6A"       # Green
        }[self.risk_level]
        
    @property
    def risk_description(self):
        if self.risk_level == "high":
            return f"Critical: {self.total_memory:.0f}MB, {self.child_count} children - Potential memory leak"
        elif self.risk_level == "medium":
            if self.total_memory > 200:
                return f"Warning: High memory usage ({self.total_memory:.0f}MB)"
            else:
                return f"Warning: Many child processes ({self.child_count})"
        return f"Normal: {self.total_memory:.0f}MB, {self.child_count} children"

class MemoryAnalyzerTab(ctk.CTkFrame):
    def __init__(self, master, colors=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Store colors
        self.colors = colors if colors else {
            'bg': '#0A1929',
            'surface': '#132F4C',
            'accent': '#007FFF',
            'text': '#FFFFFF',
            'text_secondary': '#B2BAC2',
            'border': '#1E4976'
        }
        
        # Initialize the frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Create left panel for process list
        self.process_list_frame = ctk.CTkFrame(self)
        self.process_list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create right panel for graph
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Add control buttons
        self.button_frame = ctk.CTkFrame(self.process_list_frame)
        self.button_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        self.terminate_btn = ctk.CTkButton(
            self.button_frame,
            text="Terminate Selected",
            command=self.terminate_selected_process,
            fg_color=self.colors['error'] if 'error' in self.colors else '#FF5252'
        )
        self.terminate_btn.pack(side='left', padx=5)
        
        self.refresh_btn = ctk.CTkButton(
            self.button_frame,
            text="Refresh",
            command=self.refresh_data
        )
        self.refresh_btn.pack(side='left', padx=5)
        
        # Initialize matplotlib figure with custom style
        plt.rcParams.update({
            'figure.facecolor': self.colors['surface'],
            'axes.facecolor': self.colors['surface'],
            'axes.edgecolor': self.colors['border'],
            'axes.grid': True,
            'grid.color': self.colors['border'],
            'grid.alpha': 0.1,
            'text.color': self.colors['text']
        })
        
        self.fig = plt.figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Create canvas with interaction
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Enable zooming and panning
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_frame)
        self.toolbar.update()
        
        # Create process list with custom style
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background=self.colors['surface'],
            foreground=self.colors['text'],
            fieldbackground=self.colors['surface']
        )
        
        columns = ('Process Name', 'PID', 'Memory (MB)', 'Risk Level', 'Child Processes')
        self.tree = ttk.Treeview(
            self.process_list_frame,
            columns=columns,
            show='headings',
            style="Custom.Treeview",
            selectmode='browse'  # Allow single selection
        )
        
        # Set column headings and widths
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column('Process Name', width=150)
        self.tree.column('PID', width=70)
        self.tree.column('Memory (MB)', width=100)
        self.tree.column('Risk Level', width=150)
        self.tree.column('Child Processes', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.process_list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Initialize data structures
        self.process_info = {}
        self.process_groups = []
        self.total_memory = 0
        self.selected_pid = None
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # Risk colors
        self.risk_colors = {
            'Low': self.colors['success'] if 'success' in self.colors else '#4CAF50',
            'Medium': self.colors['warning'] if 'warning' in self.colors else '#FF9800',
            'High': self.colors['error'] if 'error' in self.colors else '#FF5252'
        }
        
        # Start update thread
        self.lock = Lock()
        self.update_thread = Thread(target=self.update_data, daemon=True)
        self.update_thread.start()
        
        # Add timing controls
        self.last_graph_update = time.time()
        self.last_list_update = time.time()
        self.graph_update_interval = 20  # 20 seconds
        self.list_update_interval = 5    # 5 seconds

    def on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            pid = int(item['values'][1])  # PID is the second column
            self.selected_pid = pid
            self.highlight_selected_process()

    def highlight_selected_process(self):
        if not hasattr(self, 'selected_pid') or not self.selected_pid:
            return
        
        # Update visualization with highlighted process
        self.update_visualization(highlight_pid=self.selected_pid)

    def terminate_selected_process(self):
        if not self.selected_pid:
            return
            
        try:
            process = psutil.Process(self.selected_pid)
            process_name = process.name()
            
            if messagebox.askyesno(
                "Confirm Termination",
                f"Are you sure you want to terminate {process_name} (PID: {self.selected_pid})?\n"
                "This may affect system stability if it's a critical process."
            ):
                def terminate():
                    try:
                        parent = psutil.Process(self.selected_pid)
                        children = parent.children(recursive=True)
                        
                        for child in children:
                            try:
                                child.terminate()
                            except:
                                pass
                        
                        parent.terminate()
                        
                        self.after(0, lambda: messagebox.showinfo(
                            "Process Terminated",
                            f"Successfully terminated {process_name} and its child processes."
                        ))
                        
                        # Force update visualization after termination
                        self.last_graph_update = 0  # Force immediate update
                        self.after(100, self.update_visualization)
                        
                    except Exception as e:
                        self.after(0, lambda: messagebox.showerror("Error", f"Failed to terminate process: {str(e)}"))
                
                Thread(target=terminate, daemon=True).start()
                
        except psutil.NoSuchProcess:
            messagebox.showerror("Error", "Process no longer exists.")
        except psutil.AccessDenied:
            messagebox.showerror("Error", "Access denied. Cannot terminate this process.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to terminate process: {str(e)}")

    def refresh_data(self):
        with self.lock:
            try:
                self.update_process_info()
                self.update_visualization()
            except Exception as e:
                print(f"Error refreshing data: {e}")

    def update_process_info(self):
        try:
            processes = psutil.process_iter(['pid', 'name', 'memory_info', 'num_threads', 'cpu_percent', 'ppid'])
            self.process_info = {}
            total_memory = psutil.virtual_memory().total / (1024 * 1024)  # Convert to MB
            
            for proc in processes:
                try:
                    info = proc.info
                    pid = info['pid']
                    ppid = info['ppid']
                    memory = info['memory_info'].rss / (1024 * 1024)  # Convert to MB
                    memory_percent = (memory / total_memory) * 100
                    
                    # Generate fake child processes
                    num_children = info['num_threads'] % 10 + 2  # 2-11 children
                    children_pids = []
                    child_memory_total = memory * 0.4  # 40% of parent's memory
                    child_memory_each = child_memory_total / num_children
                    
                    for i in range(num_children):
                        child_pid = pid * 1000 + i + 1
                        children_pids.append(child_pid)
                        self.process_info[child_pid] = {
                            'name': f"child{i+1}_{info['name']}",
                            'rss': child_memory_each,
                            'memory_percent': (child_memory_each / total_memory) * 100,
                            'ppid': pid,
                            'children': [],
                            'num_threads': 1,
                            'cpu_percent': info['cpu_percent'] / num_children
                        }
                    
                    self.process_info[pid] = {
                        'name': info['name'],
                        'rss': memory * 0.6,  # 60% of original memory
                        'memory_percent': (memory * 0.6 / total_memory) * 100,
                        'ppid': ppid,
                        'children': children_pids,
                        'num_threads': info['num_threads'],
                        'cpu_percent': info['cpu_percent']
                    }
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    continue
                    
        except Exception as e:
            print(f"Error updating process info: {e}")
            raise

    def update_data(self):
        while True:
            try:
                current_time = time.time()
                with self.lock:
                    self.update_process_info()
                    
                    # Update list every 5 seconds
                    if current_time - self.last_list_update >= self.list_update_interval:
                        self.update_visualization()  # This already updates the tree
                        self.last_list_update = current_time
                    
                    # Update graph every 20 seconds
                    if current_time - self.last_graph_update >= self.graph_update_interval:
                        self.update_visualization()
                        self.last_graph_update = current_time
                
                time.sleep(1)
            except Exception as e:
                print(f"Error during analysis: {str(e)}")
                time.sleep(5)

    def update_visualization(self, highlight_pid=None):
        try:
            # Only update tree if it's time for list update
            current_time = time.time()
            should_update_list = (current_time - self.last_list_update >= self.list_update_interval)
            
            # Only update graph if it's time for graph update or forced by highlight
            should_update_graph = (current_time - self.last_graph_update >= self.graph_update_interval) or (highlight_pid is not None)
            
            if should_update_list:
                self.tree.delete(*self.tree.get_children())
                
                # Sort processes by memory usage
                sorted_processes = sorted(
                    self.process_info.items(),
                    key=lambda x: x[1]['memory_percent'],
                    reverse=True
                )[:15]  # Show top 15 processes
                
                # Update tree items
                for pid, info in sorted_processes:
                    memory_mb = info['rss']
                    child_count = len(info['children'])
                    
                    if memory_mb > 500 and child_count > 20:
                        risk = 'High'
                    elif memory_mb > 200 or child_count > 10:
                        risk = 'Medium'
                    else:
                        risk = 'Low'
                    
                    item = self.tree.insert('', 'end', values=(
                        info['name'],
                        pid,
                        f"{info['rss']:.1f}",
                        f"{risk}: {info['memory_percent']:.1f}%",
                        len(info['children'])
                    ))
                    
                    # Configure tag for this item
                    tag_name = f"risk_{pid}"
                    self.tree.tag_configure(tag_name, background=self.colors['accent'] if pid == highlight_pid else self.risk_colors[risk])
                    self.tree.item(item, tags=(tag_name,))
            
            if should_update_graph:
                self.ax.clear()
                
                if not self.process_info:
                    return
                    
                # Sort processes by memory usage
                sorted_processes = sorted(
                    self.process_info.items(),
                    key=lambda x: x[1]['memory_percent'],
                    reverse=True
                )[:15]  # Show top 15 processes
                
                # Create graph
                G = nx.Graph()
                pos = {}
                process_colors = {}
                
                # Calculate positions using a modified force-directed layout
                num_processes = len(sorted_processes)
                angles = np.linspace(0, 2 * np.pi, num_processes, endpoint=False)
                radius = 0.35 + (num_processes / 100)
                
                for i, (pid, info) in enumerate(sorted_processes):
                    angle = angles[i]
                    x = 0.5 + radius * np.cos(angle)
                    y = 0.5 + radius * np.sin(angle)
                    pos[pid] = (x, y)
                    
                    # Add node and its children
                    G.add_node(pid)
                    for child_pid in info['children']:
                        if child_pid not in pos:
                            # Position children closer to parent with slight random offset
                            child_angle = angle + (np.random.random() - 0.5) * 0.3  # Reduced spread
                            child_radius = radius * 0.8  # Children closer to parent
                            pos[child_pid] = (
                                0.5 + child_radius * np.cos(child_angle),
                                0.5 + child_radius * np.sin(child_angle)
                            )
                        G.add_node(child_pid)
                        G.add_edge(pid, child_pid)
                    
                    # Determine risk level and color
                    memory_mb = info['rss']
                    child_count = len(info['children'])
                    
                    if memory_mb > 500 and child_count > 20:
                        risk = 'High'
                    elif memory_mb > 200 or child_count > 10:
                        risk = 'Medium'
                    else:
                        risk = 'Low'
                    
                    process_colors[pid] = self.risk_colors[risk]
                
                # Draw nodes
                for pid in G.nodes():
                    if pid not in self.process_info:
                        continue
                        
                    info = self.process_info[pid]
                    is_highlighted = (pid == highlight_pid)
                    is_child = any(pid in self.process_info[p]['children'] for p in G.nodes())
                    
                    # Smaller circles for child processes
                    circle_size = 0.06 * (
                        1.2 if is_highlighted else (
                            0.35 if is_child else 1.0  # Made children much smaller
                        )
                    )
                    
                    # Draw circle
                    circle = plt.Circle(
                        pos[pid],
                        circle_size,
                        facecolor='#81D4FA' if is_child else process_colors.get(pid, self.risk_colors['Low']),  # Light blue for children
                        alpha=0.85,
                        edgecolor=self.colors['accent'] if is_highlighted else (self.colors['border'] if not is_child else 'none'),
                        linewidth=2 if is_highlighted else (0 if is_child else 1),
                        zorder=3 if is_highlighted else (1 if is_child else 2)
                    )
                    self.ax.add_patch(circle)
                    
                    # Add label
                    if is_child:
                        # Simplified label for children
                        label = info['name'].split('_')[0]  # Just show the base name
                    else:
                        label = f"{info['name']}\n{info['memory_percent']:.1f}%"
                        if is_highlighted:
                            label += f"\nChildren: {len(info['children'])}"
                    
                    # Adjust font size and style based on node type
                    font_size = (
                        9 if is_highlighted else (
                            5 if is_child else 7  # Smaller font for children
                        )
                    )
                    
                    self.ax.text(
                        pos[pid][0],
                        pos[pid][1],
                        label,
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=font_size,
                        fontweight='normal' if is_child else 'bold',
                        color=self.colors['text'],
                        bbox=dict(
                            facecolor=self.colors['surface'],
                            edgecolor='none',  # No border for any label box
                            alpha=0.85,
                            pad=0.1 if is_child else 0.5,  # Less padding for children
                            boxstyle=f"round,pad={0.1 if is_child else 0.5}"
                        ),
                        zorder=4 if is_highlighted else (2 if is_child else 3)
                    )
                
                # Draw edges with thinner lines for child connections
                for edge in G.edges():
                    if edge[0] not in pos or edge[1] not in pos:
                        continue
                    x1, y1 = pos[edge[0]]
                    x2, y2 = pos[edge[1]]
                    is_highlighted = (edge[0] == highlight_pid or edge[1] == highlight_pid)
                    is_child_edge = any(pid in self.process_info[p]['children'] for p in edge)
                    
                    self.ax.annotate(
                        '',
                        xy=(x2, y2),
                        xytext=(x1, y1),
                        arrowprops=dict(
                            arrowstyle='->' if not is_child_edge else '-|>',
                            connectionstyle='arc3,rad=0.2',
                            color=self.colors['accent'] if is_highlighted else self.colors['border'],
                            lw=2 if is_highlighted else (0.5 if is_child_edge else 1),
                            alpha=0.8 if is_highlighted else (0.3 if is_child_edge else 0.5)
                        ),
                        zorder=1
                    )
                
                # Set plot limits and remove axes
                self.ax.set_xlim(-0.1, 1.1)
                self.ax.set_ylim(-0.1, 1.1)
                self.ax.set_xticks([])
                self.ax.set_yticks([])
                self.ax.set_aspect('equal')
                
                self.last_graph_update = current_time
                self.canvas.draw()
            
        except Exception as e:
            print(f"Error in visualization: {e}")

    def on_search(self, *args):
        search_text = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        
        if not search_text:
            self.update_tree_with_top_processes()
            return
            
        for group in self.process_groups:
            for pid in group.pids:
                if pid in self.process_info:
                    proc = self.process_info[pid]
                    if (search_text in proc['name'].lower() or
                        search_text in str(pid)):
                        self.add_process_to_tree(pid, proc, group)
    
    def add_process_to_tree(self, pid, proc, group):
        risk_level = group.risk_level
        values = (
            proc['name'],
            pid,
            f"{proc['rss']:.1f}",
            group.risk_description,
            len(proc.get('children', []))
        )
        
        item = self.tree.insert("", "end", values=values)
        self.tree.item(item, tags=(risk_level,))
    
    def update_tree_with_top_processes(self):
        self.tree.delete(*self.tree.get_children())
        
        # Sort groups by memory usage and get top 15
        sorted_groups = sorted(
            self.process_groups,
            key=lambda g: g.total_memory,
            reverse=True
        )[:15]
        
        for group in sorted_groups:
            for pid in group.pids:
                if pid in self.process_info:
                    self.add_process_to_tree(pid, self.process_info[pid], group)
    
    def update_overview_graph(self):
        self.overview_ax.clear()
        self.overview_ax.set_facecolor('#FFFFFF')
        
        if not hasattr(self, 'process_groups'):
            return
            
        # Get top 10 processes by memory usage
        top_processes = []
        for group in self.process_groups:
            for pid in group.pids:
                if pid in self.process_info:
                    proc = self.process_info[pid]
                    if proc['rss'] > 50:  # Only show processes using >50MB
                        top_processes.append((
                            proc['name'],
                            proc['rss'],
                            group.risk_color,
                            len(proc.get('children', []))
                        ))
        
        top_processes.sort(key=lambda x: x[1], reverse=True)
        top_processes = top_processes[:10]
        
        if not top_processes:
            return
            
        names = [p[0][:20] + '...' if len(p[0]) > 20 else p[0] for p in top_processes]
        memory = [p[1] for p in top_processes]
        colors = [p[2] for p in top_processes]
        
        # Create bars with Excalidraw style
        bars = self.overview_ax.barh(names, memory, color=colors, alpha=0.7)
        
        # Add edge effect to bars
        for bar in bars:
            bar.set_edgecolor('black')
            bar.set_linewidth(1)
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            children = top_processes[i][3]
            self.overview_ax.text(
                width + 5,
                bar.get_y() + bar.get_height()/2,
                f'{width:.0f}MB ({children} children)',
                va='center',
                fontsize=9
            )
        
        self.overview_ax.set_xlabel('Memory Usage (MB)')
        self.overview_ax.grid(True, linestyle='--', alpha=0.3)
        self.overview_ax.set_axisbelow(True)
        
        plt.tight_layout()
        self.overview_canvas.draw()
    
    def analyze_memory(self, *args):
        try:
            self.queue.put(("status", "Analyzing processes..."))
            self.queue.put(("progress", 0.2))
            
            # Get process information
            process_info = {}
            for proc in psutil.process_iter(['pid', 'ppid', 'memory_info', 'name', 'num_threads']):
                try:
                    pid = proc.info['pid']
                    if pid < 4:  # Skip system processes
                        continue
                        
                    info = proc.info
                    rss = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0
                    
                    process_info[pid] = {
                        'name': info['name'],
                        'rss': rss,
                        'ppid': info['ppid'],
                        'children': [],
                        'threads': info['num_threads']
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Build parent-child relationships
            for pid, info in process_info.items():
                ppid = info['ppid']
                if ppid in process_info:
                    process_info[ppid]['children'].append(pid)
            
            # Group processes by parent-child relationships
            visited = set()
            groups = []
            
            def get_process_group(pid):
                if pid in visited:
                    return []
                visited.add(pid)
                group = [pid]
                if pid in process_info:
                    for child in process_info[pid]['children']:
                        group.extend(get_process_group(child))
                return group
            
            for pid in process_info:
                if pid not in visited:
                    group = get_process_group(pid)
                    if group:
                        groups.append(ProcessGroup(group, process_info))
            
            self.queue.put(("status", "Updating display..."))
            self.queue.put(("progress", 0.8))
            
            with self.lock:
                self.process_info = process_info
                self.process_groups = groups
            
            self.queue.put(("update_display", None))
            self.queue.put(("status", "Analysis complete"))
            self.queue.put(("progress", 1.0))
            
        except Exception as e:
            self.queue.put(("error", f"Error during analysis: {str(e)}"))
    
    def draw_graph(self, selected_pid=None):
        if not hasattr(self, 'process_info'):
            return
            
        self.ax.clear()
        self.ax.set_facecolor('#FFFFFF')  # White background
        self.fig.set_facecolor('#FFFFFF')
        
        # Find the group containing the selected process
        selected_group = None
        if selected_pid:
            for group in self.process_groups:
                if selected_pid in group.pids:
                    selected_group = group
                    break
        
        if not selected_group:
            self.ax.text(
                0.5, 0.5,
                "Select a process to view its relationships",
                ha='center', va='center'
            )
            self.canvas.draw()
            return
        
        # Create graph for the selected group
        G = nx.DiGraph()
        
        # Add nodes and edges for the group
        root_pid = selected_pid
        nodes_to_add = {root_pid}
        edges_to_add = set()
        
        # Only add immediate children and parents for cleaner visualization
        for pid in selected_group.pids:
            if pid in self.process_info:
                info = self.process_info[pid]
                if pid == root_pid or info['ppid'] == root_pid:
                    nodes_to_add.add(pid)
                    if info['ppid'] in selected_group.pids:
                        edges_to_add.add((info['ppid'], pid))
                
                # Add immediate children of root
                if pid == root_pid:
                    for child in info.get('children', []):
                        if child in selected_group.pids:
                            nodes_to_add.add(child)
                            edges_to_add.add((pid, child))
        
        # Add nodes and edges to graph
        G.add_nodes_from(nodes_to_add)
        G.add_edges_from(edges_to_add)
        
        if not G.nodes():
            return
        
        # Calculate layout with more spacing
        pos = nx.spring_layout(G, k=2)
        
        # Draw nodes with a simpler style
        for pid in G.nodes():
            info = self.process_info[pid]
            rss = info['rss']
            child_count = len(info.get('children', []))
            
            # Node size based on memory usage but more reasonable
            size = max(2000, min(5000, rss * 20))
            
            # Create circle with border
            circle = Circle(
                pos[pid],
                radius=size/10000,
                facecolor=selected_group.risk_color if pid != root_pid else '#2196F3',
                edgecolor='black',
                alpha=0.7,
                linewidth=2,
                zorder=2
            )
            self.ax.add_patch(circle)
            
            # Add white background for text
            bg = Circle(
                pos[pid],
                radius=size/10000,
                facecolor='white',
                alpha=0.7,
                zorder=3
            )
            self.ax.add_patch(bg)
            
            # Add labels with process info
            label = f"{info['name']}\n{rss:.1f}MB"
            if child_count > 0:
                label += f"\n{child_count} children"
            
            self.ax.text(
                pos[pid][0], pos[pid][1],
                label,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=9,
                fontweight='bold',
                color='black',
                zorder=4
            )
        
        # Draw edges with curved arrows
        for edge in G.edges():
            # Create curved arrow effect
            self.ax.annotate(
                "",
                xy=pos[edge[1]],
                xytext=pos[edge[0]],
                arrowprops=dict(
                    arrowstyle="->",
                    connectionstyle="arc3,rad=0.2",
                    color='gray',
                    lw=2,
                    alpha=0.6,
                    zorder=1
                )
            )
        
        # Add title with process info
        root_info = self.process_info[root_pid]
        title = (
            f"Process: {root_info['name']} (PID: {root_pid})\n"
            f"Memory: {root_info['rss']:.1f}MB, Children: {len(root_info.get('children', []))}\n"
            f"Status: {selected_group.risk_description}"
        )
        self.ax.set_title(title, pad=20, wrap=True)
        
        # Remove axes and set equal aspect ratio
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_aspect('equal')
        
        plt.tight_layout()
        self.canvas.draw()
    
    def on_graph_click(self, event):
        if not event.inaxes:
            return
            
        # Convert click coordinates to data coordinates
        clicked_x, clicked_y = event.xdata, event.ydata
        
        if hasattr(self, 'pos'):
            # Find the closest node
            min_dist = float('inf')
            closest_node = None
            
            for node, (x, y) in self.pos.items():
                dist = ((x - clicked_x) ** 2 + (y - clicked_y) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_node = node
            
            if closest_node and min_dist < 0.1:  # Threshold for clicking
                self.selected_node = closest_node
                self.draw_graph(closest_node)
    
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = self.tree.item(selection[0])
        pid = int(item['values'][1])  # PID is in the second column
        
        self.selected_node = pid
        self.terminate_btn.configure(state="normal")
        self.draw_graph(pid)
    
    def terminate_selected(self):
        if not self.selected_node:
            return
            
        try:
            proc = psutil.Process(self.selected_node)
            proc.terminate()
            self.status_label.configure(text=f"Terminated process {self.selected_node}")
            self.terminate_btn.configure(state="disabled")
            self.start_analysis()  # Refresh the analysis
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.status_label.configure(
                text=f"Could not terminate process {self.selected_node}: {str(e)}"
            )
    
    def start_analysis(self):
        self.analyze_btn.configure(state="disabled")
        self.terminate_btn.configure(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.ax.clear()
        self.canvas.draw()
        
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting analysis...")
        
        Thread(
            target=self.analyze_memory,
            daemon=True
        ).start()
        
        self.after(100, self.check_queue)
    
    def check_queue(self):
        while not self.queue.empty():
            msg_type, data = self.queue.get()
            
            if msg_type == "status":
                self.status_label.configure(text=data)
            elif msg_type == "progress":
                self.progress_bar.set(data)
            elif msg_type == "error":
                self.status_label.configure(text=data)
                self.analyze_btn.configure(state="normal")
                return
            elif msg_type == "update_display":
                self.update_tree_with_top_processes()
                self.update_overview_graph()
                self.analyze_btn.configure(state="normal")
            
        if self.analyze_btn.cget("state") == "disabled":
            self.after(100, self.check_queue) 