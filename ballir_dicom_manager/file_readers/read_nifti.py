import numpy as np

from ballir_dicom_manager.file_readers.read_image_volume import ReadImageVolume
from ballir_dicom_manager.file_loaders.nifti_loader import NiftiLoader
from ballir_dicom_manager.file_viewers.array_viewer import ArrayViewer

class ReadNifti(ReadImageVolume):
    
    loader = NiftiLoader()
    
    def __init__(self, target_path):
        super().__init__(target_path)  
#         self.files = self.sorter.sort_dicom_files(self.files)
#         self.validator.validate(self.files)
        self.spacing = self.files[0].header.get_zooms()
        self.set_arr()
        
    def set_arr(self):
        self.arr = np.flip(self.files[0].get_fdata(), 1)
        self.viewer = ArrayViewer(self.arr, self.spacing)    

        
