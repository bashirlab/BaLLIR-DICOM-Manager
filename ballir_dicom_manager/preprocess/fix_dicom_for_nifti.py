import copy

import dicom2nifti

from ballir_dicom_manager.preprocess.dicom_validator import DicomVolumeValidator

class FixDicomForNifti(DicomVolumeValidator):
    
    def __init__(self, fill_missing_with_adjacent:bool = False):
        self.fill_missing_with_adjacent = fill_missing_with_adjacent
    
    def validate_for_nifti(self, dicom_files):
        return self.validate_slice_increment(dicom_files)
    
    def validate_slice_increment(self, dicom_files):
        try: 
            dicom2nifti.common.validate_slice_increment(dicom_files)
            return dicom_files
        except dicom2nifti.exceptions.ConversionValidationError as e:
            return self.correct_slice_increment(dicom_files)        
            
    def correct_slice_increment(self, dicom_files):
        
        # return next_best dicom slices (with key thing...)
        # rewrite slice locations as best
        dicom_slice_positions = self.return_all_tag_idx(dicom_files, tag = 'ImagePositionPatient', idx = 2)
#         step_size = self.slice_manager.return_step_size(dicom_slice_positions)
        step_size = self.slice_manager.return_step_size(dicom_files)
        print(f'step_size: {step_size}')
        assert step_size != 0, "step size cannot be equal to zero"
        best_slice_positions = self.slice_manager.return_best_positions(dicom_slice_positions, step_size)
        next_best_slice_positions = self.slice_manager.return_next_best_positions(dicom_slice_positions, best_slice_positions) 
        if not self.fill_missing_with_adjacent: 
            next_best_slice_positions = sorted(list(set(next_best_slice_positions)))
        dicom_files = self.return_next_best_slices(dicom_files, dicom_slice_positions, next_best_slice_positions) # may add duplicate slices
        return self.reset_slice_positions(dicom_files, best_slice_positions)

    def return_next_best_slices(self, dicom_files, dicom_slice_positions: list, next_best_slice_positions: list):
        return [copy.deepcopy(dicom_files[dicom_slice_positions.index(pos)]) for pos in next_best_slice_positions]
        
    def reset_slice_positions(self, dicom_files, best_slice_positions: list):
        for num, dicom_file in enumerate(dicom_files):
            dicom_file.ImagePositionPatient = [0, 0, best_slice_positions[num]]
            dicom_file.InstanceNumber = num
        return dicom_files

