import threading
import time
import logging
import sys
import keyboard
import argparse
from window_manager_soft import WindowPositioner
from window_hook_manager import WindowHookManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("HotkeyManager")


class HotkeyWindowManager:
    """
    Manage windows with hotkey support for controlling the window manager.
    Default hotkeys:
    - Win+F11: Toggle window manager on/off
    - Win+F10: Force position all windows
    - Win+F9: Reload configuration
    """

    def __init__(self, auto_start=True):
        try:
            # Create the window positioner (just handles positioning)
            self.positioner = WindowPositioner()

            # Create the hook manager (handles window events)
            self.hook_manager = WindowHookManager(self.positioner)

            self.active = False
            self.setup_hotkeys()

            # Auto-start if requested
            if auto_start:
                self.start_manager()

        except Exception as e:
            logger.error(f"Error initializing window manager: {e}")
            raise

    def setup_hotkeys(self):
        """Set up the keyboard hotkeys"""
        logger.info("Setting up hotkeys...")
        try:
            # Toggle window manager
            keyboard.add_hotkey("win+f11", self.toggle_manager)

            # Force position all windows
            keyboard.add_hotkey("win+f10", self.force_position_all)

            # Reload configuration
            keyboard.add_hotkey("win+f9", self.reload_config)

            logger.info("Hotkeys set up successfully")
            logger.info("  Win+F11: Toggle window manager on/off")
            logger.info("  Win+F10: Force position all windows")
            logger.info("  Win+F9: Reload configuration")
        except Exception as e:
            logger.error(f"Error setting up hotkeys: {e}")
            raise

    def toggle_manager(self):
        """Toggle the window manager on/off"""
        if self.active:
            self.stop_manager()
        else:
            self.start_manager()

    def start_manager(self):
        """Start the window manager"""
        if not self.active:
            logger.info("Starting window hook manager...")
            if self.hook_manager.start():
                self.active = True
                logger.info("Window manager started")
            else:
                logger.error("Failed to start window manager")

    def stop_manager(self):
        """Stop the window manager"""
        if self.active:
            logger.info("Stopping window manager...")
            self.hook_manager.stop()
            self.active = False
            logger.info("Window manager stopped")

    def force_position_all(self):
        """Force position all windows according to configuration"""
        logger.info("Force positioning all windows...")
        count = self.positioner.position_all_manageable_windows()
        logger.info(f"Positioned {count} windows")

    def reload_config(self):
        """Reload the configuration file"""
        logger.info("Reloading configuration...")
        self.positioner.reload_config()

        # Reapply positions with new config
        self.force_position_all()

    def run(self):
        """Run the hotkey manager"""
        logger.info("Window manager hotkey service running")
        logger.info("Press Ctrl+C to exit")

        try:
            # Keep the program running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Exiting due to user interrupt")
            if self.active:
                self.stop_manager()


def main():
    """Main function to run the hotkey manager"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Window Manager with Hotkey Support")
    parser.add_argument(
        "--no-auto-start",
        action="store_true",
        help="Don't start window management automatically",
    )
    parser.add_argument(
        "--position-only",
        action="store_true",
        help="Just position windows once and exit",
    )
    args = parser.parse_args()

    # Print header
    print("Window Manager with Hotkey Support")
    print("-" * 50)

    try:
        if args.position_only:
            # Just position windows once and exit
            print("One-time positioning mode")
            positioner = WindowPositioner()
            count = positioner.position_all_manageable_windows()
            print(f"Positioned {count} windows")
            return 0

        # Normal mode with hotkeys
        print("Available hotkeys:")
        print("  Win+F11: Toggle window manager on/off")
        print("  Win+F10: Force position all windows")
        print("  Win+F9: Reload configuration")
        print("\nPress Ctrl+C to exit\n")

        # Create and run the hotkey manager
        manager = HotkeyWindowManager(auto_start=not args.no_auto_start)

        if args.no_auto_start:
            print("Window manager is NOT running (press Win+F11 to start)")
        else:
            print("Window manager is running (press Win+F11 to toggle)")

        # Run the hotkey service
        manager.run()

    except Exception as e:
        logger.error(f"Error in hotkey manager: {e}")
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
