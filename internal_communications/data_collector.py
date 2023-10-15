import os

# Define the path where you want to save the files
SAVE_DIRECTORY = "./data_files/"

class DataCollector:
    """Class to handle data storage operations."""
    
    def __init__(self, person_name, action):
        """Initialize the data collector with a fixed file."""
        
        # Create a sub-directory for the action
        self.action_directory = os.path.join(SAVE_DIRECTORY, action)
        
        # Ensure the sub-directory exists
        if not os.path.exists(self.action_directory):
            os.makedirs(self.action_directory)
        
        # Set the file path within the sub-directory
        self.filename = f"{person_name}_{action}.txt"
        self.filepath = os.path.join(self.action_directory, self.filename)
        
        # Clear the file content if it exists
        open(self.filepath, 'w').close()

    def store_data(self, data):
        """Append data to the initialized file."""
        with open(self.filepath, 'a') as f:
            f.write(str(data) + "\n")

# Usage:
# Initialize DataCollector once per run
# collector = DataCollector("John", "jump")

# Whenever you want to save data during the run
# collector.store_data(accel_data)
