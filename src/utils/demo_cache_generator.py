import os
import random
import time
import json
from pathlib import Path

def generate_fake_json():
    """Generate fake JSON content for cache files."""
    return {
        "timestamp": time.time(),
        "session_id": ''.join(random.choices('0123456789abcdef', k=32)),
        "cache_version": "1.0",
        "data": {
            "user_preferences": {
                "theme": random.choice(["light", "dark", "system"]),
                "language": random.choice(["en", "es", "fr", "de"]),
                "notifications": random.choice([True, False])
            },
            "recent_files": [
                f"document_{i}.pdf" for i in range(random.randint(5, 15))
            ],
            "search_history": [
                "project report",
                "meeting notes",
                "presentation slides",
                "budget analysis"
            ]
        }
    }

def create_demo_cache():
    """Create demonstration cache files that look like real application cache."""
    home = Path.home()
    
    # Define cache structure
    cache_structure = {
        ".app_cache": {
            "vscode": {
                "files": [
                    ("workspace.cache", 50),  # MB
                    ("extensions.tmp", 75),
                    ("user_data.cache", 100)
                ]
            },
            "chrome": {
                "files": [
                    ("browser_cache.dat", 200),
                    ("media_cache.bin", 150),
                    ("thumbnails.cache", 80)
                ]
            }
        },
        ".browser_cache": {
            "mozilla": {
                "files": [
                    ("profile.cache", 120),
                    ("cookies.sqlite", 45),
                    ("favicons.dat", 30)
                ]
            },
            "edge": {
                "files": [
                    ("cache_data.tmp", 180),
                    ("history.dat", 90),
                    ("downloads.db", 150)
                ]
            }
        },
        ".system_temp": {
            "updates": {
                "files": [
                    ("pending_updates.tmp", 250),
                    ("installer_cache.bin", 175),
                    ("system_logs.dat", 85)
                ]
            },
            "apps": {
                "files": [
                    ("temp_data.cache", 120),
                    ("installer_files.tmp", 200),
                    ("crash_dumps.dat", 95)
                ]
            }
        }
    }
    
    total_size = 0
    created_files = []
    
    print("Creating demonstration cache files...")
    
    for main_dir, categories in cache_structure.items():
        main_path = home / main_dir
        main_path.mkdir(exist_ok=True)
        print(f"\nCreating {main_dir}...")
        
        for category, content in categories.items():
            category_path = main_path / category
            category_path.mkdir(exist_ok=True)
            print(f"  └─ {category}")
            
            for file_name, size_mb in content["files"]:
                file_path = category_path / file_name
                
                # Create file with appropriate content based on extension
                try:
                    with open(file_path, 'wb') as f:
                        if file_name.endswith(('.json', '.cache')):
                            # JSON-like content for cache files
                            json_content = json.dumps(generate_fake_json(), indent=2).encode('utf-8')
                            f.write(json_content)
                            # Pad to reach desired size
                            remaining = (size_mb * 1024 * 1024) - len(json_content)
                            if remaining > 0:
                                f.write(os.urandom(remaining))
                        else:
                            # Binary content for other files
                            f.write(os.urandom(size_mb * 1024 * 1024))
                    
                    # Set old timestamp
                    access_time = time.time() - random.randint(3600, 86400 * 7)  # 1 hour to 7 days old
                    os.utime(file_path, (access_time, access_time))
                    
                    total_size += size_mb
                    created_files.append(str(file_path))
                    print(f"    └─ Created {file_name} ({size_mb} MB)")
                    
                except Exception as e:
                    print(f"    ✗ Failed to create {file_name}: {e}")
    
    print(f"\nCreated {len(created_files)} cache files totaling {total_size} MB")
    print("\nCache locations:")
    for file in created_files:
        print(f"- {file}")
    
    print("\nYou can now run the disk analyzer to detect and clean these files!")

if __name__ == "__main__":
    create_demo_cache() 