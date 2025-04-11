import os
import shutil
import json
import datetime
import csv

class ProjectManager:
    def __init__(self):
        """Initialize the Project Manager"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.projects_dir = os.path.join(self.base_dir, "Projects")
        self.current_project = None
        self.ensure_projects_directory()
        
    def ensure_projects_directory(self):
        """Ensure the Projects directory exists"""
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)
            print(f"Created Projects directory at {self.projects_dir}")
    
    def get_projects_list(self):
        """Get a list of all projects"""
        self.ensure_projects_directory()
        return [d for d in os.listdir(self.projects_dir) 
                if os.path.isdir(os.path.join(self.projects_dir, d))]
    
    def create_project(self, project_name):
        """Create a new project with the given name"""
        if not project_name:
            raise ValueError("Project name cannot be empty")
            
        # Sanitize project name (remove invalid characters)
        project_name = "".join([c for c in project_name if c.isalnum() or c in "_ -"])
        
        # Create project directory
        project_dir = os.path.join(self.projects_dir, project_name)
        
        if os.path.exists(project_dir):
            raise ValueError(f"Project '{project_name}' already exists")
        
        # Create project directory and subdirectories
        subdirs = ["Scenes", "Transcript", "Audio", "RawVideo", "Clips", "Output", "Research"]
        os.makedirs(project_dir)
        
        for subdir in subdirs:
            os.makedirs(os.path.join(project_dir, subdir))
        
        # Create project metadata
        metadata = {
            "name": project_name,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        with open(os.path.join(project_dir, "project.json"), "w") as f:
            json.dump(metadata, f, indent=4)
        
        self.current_project = project_name
        print(f"Created new project: {project_name}")
        return project_name
    
    def load_project(self, project_name):
        """Load an existing project"""
        project_dir = os.path.join(self.projects_dir, project_name)
        
        if not os.path.exists(project_dir):
            raise ValueError(f"Project '{project_name}' does not exist")
        
        # Update metadata
        metadata_path = os.path.join(project_dir, "project.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            metadata["updated_at"] = datetime.datetime.now().isoformat()
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=4)
        
        self.current_project = project_name
        print(f"Loaded project: {project_name}")
        return project_name
    
    def get_project_path(self, subfolder=None):
        """Get the full path to the current project or a subfolder within it"""
        if not self.current_project:
            raise ValueError("No project is currently loaded")
        
        project_dir = os.path.join(self.projects_dir, self.current_project)
        
        if subfolder:
            return os.path.join(project_dir, subfolder)
        return project_dir

# Function to get a ProjectManager instance
def get_project_manager():
    return ProjectManager() 