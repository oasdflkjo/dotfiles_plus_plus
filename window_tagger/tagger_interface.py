from typing import Dict, List, Optional, Tuple, Any

class TaggerInterface:
    """Interface for window tagger functionality"""
    
    def get_active_window_info(self) -> Dict[str, Any]:
        """Get information about the currently active window"""
        raise NotImplementedError()
    
    def get_centered_zone(self) -> Dict[str, int]:
        """Get the centered zone dimensions"""
        raise NotImplementedError()
    
    def position_window_with_offsets(self, hwnd: int, base_x: int, base_y: int, 
                                   base_width: int, base_height: int, 
                                   x_offset: int, y_offset: int, 
                                   width_offset: int, height_offset: int) -> Tuple[int, int, int, int]:
        """Position window with base values and offsets"""
        raise NotImplementedError()
    
    def save_tag_definition(self, tag_definition: Dict[str, Any]) -> None:
        """Save a new tag definition
        
        The tag_definition should contain:
        - name: str - The name of the tag
        - process_name: Optional[str] - The process name to match
        - class_name: Optional[str] - The window class name to match
        - title_substring: Optional[str] - A substring to match in the window title
        """
        raise NotImplementedError()
    
    def save_offset(self, tag_name: str, x_offset: int, y_offset: int, 
                   width_offset: int, height_offset: int) -> None:
        """Save window offsets for a tag"""
        raise NotImplementedError()
    
    def get_existing_tag_info(self, window_info: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, int]]]:
        """Get existing tag information for a window
        
        Matches are made in the following order:
        1. Process name (if specified)
        2. Class name (if specified)
        3. Title substring (if specified)
        
        All specified criteria must match for a tag to be considered a match.
        """
        raise NotImplementedError()
    
    def center_active_window_with_tag(self) -> bool:
        """Center the active window using its tag definition if found"""
        raise NotImplementedError() 