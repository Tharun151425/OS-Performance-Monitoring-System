import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

class MetricBox(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        
        main_window = self.winfo_toplevel()
        colors = main_window.colors
        
        self.configure(
            fg_color=colors["surface"],
            corner_radius=15,
            border_width=1,
            border_color=colors["border"]
        )
        
        gradient_canvas = ctk.CTkCanvas(
            self,
            height=4,
            width=self.winfo_width(),
            highlightthickness=0
        )
        gradient_canvas.pack(fill="x", side="top")
        
        def create_gradient():
            width = gradient_canvas.winfo_width()
            height = 4
            gradient_canvas.delete("gradient")
            
            for i in range(width):
                x = i / width
                r1, g1, b1 = tuple(int(colors["gradient"][0].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                r2, g2, b2 = tuple(int(colors["gradient"][1].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                r = int(r1 + (r2-r1) * x)
                g = int(g1 + (g2-g1) * x)
                b = int(b1 + (b2-b1) * x)
                color = f'#{r:02x}{g:02x}{b:02x}'
                gradient_canvas.create_line(i, 0, i, height, fill=color, tags="gradient")
        
        gradient_canvas.bind('<Configure>', lambda e: create_gradient())
        
        icons = {
            "CPU": "⚡", "Memory": "💾", "Disk": "💿",
            "Virtual Memory": "📊", "Core Count": "🔢",
            "Thread Count": "🧵", "CPU Usage": "📈",
            "CPU Frequency": "⚙️"
        }
        
        icon = icons.get(title, "📊")
        
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(15,5))
        
        icon_label = ctk.CTkLabel(
            title_frame,
            text=icon,
            font=ctk.CTkFont(size=20)
        )
        icon_label.pack(side="left", padx=5)
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors["accent"]
        )
        self.title_label.pack(side="left", padx=5)
        
        value_frame = ctk.CTkFrame(self, fg_color="transparent")
        value_frame.pack(pady=(5,15))
        
        self.value_label = ctk.CTkLabel(
            value_frame,
            text="--",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=colors["text"]
        )
        self.value_label.pack()

class GraphFrame(ctk.CTkFrame):
    def __init__(self, master, title, ylabel, **kwargs):
        super().__init__(master, **kwargs)
        
        main_window = self.winfo_toplevel()
        colors = main_window.colors
        
        self.configure(
            fg_color=colors["surface"],
            corner_radius=15,
            border_width=1,
            border_color=colors["border"]
        )
        
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=15, pady=(15,5))
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors["accent"]
        )
        title_label.pack(side="left")
        
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
        
        self.ax.set_facecolor(colors["surface"])
        self.fig.patch.set_facecolor(colors["surface"])
        
        self.ax.grid(True, linestyle='--', alpha=0.2, color=colors["border"])
        self.ax.tick_params(colors=colors["text"], labelsize=9)
        
        for spine in self.ax.spines.values():
            spine.set_color(colors["border"])
            spine.set_linewidth(0.5)

class PieChartFrame(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        self.title_label = ctk.CTkLabel(
            self, 
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(4, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ax.axis('equal')  

    def update_chart(self, labels, sizes, colors):
        self.ax.clear()
        self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        self.ax.set_title("Usage Distribution")
        self.canvas.draw() 