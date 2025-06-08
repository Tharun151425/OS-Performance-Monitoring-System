import customtkinter as ctk
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import time
from datetime import datetime
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
import os
import platform
import ctypes

from src.utils.theme_manager import ThemeManager
from src.utils.system_metrics import SystemMetrics
from src.components.metric_components import MetricBox, GraphFrame, PieChartFrame
from src.components.memory_analyzer import MemoryAnalyzerTab
from src.components.disk_analyzer import DiskAnalyzerTab

class SystemMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("System Monitor Pro")
        self.geometry("1400x900")
        
        self.theme_manager = ThemeManager()
        self.colors = self.theme_manager.current_theme
        self.configure(fg_color=self.colors["bg"])
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.history = {
            'time': [],
            'cpu': [],
            'memory': [],
            'virtual': [],
            'disk': []
        }
        
        self.create_sidebar()
        self.create_main_area()
        self.create_status_bar()
        
        self.running = True
        self.monitor_thread = Thread(target=self.update_metrics, daemon=True)
        self.monitor_thread.start()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color=self.colors["surface"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo and theme switch
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20,10), sticky="ew")
        
        ctk.CTkLabel(header_frame, text="SYSTEM\nMONITOR", 
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=self.colors["accent"]).pack()
        
        theme_switch = ctk.CTkSwitch(header_frame, text="Dark Mode", command=self.toggle_theme,
                                   progress_color=self.colors["accent"],
                                   button_color=self.colors["accent"])
        theme_switch.pack(pady=10)
        theme_switch.select() if self.theme_manager.is_dark else theme_switch.deselect()
        
        # Navigation buttons
        sections = {
            "Overview": "🏠", "CPU": "⚡", "Memory": "💾",
            "Virtual Memory": "📊", "Disk": "💿", "Memory Analyzer": "🔍",
            "Disk Analyzer": "🗂️"
        }
        
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        for section, icon in sections.items():
            btn = ctk.CTkButton(nav_frame, text=f" {icon} {section}",
                              command=lambda s=section: self.show_section(s),
                              fg_color="transparent", hover_color=self.colors["accent"],
                              height=45, anchor="w", font=ctk.CTkFont(size=14))
            btn.pack(fill="x", pady=2)

    def create_main_area(self):
        self.canvas = ctk.CTkCanvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.main_frame = ctk.CTkFrame(self.canvas)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.scrollbar.grid(row=0, column=2, sticky="ns")
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        
        self.sections = {}
        self.create_overview_section()
        self.create_cpu_section()
        self.create_memory_section()
        self.create_virtual_memory_section()
        self.create_disk_section()
        self.create_memory_analyzer_section()
        self.create_disk_analyzer_section()
        
        self.main_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        self.show_section("Overview")

    def create_overview_section(self):
        section = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        section.grid_columnconfigure((0, 1), weight=1)
        
        # System info
        sys_info = SystemMetrics.get_system_info()
        sys_frame = ctk.CTkFrame(section, fg_color=self.colors["surface"])
        sys_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        sys_info_text = (
            f"Operating System: {sys_info['os']}\n"
            f"CPU: {sys_info['cpu']}\n"
            f"Total Cores: {sys_info['total_cores']} ({sys_info['physical_cores']} Physical)\n"
            f"Architecture: {sys_info['architecture']}"
        )
        
        ctk.CTkLabel(sys_frame, text=sys_info_text, font=ctk.CTkFont(size=14)).pack(pady=15)
        
        # Metric boxes
        self.overview_boxes = {}
        metrics = [
            ("CPU", "CPU Usage", 1, 0),
            ("Memory", "Memory Usage", 1, 1),
            ("Disk", "Disk Usage", 2, 0),
            ("Virtual Memory", "Virtual Memory", 2, 1)
        ]
        
        for key, title, row, col in metrics:
            box = MetricBox(section, title)
            box.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            self.overview_boxes[key] = box
        
        # Performance graph
        perf_graph = GraphFrame(section, "System Performance Overview", "Usage (%)")
        perf_graph.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.overview_boxes["Performance"] = perf_graph
        
        self.sections["Overview"] = section

    def create_cpu_section(self):
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.cpu_boxes = {}
        metrics = ["CPU Usage", "CPU Frequency", "Core Count", "Thread Count"]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)
            box.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            self.cpu_boxes[metric] = box
        
        self.cpu_pie = PieChartFrame(section, "CPU Usage")
        self.cpu_pie.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.cpu_graph = GraphFrame(section, "CPU Usage Over Time", "Usage (%)")
        self.cpu_graph.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.sections["CPU"] = section

    def create_memory_section(self):
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.mem_boxes = {}
        metrics = ["Total Memory", "Available Memory", "Used Memory", "Memory Percentage"]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)
            box.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            self.mem_boxes[metric] = box
        
        self.mem_pie = PieChartFrame(section, "Memory Usage")
        self.mem_pie.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.mem_graph = GraphFrame(section, "Memory Usage Over Time", "Usage (%)")
        self.mem_graph.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.sections["Memory"] = section

    def create_virtual_memory_section(self):
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.vm_boxes = {}
        metrics = [
            "Total Virtual Memory", "Available Virtual Memory",
            "Used Virtual Memory", "Page File Usage",
            "Commit Charge", "Commit Limit",
            "Peak Commit", "Page Faults"
        ]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)
            box.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            self.vm_boxes[metric] = box
        
        self.vm_pie = PieChartFrame(section, "Virtual Memory Usage")
        self.vm_pie.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.vm_graph = GraphFrame(section, "Virtual Memory Usage Over Time", "Usage (%)")
        self.vm_graph.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.sections["Virtual Memory"] = section

    def create_disk_section(self):
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.disk_boxes = {}
        metrics = ["Total Disk Space", "Used Disk Space", "Free Disk Space", "Disk Usage Percentage"]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)
            box.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            self.disk_boxes[metric] = box
        
        self.disk_pie = PieChartFrame(section, "Disk Usage")
        self.disk_pie.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.disk_graph = GraphFrame(section, "Disk Usage Over Time", "Usage (%)")
        self.disk_graph.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.sections["Disk"] = section

    def create_memory_analyzer_section(self):
        self.sections["Memory Analyzer"] = MemoryAnalyzerTab(self.main_frame, self.colors)

    def create_disk_analyzer_section(self):
        self.sections["Disk Analyzer"] = DiskAnalyzerTab(self.main_frame, self.colors)

    def create_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=self.colors["surface"])
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        sys_info = ctk.CTkLabel(
            self.status_bar,
            text=f"OS: {os.name.upper()} | CPU: {platform.processor()}",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        sys_info.pack(side="left", padx=15)
        
        self.clock_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        self.clock_label.pack(side="right", padx=15)
        self.update_clock()

    def update_clock(self):
        self.clock_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def update_metrics(self):
        while self.running:
            try:
                # Get metrics
                cpu_metrics = SystemMetrics.get_cpu_metrics()
                memory_metrics = SystemMetrics.get_memory_metrics()
                vm_metrics = SystemMetrics.get_virtual_memory_metrics()
                disk_metrics = SystemMetrics.get_disk_metrics()
                
                current_time = datetime.now()
                
                # Update history
                self.history['time'].append(current_time)
                self.history['cpu'].append(cpu_metrics['cpu_percent'])
                self.history['memory'].append(memory_metrics['percent'])
                self.history['virtual'].append(vm_metrics['swap_percent'])
                self.history['disk'].append(disk_metrics['percent'])

                if len(self.history['time']) > 60:
                    for key in self.history:
                        self.history[key].pop(0)

                # Update overview boxes
                if hasattr(self, 'overview_boxes'):
                    self.overview_boxes["CPU"].value_label.configure(text=f"{cpu_metrics['cpu_percent']:.1f}%")
                    self.overview_boxes["Memory"].value_label.configure(text=f"{memory_metrics['percent']:.1f}%")
                    self.overview_boxes["Disk"].value_label.configure(text=f"{disk_metrics['percent']:.1f}%")
                    self.overview_boxes["Virtual Memory"].value_label.configure(text=f"{vm_metrics['swap_percent']:.1f}%")
                    
                    if "Performance" in self.overview_boxes:
                        perf_graph = self.overview_boxes["Performance"]
                        self.update_performance_graph(perf_graph)

                # Update CPU section
                self.update_cpu_section(cpu_metrics)
                
                # Update Memory section
                self.update_memory_section(memory_metrics)
                
                # Update Virtual Memory section
                self.update_vm_section(vm_metrics)
                
                # Update Disk section
                self.update_disk_section(disk_metrics)

                time.sleep(1)

            except Exception as e:
                print(f"Error updating metrics: {e}")
                time.sleep(1)

    def update_performance_graph(self, graph):
        graph.ax.clear()
        graph.ax.plot(self.history['time'], self.history['cpu'], label="CPU", color="#00A9FF")
        graph.ax.plot(self.history['time'], self.history['memory'], label="Memory", color="#FF6B6B")
        graph.ax.plot(self.history['time'], self.history['disk'], label="Disk", color="#32CD32")
        
        graph.ax.legend(loc='upper right')
        graph.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        graph.ax.set_xlabel("Time")
        graph.ax.set_ylabel("Usage (%)")
        
        graph.canvas.draw()

    def update_cpu_section(self, metrics):
        self.cpu_boxes["CPU Usage"].value_label.configure(text=f"{metrics['cpu_percent']:.1f}%")
        self.cpu_boxes["CPU Frequency"].value_label.configure(text=f"{metrics['cpu_freq']} MHz")
        self.cpu_boxes["Core Count"].value_label.configure(text=f"{metrics['core_count']} Cores")
        self.cpu_boxes["Thread Count"].value_label.configure(text=f"{metrics['thread_count']} Threads")
        
        self.cpu_pie.update_chart(
            ["Used", "Idle"],
            [metrics['cpu_percent'], 100 - metrics['cpu_percent']],
            ["#FF6347", "#32CD32"]
        )
        
        self.cpu_graph.ax.clear()
        self.cpu_graph.ax.plot(self.history['time'], self.history['cpu'], color="tomato")
        self.cpu_graph.ax.set_xlabel("Time")
        self.cpu_graph.ax.set_ylabel("CPU Usage (%)")
        self.cpu_graph.canvas.draw()

    def update_memory_section(self, metrics):
        self.mem_boxes["Total Memory"].value_label.configure(text=f"{metrics['total']:.2f} GB")
        self.mem_boxes["Used Memory"].value_label.configure(text=f"{metrics['used']:.2f} GB")
        self.mem_boxes["Available Memory"].value_label.configure(text=f"{metrics['available']:.2f} GB")
        self.mem_boxes["Memory Percentage"].value_label.configure(text=f"{metrics['percent']:.1f}%")
        
        self.mem_pie.update_chart(
            ["Used", "Free"],
            [metrics['percent'], 100 - metrics['percent']],
            ["#FF6347", "#32CD32"]
        )
        
        self.mem_graph.ax.clear()
        self.mem_graph.ax.plot(self.history['time'], self.history['memory'], color="coral")
        self.mem_graph.ax.set_xlabel("Time")
        self.mem_graph.ax.set_ylabel("Memory Usage (%)")
        self.mem_graph.canvas.draw()

    def update_vm_section(self, metrics):
        self.vm_boxes["Total Virtual Memory"].value_label.configure(text=f"{metrics['total']:.2f} GB")
        self.vm_boxes["Used Virtual Memory"].value_label.configure(text=f"{metrics['used']:.2f} GB")
        self.vm_boxes["Available Virtual Memory"].value_label.configure(text=f"{metrics['available']:.2f} GB")
        self.vm_boxes["Page File Usage"].value_label.configure(text=f"{metrics['swap_percent']:.1f}%")
        self.vm_boxes["Commit Charge"].value_label.configure(text=f"{metrics['commit_charge']:.2f} GB")
        self.vm_boxes["Commit Limit"].value_label.configure(text=f"{metrics['commit_limit']:.2f} GB")
        self.vm_boxes["Peak Commit"].value_label.configure(text=f"{metrics['peak_commit']:.2f} GB")
        self.vm_boxes["Page Faults"].value_label.configure(text=str(metrics['page_faults']))
        
        self.vm_pie.update_chart(
            ["Used", "Free"],
            [metrics['swap_percent'], 100 - metrics['swap_percent']],
            ["#FF6347", "#32CD32"]
        )
        
        self.vm_graph.ax.clear()
        self.vm_graph.ax.plot(self.history['time'], self.history['virtual'], color="yellowgreen")
        self.vm_graph.ax.set_xlabel("Time")
        self.vm_graph.ax.set_ylabel("Virtual Memory Usage (%)")
        self.vm_graph.canvas.draw()

    def update_disk_section(self, metrics):
        self.disk_boxes["Total Disk Space"].value_label.configure(text=f"{metrics['total']:.2f} GB")
        self.disk_boxes["Used Disk Space"].value_label.configure(text=f"{metrics['used']:.2f} GB")
        self.disk_boxes["Free Disk Space"].value_label.configure(text=f"{metrics['free']:.2f} GB")
        self.disk_boxes["Disk Usage Percentage"].value_label.configure(text=f"{metrics['percent']:.1f}%")
        
        self.disk_pie.update_chart(
            ["Used", "Free"],
            [metrics['percent'], 100 - metrics['percent']],
            ["#FF6347", "#32CD32"]
        )
        
        self.disk_graph.ax.clear()
        self.disk_graph.ax.plot(self.history['time'], self.history['disk'], color="dodgerblue")
        self.disk_graph.ax.set_xlabel("Time")
        self.disk_graph.ax.set_ylabel("Disk Usage (%)")
        self.disk_graph.canvas.draw()

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        min_width = self.main_frame.winfo_reqwidth()
        if event.width > min_width:
            self.canvas.itemconfig(self.canvas_window, width=event.width)

    def show_section(self, section_name):
        for section in self.sections.values():
            section.grid_remove()
        self.sections[section_name].grid(row=0, column=0, sticky="nsew")
        self.canvas.yview_moveto(0)

    def toggle_theme(self):
        self.colors = self.theme_manager.toggle_theme()
        ctk.set_appearance_mode("dark" if self.theme_manager.is_dark else "light")
        self.configure(fg_color=self.colors["bg"])
        # Update other UI elements as needed

    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = SystemMonitor()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()