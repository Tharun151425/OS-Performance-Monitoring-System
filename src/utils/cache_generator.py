import os
import random
import string
import time

def generate_random_content(size_mb):
    """Generate random content of specified size in MB."""
    return os.urandom(size_mb * 1024 * 1024)

def create_cache_files():
    """Create synthetic cache files for demonstration."""
    home = os.path.expanduser("~")
    
    # Create demo cache directories
    cache_dirs = {
        "app_cache": {
            "size_range": (50, 100),  # MB
            "files": ["temp_data.cache", "user_session.tmp", "analytics.log"]
        },
        "browser_cache": {
            "size_range": (100, 200),
            "files": ["browser_history.cache", "cookies.tmp", "media_cache.dat"]
        },
        "system_cache": {
            "size_range": (20, 50),
            "files": ["system.log", "updates.tmp", "installer.cache"]
        }
    }
    
    total_size = 0
    created_files = []
    
    for dir_name, config in cache_dirs.items():
        cache_dir = os.path.join(home, f".{dir_name}")
        os.makedirs(cache_dir, exist_ok=True)
        
        for file_name in config["files"]:
            file_path = os.path.join(cache_dir, file_name)
            size_mb = random.randint(*config["size_range"])
            
            with open(file_path, 'wb') as f:
                f.write(generate_random_content(size_mb))
            
            total_size += size_mb
            created_files.append(file_path)
            
            # Add timestamp to make it look realistic
            access_time = time.time() - random.randint(3600, 86400)  # 1 hour to 1 day old
            os.utime(file_path, (access_time, access_time))
    
    print(f"Created {len(created_files)} cache files totaling {total_size} MB")
    print("Cache locations:")
    for file in created_files:
        print(f"- {file}")

if __name__ == "__main__":
    create_cache_files() 