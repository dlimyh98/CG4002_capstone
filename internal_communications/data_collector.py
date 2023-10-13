import os

# Define the path where you want to save the files
SAVE_DIRECTORY = "./data_files/"

# Ensure the directory exists
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

class DataCollector:
    """Class to handle data storage operations."""
    
    def __init__(self, person_name, action):
        """Initialize the data collector with a fixed file."""
        self.filename = f"{person_name}_{action}.txt"
        self.filepath = os.path.join(SAVE_DIRECTORY, self.filename)
        
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
