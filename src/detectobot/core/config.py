"""Configuration handling for detectobot."""
import os
import yaml

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config.yaml'))

def load_config(section: str = None):
    """
    Load configuration from YAML file.
    
    Args:
        section: Optional section name to return only that section
        
    Returns:
        The entire config dict or just the specified section
    """
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    if section:
        return config.get(section, [])
    return config
