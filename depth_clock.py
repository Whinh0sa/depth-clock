import sys
import os
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Windows Depth Clock CLI & Launcher")
    parser.add_argument("--daemon", action="store_true", help="Start the desktop background renderer directly without opening the GUI")
    parser.add_argument("--overlay", action="store_true", help="Start in click-through overlay mode instead of WorkerW background mode")
    
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.daemon:
        # Start wallpaper daemon directly
        import wallpaper_daemon
        wallpaper_daemon.main()
    else:
        # Start the GUI Settings Application
        print("Launching Depth Clock Configuration Panel...")
        cmd = ["python", os.path.join(script_dir, "gui.py")]
        subprocess.Popen(cmd, cwd=script_dir)

if __name__ == "__main__":
    main()
