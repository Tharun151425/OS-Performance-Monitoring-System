import psutil
import platform
from datetime import datetime

class SystemMetrics:
    @staticmethod
    def get_system_info():
        return {
            "os": f"{platform.system()} {platform.release()}",
            "cpu": platform.processor(),
            "total_cores": psutil.cpu_count(),
            "physical_cores": psutil.cpu_count(logical=False),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def get_cpu_metrics():
        return {
            "cpu_percent": psutil.cpu_percent(),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else "N/A",
            "core_count": psutil.cpu_count(logical=False),
            "thread_count": psutil.cpu_count(logical=True)
        }

    @staticmethod
    def get_memory_metrics():
        virtual = psutil.virtual_memory()
        return {
            "total": virtual.total / (1024**3),
            "used": virtual.used / (1024**3),
            "available": virtual.available / (1024**3),
            "percent": virtual.percent
        }

    @staticmethod
    def get_virtual_memory_metrics():
        virtual = psutil.virtual_memory()
        swap = psutil.swap_memory()
        process = psutil.Process()
        
        return {
            "total": (virtual.total + swap.total) / (1024**3),
            "used": swap.used / (1024**3),
            "available": (virtual.available + swap.free) / (1024**3),
            "swap_percent": swap.percent,
            "commit_charge": process.memory_info().rss / (1024**3),  # Using RSS instead of private
            "commit_limit": (virtual.total + swap.total) / (1024**3),
            "peak_commit": process.memory_info().vms / (1024**3),  # Using VMS for Linux
            "page_faults": process.memory_info().num_page_faults if hasattr(process.memory_info(), 'num_page_faults') else 0
        }

    @staticmethod
    def get_disk_metrics(path='/'):
        try:
            disk = psutil.disk_usage(path)
            return {
                "total": disk.total / (1024**3),
                "used": disk.used / (1024**3),
                "free": disk.free / (1024**3),
                "percent": disk.percent
            }
        except Exception as e:
            print(f"Error getting disk metrics: {e}")
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "percent": 0
            } 