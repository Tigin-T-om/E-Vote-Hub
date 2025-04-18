import os
import shutil

# Customize this list based on what you consider "unwanted"
UNWANTED_EXTENSIONS = ['.pyc', '.pyo', '.log', '.DS_Store']
UNWANTED_DIRS = [
    '__pycache__',
    '.vscode',
    '.idea',
    'staticfiles',
    'media/static/images/profiles'  # adjust if some images are necessary
]

def is_unwanted_file(file_path):
    return any(file_path.endswith(ext) for ext in UNWANTED_EXTENSIONS)

def is_unwanted_dir(dir_path):
    return any(unwanted in dir_path for unwanted in UNWANTED_DIRS)

def cleanup_cursor():
    print("\n🔍 Scanning your project for unwanted files and directories...\n")
    for root, dirs, files in os.walk('.', topdown=True):
        # Check directories first
        for d in list(dirs):
            full_dir = os.path.join(root, d)
            if is_unwanted_dir(full_dir):
                print(f"📁 Found unwanted directory: {full_dir}")
                choice = input("❓ Do you want to delete this directory? (y/n): ").strip().lower()
                if choice == 'y':
                    shutil.rmtree(full_dir)
                    print(f"✅ Deleted: {full_dir}\n")
                else:
                    print("⏭️ Skipped\n")

        # Check files
        for f in files:
            full_file = os.path.join(root, f)
            if is_unwanted_file(full_file):
                print(f"🗑️ Found unwanted file: {full_file}")
                choice = input("❓ Do you want to delete this file? (y/n): ").strip().lower()
                if choice == 'y':
                    os.remove(full_file)
                    print(f"✅ Deleted: {full_file}\n")
                else:
                    print("⏭️ Skipped\n")

    print("🎉 Scan complete!")

if __name__ == "__main__":
    cleanup_cursor()
