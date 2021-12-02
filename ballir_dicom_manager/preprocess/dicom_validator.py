from ballir_dicom_manager.preprocess.dicom_tag_parser import DicomTagParser
from ballir_dicom_manager.preprocess.slice_manager import SliceManager

class DicomVolumeValidator(DicomTagParser):
    
    slice_manager = SliceManager()
    
    def __init__(self, allow: list):
        self.allow = allow
    
    def check_tag_consistent(self, dicom_files, tag: str) -> bool:
        return len(self.return_all_tag_unique(dicom_files, tag)) == 1
    
    def validate(self, dicom_files):
        if not 'SeriesNumber' in self.allow:
            assert self.check_tag_consistent(dicom_files, 'SeriesNumber'), f'mulitple SeriesNumber values found: {self.return_all_tag_unique(dicom_files, "SeriesNumber")}'
        
        