import pathlib

import numpy as np

from ballir_dicom_manager.file_viewers.array_viewer import ArrayViewer
from ballir_dicom_manager.file_readers.read_image_volume import ReadImageVolume
from ballir_dicom_manager.file_loaders.dicom_loader import DicomLoader
from ballir_dicom_manager.preprocess.dicom_tag_parser import DicomSorter, DicomWriter, DicomTagParser
from ballir_dicom_manager.preprocess.dicom_validator import DicomVolumeValidator
from ballir_dicom_manager.preprocess.fix_dicom_for_nifti import FixDicomForNifti

class ReadDicom(ReadImageVolume):
    
    loader = DicomLoader()
    sorter = DicomSorter()
    writer = DicomWriter()
    nifti_fixer = FixDicomForNifti(fill_missing_with_adjacent = False)
    
    def __init__(self, target_path: pathlib.Path, allow = []):
        super().__init__(target_path)  
        self.files = self.sorter.sort_dicom_files(self.files)
        
        self.validator = DicomVolumeValidator(allow)
        self.validator.validate(self.files)
        
        self.parser = DicomTagParser(allow)
        self.spacing = self.parser.get_dicom_spacing(self.files)
        
        self.set_arr()
        
    def set_arr(self) -> None:
        self.arr = np.swapaxes(np.array([file.pixel_array for file in self.files]), 0, 2)
        self.viewer = ArrayViewer(self.arr, self.spacing)    
        
    def prep_for_nifti(self) -> None:
        self.files = self.nifti_fixer.validate_for_nifti(self.files)
        self.set_arr()