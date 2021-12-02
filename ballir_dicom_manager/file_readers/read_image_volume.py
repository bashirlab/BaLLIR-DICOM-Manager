from abc import abstractmethod

from ballir_dicom_manager.file_loaders.file_loader import FileLoader

class ReadImageVolume:
    
    loader: FileLoader
        
    def __init__(self, target_path):
        self.files = self.loader.load_all_files(target_path)
        
    @abstractmethod
    def build_arr(self):
        """Return numpy array with pixel values in (Z, Y, X) shape."""
        
    def orthoview(self):
        return