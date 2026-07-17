import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Windows Depth Clock CLI & Launcher")
    parser.add_argument("--daemon", action="store_true", help="Start the desktop background renderer directly without opening the GUI")
    parser.add_argument("--overlay", action="store_true", help="Start in click-through overlay mode instead of WorkerW background mode")
    
    args = parser.parse_args()
    
    if args.daemon:
        # Start wallpaper daemon directly
        import wallpaper_daemon
        wallpaper_daemon.main()
    else:
        # Start the GUI Settings Application directly in the same process
        import gui
        app = gui.DepthClockGUI()
        app.mainloop()

if __name__ == "__main__":
    main()
