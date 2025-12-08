"""
Cloud Storage Configuration for BRIDGE
Handles Google Drive integration for database sync
"""

import os
import platform

# Google Drive folder path
# User should update this to their local Google Drive folder path
GOOGLE_DRIVE_FOLDER = None

# Auto-detect Google Drive folder based on OS
def get_google_drive_path():
    """Auto-detect Google Drive folder path"""
    system = platform.system()
    username = os.getenv('USERNAME') or os.getenv('USER')
    
    if system == "Windows":
        # Common Google Drive paths on Windows
        possible_paths = [
            f"C:\\Users\\{username}\\Google Drive",
            f"C:\\Users\\{username}\\GoogleDrive",
            os.path.expanduser("~/Google Drive"),
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            f"/Users/{username}/Google Drive",
            os.path.expanduser("~/Google Drive"),
        ]
    else:  # Linux
        possible_paths = [
            f"/home/{username}/Google Drive",
            os.path.expanduser("~/Google Drive"),
        ]
    
    # Check which path exists
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def get_database_path():
    """
    Get the database file path
    If Google Drive is configured, use it. Otherwise use local.
    """
    # Check if user has set custom Google Drive path
    if GOOGLE_DRIVE_FOLDER and os.path.exists(GOOGLE_DRIVE_FOLDER):
        bridge_folder = os.path.join(GOOGLE_DRIVE_FOLDER, "BRIDGE")
        
        # Create BRIDGE folder if it doesn't exist
        if not os.path.exists(bridge_folder):
            os.makedirs(bridge_folder)
        
        return os.path.join(bridge_folder, "bridge_data.db")
    
    # Try to auto-detect Google Drive
    gdrive_path = get_google_drive_path()
    if gdrive_path:
        bridge_folder = os.path.join(gdrive_path, "BRIDGE")
        
        # Create BRIDGE folder if it doesn't exist
        if not os.path.exists(bridge_folder):
            try:
                os.makedirs(bridge_folder)
                return os.path.join(bridge_folder, "bridge_data.db")
            except:
                pass  # Fall back to local
    
    # Fall back to local database
    return "bridge_data.db"


def setup_google_drive(folder_path: str):
    """
    Set up Google Drive folder for BRIDGE
    
    Args:
        folder_path: Path to Google Drive folder
        
    Returns:
        Success status and message
    """
    global GOOGLE_DRIVE_FOLDER
    
    if not os.path.exists(folder_path):
        return False, f"Folder does not exist: {folder_path}"
    
    # Create BRIDGE subfolder
    bridge_folder = os.path.join(folder_path, "BRIDGE")
    try:
        if not os.path.exists(bridge_folder):
            os.makedirs(bridge_folder)
        
        GOOGLE_DRIVE_FOLDER = folder_path
        
        # Test write access
        test_file = os.path.join(bridge_folder, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        return True, f"Google Drive configured: {bridge_folder}"
        
    except Exception as e:
        return False, f"Error setting up Google Drive: {str(e)}"


def get_cloud_status():
    """Get current cloud storage status"""
    db_path = get_database_path()
    
    if "Google Drive" in db_path or "GoogleDrive" in db_path:
        return {
            'enabled': True,
            'provider': 'Google Drive',
            'path': db_path,
            'synced': os.path.exists(db_path)
        }
    else:
        return {
            'enabled': False,
            'provider': 'Local',
            'path': db_path,
            'synced': False
        }
