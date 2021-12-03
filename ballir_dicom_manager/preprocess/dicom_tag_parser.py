import os

import dicom2nifti

class DicomSorter:
    
    def sort_dicom_files(self, dicom_files):
        return dicom2nifti.common.sort_dicoms(dicom_files)

class DicomWriter:
    
    def __init__(self):
        return        
    
    def save_all(self, dicom_files, destination_dir: str):
        if not os.path.exists(destination_dir): 
            os.makedirs(destination_dir)            
        for num, dicom_file in enumerate(dicom_files):
            dicom_file.save_as(os.path.join(destination_dir, f'{str(num).zfill(4)}.dcm')) 

class DicomTagParser:
    
    def __init__(self, allow = []):
        self.allow = allow
    
    def get_all_tag(self, dicom_files, tag: str) -> list:
        return [getattr(file, tag) for file  in dicom_files if hasattr(file, tag)]
    
    def get_all_tag_idx(self, dicom_files, tag: str, idx: int) -> list:
        return [getattr(file, tag)[idx] for file  in dicom_files if hasattr(file, tag)]
    
    def get_all_tag_unique(self, dicom_files, tag: str) -> list:
        return list(set(self.get_all_tag(dicom_files, tag)))
    
    def get_dicom_slice_spacing(self, dicom_files):
        assert all([hasattr(file, 'SpacingBetweenSlices') for file in dicom_files]), f'SpacingBetweenSlices tag not present in all files'
        dicom_slice_spacing = list(set([file.SpacingBetweenSlices for file in dicom_files]))
        if not 'SpacingBetweenSlices' in self.allow:
            assert len(dicom_slice_spacing) == 1, f'{len(dicom_slice_spacing)} spacings between slices detected: {dicom_slice_spacing}'
        return dicom_slice_spacing[0]

    def get_dicom_pixel_spacing(self, dicom_files):
        assert all([hasattr(file, 'PixelSpacing') for file in dicom_files])
        dicom_pixel_spacing = [list(x) for x in set(tuple(x) for x in [file.PixelSpacing[:2] for file in dicom_files])]
        if not 'PixelSpacing' in self.allow:
            assert len(dicom_pixel_spacing) == 1, f'{len(dicom_pixel_spacing)} XY spacings detected: {dicom_pixel_spacing}'
        return dicom_pixel_spacing[0]
    
    def get_dicom_spacing(self, dicom_files):
        return self.get_dicom_pixel_spacing(dicom_files) + [self.get_dicom_slice_spacing(dicom_files)]

   
    