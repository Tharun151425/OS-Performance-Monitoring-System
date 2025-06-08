import os
import random
import time
from pathlib import Path

def create_synthetic_cache():
    """Create synthetic cache files for testing disk analyzer."""
    home = Path.home()
    
    # Define cache directories and their contents
    cache_structure = {
        ".app_cache": {
            "size_range": (50, 100),  # MB
            "files": [
                "temp_data.cache",
                "user_session.tmp",
                "analytics.log",
                "background_tasks.tmp"
            ]
        },
        ".browser_cache": {
            "size_range": (200, 400),
            "files": [
                "browser_history.cache",
                "cookies.tmp",
                "media_cache.dat",
                "downloads.tmp"
            ]
        },
        ".system_temp": {
            "size_range": (100, 200),
            "files": [
                "system.log",
                "updates.tmp",
                "installer.cache",
                "temp_downloads.dat"
            ]
        }
    }
    
    total_size = 0
    created_files = []
    
    print("Creating synthetic cache files for testing...")
    
    for dir_name, config in cache_structure.items():
        cache_dir = home / dir_name
        cache_dir.mkdir(exist_ok=True)
        
        print(f"\nCreating {dir_name}...")
        
        for file_name in config["files"]:
            file_path = cache_dir / file_name
            size_mb = random.randint(*config["size_range"])
            
            # Create file with random content
            with open(file_path, 'wb') as f:
                # Write in chunks to avoid memory issues
                chunk_size = 1024 * 1024  # 1MB
                remaining = size_mb * chunk_size
                
                while remaining > 0:
                    write_size = min(chunk_size, remaining)
                    f.write(os.urandom(write_size))
                    remaining -= write_size
            
            # Set old timestamp
            access_time = time.time() - random.randint(3600, 86400)  # 1 hour to 1 day old
            os.utime(file_path, (access_time, access_time))
            
            total_size += size_mb
            created_files.append(str(file_path))
            print(f"Created {file_name} ({size_mb} MB)")
    
    print(f"\nCreated {len(created_files)} cache files totaling {total_size} MB")
    print("Cache locations:")
    for file in created_files:
        print(f"- {file}")

if __name__ == "__main__":
    create_synthetic_cache() 