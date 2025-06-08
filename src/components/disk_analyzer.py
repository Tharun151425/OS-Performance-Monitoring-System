import customtkinter as ctk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, messagebox
import os
import time
from threading import Thread, Lock
from queue import Queue
import psutil
from typing import Dict, List, Tuple
import numpy as np
import shutil

class DiskAnalyzerTab(ctk.CTkFrame):
    def __init__(self, master, colors=None, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors or {
            "bg": "#FFFFFF",
            "surface": "#F0F0F0",
            "text": "#000000",
            "accent": "#1E88E5",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#FF5252",
            "border": "#E0E0E0"
        }
        
        # Initialize data structures
        self.directory_sizes = {}
        self.G = nx.Graph()
        self.lock = Lock()
        self.queue = Queue()
        self.recommendations = []
        self.current_path = os.path.expanduser("~")
        self.selected_node = None
        
        # Cache locations to check
        self.cache_locations = [
            ".app_cache",
            ".browser_cache",
            ".system_temp"
        ]
        
        # Custom colors for directories
        self.dir_colors = [
            "#FF6B6B",  # Coral
            "#4ECDC4",  # Turquoise
            "#45B7D1",  # Sky Blue
            "#96CEB4",  # Sage
            "#FFEEAD",  # Cream
            "#D4A5A5",  # Dusty Rose
            "#9B59B6",  # Purple
        ]
        
        # Skip patterns for faster analysis
        self.skip_patterns = [
            "Windows", "Program Files", "Program Files (x86)", 
            "ProgramData", "$Recycle.Bin", "System Volume Information",
            "Recovery", "Config.Msi"
        ]
        
        self.create_layout()
        
    def create_layout(self):
        # Configure grid
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create left panel (graph)
        left_panel = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Controls at top
        controls_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        self.analyze_btn = ctk.CTkButton(
            controls_frame,
            text="Analyze Storage",
            command=self.start_analysis,
            fg_color=self.colors["accent"]
        )
        self.analyze_btn.pack(side="left", padx=5)
        
        self.back_btn = ctk.CTkButton(
            controls_frame,
            text="Back to Home",
            command=self.back_to_home,
            fg_color=self.colors["accent"],
            state="disabled"
        )
        self.back_btn.pack(side="left", padx=5)
        
        self.progress_bar = ctk.CTkProgressBar(controls_frame, width=200)
        self.progress_bar.pack(side="left", padx=10)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            controls_frame,
            text="Ready to analyze",
            text_color=self.colors["text"]
        )
        self.status_label.pack(side="left", padx=5)
        
        # Graph
        self.fig = plt.figure(figsize=(8, 8))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create right panel (recommendations)
        right_panel = ctk.CTkFrame(self, fg_color=self.colors["surface"])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Recommendations header
        header_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            header_frame,
            text="Storage Recommendations",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Add buttons frame
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.pack(side="right")
        
        self.delete_selected_btn = ctk.CTkButton(
            buttons_frame,
            text="Delete Selected",
            command=self.delete_selected,
            fg_color=self.colors["error"],
            state="disabled"
        )
        self.delete_selected_btn.pack(side="left", padx=5)
        
        self.optimize_btn = ctk.CTkButton(
            buttons_frame,
            text="Optimize All",
            command=self.optimize_storage,
            fg_color=self.colors["success"],
            state="disabled"
        )
        self.optimize_btn.pack(side="left", padx=5)
        
        # Create Treeview for recommendations
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            rowheight=30,
            background=self.colors["surface"],
            foreground="black",
            fieldbackground=self.colors["surface"]
        )
        
        self.tree = ttk.Treeview(
            right_panel,
            columns=("Type", "Size", "Action"),
            show="headings",
            selectmode="browse",
            style="Custom.Treeview"
        )
        
        # Configure columns
        self.tree.heading("Type", text="Type")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Action", text="Recommended Action")
        
        self.tree.column("Type", width=150)
        self.tree.column("Size", width=100)
        self.tree.column("Action", width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # Configure tree tags with darker colors
        self.tree.tag_configure("error", background="#FF7F7F", foreground="black")  # Darker red
        self.tree.tag_configure("warning", background="#FFB347", foreground="black")  # Darker orange
        self.tree.tag_configure("info", background="#87CEEB", foreground="black")  # Darker blue
        self.tree.tag_configure("cache", background="#98FB98", foreground="black")  # Darker green
        
        # Bind tree selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
    def back_to_home(self):
        """Return to home view."""
        self.current_path = os.path.expanduser("~")
        self.selected_node = None
        self.back_btn.configure(state="disabled")
        self.analyze_disk()
        
    def on_hover(self, event):
        """Handle hover events on the graph."""
        if not event.inaxes or not self.G.nodes():
            self.canvas.get_tk_widget().configure(cursor="")
            return
            
        # Find if mouse is over a node
        clicked_x, clicked_y = event.xdata, event.ydata
        for node in self.G.nodes():
            if node == "Home" or node == "Others":
                continue
                
            node_pos = self.G.nodes[node].get('pos', None)
            if node_pos is not None:  # Changed condition
                dist = np.sqrt((node_pos[0] - clicked_x)**2 + (node_pos[1] - clicked_y)**2)
                if dist < 0.1:  # Threshold for hovering
                    self.canvas.get_tk_widget().configure(cursor="hand2")
                    return
        
        self.canvas.get_tk_widget().configure(cursor="")

    def on_graph_click(self, event):
        """Handle click events on the graph."""
        if not event.inaxes or not self.G.nodes():
            return
            
        # Convert click coordinates to node
        clicked_x, clicked_y = event.xdata, event.ydata
        
        # Find closest node
        min_dist = float('inf')
        clicked_node = None
        
        for node in self.G.nodes():
            if node == "Home" or node == "Others":
                continue
                
            node_pos = self.G.nodes[node].get('pos', None)
            if node_pos is not None:  # Changed condition
                dist = np.sqrt((node_pos[0] - clicked_x)**2 + (node_pos[1] - clicked_y)**2)
                if dist < min_dist and dist < 0.1:  # Threshold for clicking
                    min_dist = dist
                    clicked_node = node
        
        if clicked_node:
            self.selected_node = clicked_node
            self.back_btn.configure(state="normal")
            self.current_path = os.path.join(self.current_path, clicked_node)
            self.analyze_disk()
            
    def should_skip_directory(self, path: str) -> bool:
        """Check if directory should be skipped for faster analysis."""
        basename = os.path.basename(path)
        return (
            basename.startswith(".") or
            basename.startswith("$") or
            basename in self.skip_patterns or
            any(pattern in path for pattern in self.skip_patterns)
        )
        
    def get_directory_size(self, path: str) -> int:
        """Safely calculate directory size with optimizations."""
        if self.should_skip_directory(path):
            return 0
            
        total = 0
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if entry.is_file():
                            total += entry.stat().st_size
                        elif entry.is_dir() and not self.should_skip_directory(entry.path):
                            total += self.get_directory_size(entry.path)
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            pass
        return total
        
    def on_tree_select(self, event):
        """Enable/disable delete button based on selection"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            if item['tags'] and item['tags'][0] in ['cache', 'warning']:
                self.delete_selected_btn.configure(state="normal")
                return
        self.delete_selected_btn.configure(state="disabled")

    def delete_selected(self):
        """Delete the selected item from the list"""
        selected = self.tree.selection()
        if not selected:
            return
            
        item_id = selected[0]
        item = self.tree.item(item_id)
        values = item['values']
        
        if not values:
            return
            
        path = values[0]  # First column contains the path
        try:
            full_path = os.path.join(self.current_path, path)
            if os.path.exists(full_path):
                if os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    
                # Remove from tree regardless of success
                self.tree.delete(item_id)
                messagebox.showinfo("Success", f"Deleted: {path}")
            else:
                # If file doesn't exist, still remove from tree
                self.tree.delete(item_id)
                
        except Exception as e:
            # If there's an error, still remove from tree
            self.tree.delete(item_id)
            messagebox.showwarning("Warning", f"Could not fully delete {path} due to permission error.")
        
        # Disable delete button if no selection
        self.delete_selected_btn.configure(state="disabled")
        
        # Update optimize button state
        if len(self.tree.get_children()) == 0:
            self.optimize_btn.configure(state="disabled")

    def check_cache_locations(self):
        """Check known cache locations and add to recommendations"""
        for cache_dir in self.cache_locations:
            try:
                full_path = os.path.join(self.current_path, cache_dir)
                if os.path.exists(full_path) and os.path.isdir(full_path):
                    # Add the directory itself
                    size = self.get_directory_size(full_path) / (1024 * 1024 * 1024)  # Convert to GB
                    if size > 0:
                        self.recommendations.append({
                            "path": cache_dir,
                            "size": f"{size:.2f} GB",
                            "type": "Cache Directory",
                            "action": "Safe to clean",
                            "tag": "cache"
                        })
                        
                        # Add individual files
                        for file in os.listdir(full_path):
                            file_path = os.path.join(full_path, file)
                            if os.path.isfile(file_path):
                                file_size = os.path.getsize(file_path) / (1024 * 1024 * 1024)  # GB
                                if file_size > 0:
                                    self.recommendations.append({
                                        "path": os.path.join(cache_dir, file),
                                        "size": f"{file_size:.2f} GB",
                                        "type": "Cache File",
                                        "action": "Safe to clean",
                                        "tag": "cache"
                                    })
            except (PermissionError, FileNotFoundError):
                continue

    def analyze_disk(self):
        """Analyze disk structure focusing on current directory."""
        try:
            self.queue.put(("status", "Scanning directories..."))
            self.queue.put(("progress", 0.1))
            
            # Get all directories and their sizes
            directories: List[Tuple[str, float]] = []
            other_size = 0
            
            # First scan for cache directories and files
            cache_patterns = [
                '.cache', '.tmp', '.temp', '.log', '.dat', '.db', 
                'cache', 'temp', 'temporary', 'log'
            ]
            
            for item in os.listdir(self.current_path):
                try:
                    full_path = os.path.join(self.current_path, item)
                    
                    # Skip system directories for faster analysis
                    if self.should_skip_directory(full_path):
                        continue
                    
                    is_cache = any(pattern in item.lower() for pattern in cache_patterns)
                    
                    if os.path.isdir(full_path):
                        size = self.get_directory_size(full_path) / (1024 * 1024 * 1024)  # Convert to GB
                        if size > 0.1:  # Only show directories larger than 100MB
                            directories.append((item, size))
                            
                            # Check if it's a cache directory
                            if is_cache:
                                # Add directory itself
                                self.recommendations.append({
                                    "path": item,
                                    "size": f"{size:.2f} GB",
                                    "type": "Cache Directory",
                                    "action": "Safe to clean",
                                    "tag": "cache"
                                })
                                
                                # Add individual files from cache directory
                                try:
                                    for subitem in os.listdir(full_path):
                                        subpath = os.path.join(full_path, subitem)
                                        if os.path.isfile(subpath):
                                            subsize = os.path.getsize(subpath) / (1024 * 1024 * 1024)  # GB
                                            if subsize > 0.01:  # Files larger than 10MB
                                                self.recommendations.append({
                                                    "path": os.path.join(item, subitem),
                                                    "size": f"{subsize:.2f} GB",
                                                    "type": "Cache File",
                                                    "action": "Safe to clean",
                                                    "tag": "cache"
                                                })
                                except (PermissionError, FileNotFoundError):
                                    continue
                            
                            elif size > 1:  # Directories larger than 1GB
                                self.recommendations.append({
                                    "path": item,
                                    "size": f"{size:.2f} GB",
                                    "type": "Large Directory",
                                    "action": "Review contents",
                                    "tag": "warning"
                                })
                    
                    elif os.path.isfile(full_path):
                        size = os.path.getsize(full_path) / (1024 * 1024 * 1024)
                        if size > 0.1 and is_cache:  # Cache files larger than 100MB
                            self.recommendations.append({
                                "path": item,
                                "size": f"{size:.2f} GB",
                                "type": "Cache File",
                                "action": "Safe to clean",
                                "tag": "cache"
                            })
                            
                except (PermissionError, FileNotFoundError, OSError):
                    continue
            
            # Also check specific cache locations
            cache_locations = [
                ".app_cache",
                ".browser_cache",
                ".system_temp",
                "AppData/Local/Temp",
                "AppData/Local/Microsoft/Windows/INetCache",
                "AppData/Local/Google/Chrome/User Data/Default/Cache",
                "AppData/Local/Mozilla/Firefox/Profiles"
            ]
            
            for cache_dir in cache_locations:
                try:
                    full_path = os.path.join(self.current_path, cache_dir)
                    if os.path.exists(full_path) and os.path.isdir(full_path):
                        size = self.get_directory_size(full_path) / (1024 * 1024 * 1024)
                        if size > 0:
                            # Add directory itself
                            self.recommendations.append({
                                "path": cache_dir,
                                "size": f"{size:.2f} GB",
                                "type": "System Cache",
                                "action": "Safe to clean",
                                "tag": "cache"
                            })
                            
                            # Add individual files
                            try:
                                for root, _, files in os.walk(full_path):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        rel_path = os.path.relpath(file_path, self.current_path)
                                        file_size = os.path.getsize(file_path) / (1024 * 1024 * 1024)
                                        if file_size > 0.01:  # Files larger than 10MB
                                            self.recommendations.append({
                                                "path": rel_path,
                                                "size": f"{file_size:.2f} GB",
                                                "type": "Cache File",
                                                "action": "Safe to clean",
                                                "tag": "cache"
                                            })
                            except (PermissionError, FileNotFoundError):
                                continue
                except (PermissionError, FileNotFoundError):
                    continue
            
            self.queue.put(("progress", 0.7))
            self.queue.put(("status", "Building visualization..."))
            
            # Sort by size and split into top 7 and others
            directories.sort(key=lambda x: x[1], reverse=True)
            top_dirs = directories[:7]
            other_dirs = directories[7:]
            other_size = sum(size for _, size in other_dirs)
            
            # Create graph
            self.G.add_node("Home", size=0, color="#2196F3")
            
            # Add top directories
            for i, (name, size) in enumerate(top_dirs):
                color = self.dir_colors[i % len(self.dir_colors)]
                self.G.add_node(name, size=size, color=color)
                self.G.add_edge("Home", name)
            
            # Add "Others" node if there are more directories
            if other_dirs:
                self.G.add_node("Others", size=other_size, color="#90A4AE")
                self.G.add_edge("Home", "Others")
            
            # Update recommendations tree
            for rec in self.recommendations:
                self.tree.insert(
                    "",
                    "end",
                    values=(rec["path"], rec["size"], rec["action"]),
                    tags=(rec["tag"],)
                )
            
            self.draw_graph()
            
            self.queue.put(("progress", 1.0))
            cache_count = sum(1 for rec in self.recommendations if rec["tag"] == "cache")
            cache_size = sum(float(rec["size"].split()[0]) for rec in self.recommendations if rec["tag"] == "cache")
            self.queue.put(("status", f"Found {cache_count} cleanable items ({cache_size:.1f} GB)"))
            self.queue.put(("complete", None))
            
            # Enable optimize button if we have recommendations
            if self.recommendations:
                self.optimize_btn.configure(state="normal")
            
        except Exception as e:
            self.queue.put(("status", "Could not complete analysis"))
            self.queue.put(("complete", None))
    
    def draw_graph(self):
        """Draw the directory structure graph with a clean, modern look."""
        self.ax.clear()
        
        if not self.G.nodes():
            return
        
        # Calculate positions in a circular layout
        pos = nx.circular_layout(self.G)
        
        # Move "Home" to center
        pos["Home"] = np.array([0.5, 0.5])
        
        # Adjust other nodes to be in a perfect circle
        other_nodes = [n for n in self.G.nodes() if n != "Home"]
        angles = np.linspace(0, 2 * np.pi, len(other_nodes), endpoint=False)
        radius = 0.35
        
        for node, angle in zip(other_nodes, angles):
            pos[node] = np.array([
                0.5 + radius * np.cos(angle),
                0.5 + radius * np.sin(angle)
            ])
            # Store position in node attributes for click detection
            self.G.nodes[node]['pos'] = pos[node]
        
        # Draw edges with gradient and animation effect
        for edge in self.G.edges():
            start_pos = pos[edge[0]]
            end_pos = pos[edge[1]]
            
            # Create curved edge effect
            mid_point = (
                (start_pos[0] + end_pos[0])/2 + np.random.uniform(-0.05, 0.05),
                (start_pos[1] + end_pos[1])/2 + np.random.uniform(-0.05, 0.05)
            )
            
            curve = plt.matplotlib.patches.ConnectionPatch(
                start_pos, end_pos,
                "data", "data",
                connectionstyle=f"arc3,rad={np.random.uniform(0.1, 0.2)}",
                color=self.colors["border"],
                alpha=0.3,
                zorder=1,
                linewidth=2
            )
            self.ax.add_patch(curve)
        
        # Draw nodes with shadow effect
        for node in self.G.nodes():
            size = self.G.nodes[node].get('size', 0)
            color = self.G.nodes[node].get('color', '#90A4AE')
            
            # Calculate node size
            if node == "Home":
                node_size = 3000
            else:
                node_size = min(5000, max(2000, size * 500))
            
            # Draw shadow
            shadow = plt.Circle(
                (pos[node][0] + 0.005, pos[node][1] - 0.005),
                node_size/20000,
                facecolor='black',
                alpha=0.2,
                zorder=1
            )
            self.ax.add_patch(shadow)
            
            # Draw node
            circle = plt.Circle(
                pos[node],
                node_size/20000,
                facecolor=color,
                edgecolor='white',
                linewidth=2,
                alpha=0.8,
                zorder=2
            )
            self.ax.add_patch(circle)
            
            # Add label with shadow effect
            if node == "Home":
                label = os.path.basename(self.current_path)
            else:
                label = f"{node}\n{size:.1f} GB"
            
            # Draw text shadow
            self.ax.text(
                pos[node][0] + 0.002,
                pos[node][1] - 0.002,
                label,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=9 if node != "Home" else 12,
                fontweight='bold',
                color='black',
                alpha=0.2,
                zorder=2
            )
            
            # Draw text
            self.ax.text(
                pos[node][0],
                pos[node][1],
                label,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=9 if node != "Home" else 12,
                fontweight='bold',
                color='white',
                zorder=3
            )
        
        # Set plot limits and remove axes
        self.ax.set_xlim(-0.1, 1.1)
        self.ax.set_ylim(-0.1, 1.1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_aspect('equal')
        
        # Set title with shadow effect
        title = "Storage Distribution"
        if self.current_path != os.path.expanduser("~"):
            title += f" - {os.path.basename(self.current_path)}"
        
        # Draw title shadow
        self.ax.text(
            0.5, 1.05,
            title,
            horizontalalignment='center',
            fontsize=14,
            fontweight='bold',
            color='black',
            alpha=0.2,
            transform=self.ax.transAxes
        )
        
        # Draw title
        self.ax.text(
            0.5, 1.05,
            title,
            horizontalalignment='center',
            fontsize=14,
            fontweight='bold',
            color=self.colors["text"],
            transform=self.ax.transAxes
        )
        
        # Update canvas
        self.fig.tight_layout()
        self.canvas.draw()
    
    def start_analysis(self):
        """Start the disk analysis process."""
        self.analyze_btn.configure(state="disabled")
        self.optimize_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting analysis...")
        
        # Clear previous data
        self.directory_sizes.clear()
        self.G.clear()
        self.recommendations.clear()
        self.tree.delete(*self.tree.get_children())
        
        # Start analysis thread
        Thread(target=self.analyze_disk, daemon=True).start()
        self.after(100, self.check_queue)
        
    def optimize_storage(self):
        """Clean up cache and temporary files."""
        try:
            # Get all cache items
            cache_items = []
            for item in self.tree.get_children():
                item_data = self.tree.item(item)
                if item_data["tags"][0] == "cache":
                    path = item_data["values"][0]
                    size = item_data["values"][1]
                    cache_items.append((item, path, size))
            
            if not cache_items:
                messagebox.showinfo("Optimization", "No cache files to clean")
                return
            
            # Show confirmation dialog with list of files
            message = "The following cache files will be deleted:\n\n"
            for _, path, size in cache_items:
                message += f"- {path} ({size})\n"
            message += "\nDo you want to proceed?"
            
            if not messagebox.askyesno("Confirm Cleanup", message):
                return
            
            # Proceed with deletion
            cleaned_size = 0
            cleaned_items = []
            failed_items = []
            
            for item_id, path, _ in cache_items:
                try:
                    full_path = os.path.join(self.current_path, path)
                    if os.path.exists(full_path):
                        if os.path.isfile(full_path):
                            size = os.path.getsize(full_path)
                            os.remove(full_path)
                            cleaned_size += size
                            cleaned_items.append(path)
                        elif os.path.isdir(full_path):
                            size = self.get_directory_size(full_path)
                            shutil.rmtree(full_path)
                            cleaned_size += size
                            cleaned_items.append(path)
                except (PermissionError, FileNotFoundError, OSError):
                    failed_items.append(path)
                
                # Remove from tree regardless of success/failure
                self.tree.delete(item_id)
            
            # Show results
            message = []
            if cleaned_items:
                cleaned_gb = cleaned_size / (1024**3)
                message.append(f"Successfully cleaned up {cleaned_gb:.2f} GB")
                message.append("\nRemoved items:")
                for item in cleaned_items:
                    message.append(f"- {item}")
            
            if failed_items:
                message.append("\nFailed to remove:")
                for item in failed_items:
                    message.append(f"- {item}")
            
            if message:
                messagebox.showinfo("Cleanup Complete", "\n".join(message))
            
            # Disable buttons if no items left
            if len(self.tree.get_children()) == 0:
                self.optimize_btn.configure(state="disabled")
                self.delete_selected_btn.configure(state="disabled")
                
        except Exception as e:
            messagebox.showerror("Error", "Could not complete optimization")
    
    def check_queue(self):
        """Check for updates from the analysis thread."""
        while not self.queue.empty():
            msg_type, data = self.queue.get()
            
            if msg_type == "status":
                self.status_label.configure(text=data)
            elif msg_type == "progress":
                self.progress_bar.set(data)
            elif msg_type == "complete":
                self.analyze_btn.configure(state="normal")
        
        if self.analyze_btn.cget("state") == "disabled":
            self.after(100, self.check_queue) 