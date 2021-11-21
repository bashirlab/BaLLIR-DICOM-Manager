from abc import ABC, abstractmethod
from typing import List

import pydicom as dcm
import numpy as np
from collections import namedtuple


class DicomFilter(ABC):

    def __init__(self, filter_arg: tuple) -> None:
        pass

    @abstractmethod
    def filter_files(self, dicom_files: List[dcm.dataset.Dataset]) -> List[dcm.dataset.Dataset]:
        """Sort or filter DICOM files."""

    def return_position(self, dicom_file):
        """Return DICOM slice Z-position."""
        if hasattr(dicom_file, 'ImagePositionPatient'):
            return dicom_file.ImagePositionPatient[2]
        elif hasattr(dicom_file, 'SliceLocation'):
            return dicom_file.SliceLocation
        else:
            raise TypeError #replace with custom error



class SortSlicesFilter(DicomFilter):

    def sort_tags(self, dicom_files) -> list:
        try:
            if isinstance(self.filter_arg, str):
                return [getattr(file, self.filter_arg) for file in dicom_files]
            elif isinstance(self.filter_arg, tuple):
                tag, ind = self.filter_arg
                return [getattr(file, tag)[ind] for file in dicom_files]
            else:
                raise TypeError("ERROR: [filter_arg] enter either string or dict type as arg")
        except TypeError as e:
                print(f'{e}')

    def filter_files(self, dicom_files):
        sorted_tags = self.sort_tags(dicom_files)
        return [x for (_,x) in sorted(zip(sorted_tags,dicom_files), key=lambda pair: pair[0])]



    
class RemoveSliceOverlapFilter(DicomFilter):
    """Remove DICOM files with dupliate slice locations."""

    def return_step_size(self, dicom_file) -> float:
        if hasattr(dicom_file, 'SpacingBetweenSlices'):
            return dicom_file.SpacingBetweenSlices
        elif hasattr(dicom_file, 'SliceThickness'):
            return dicom_file.SliceThickness
        else:
            raise TypeError #replace with custom error

    def return_step_sizes(self, dicom_files) -> List[float]:
        return [self.return_step_size(file) for file in dicom_files] 

    def return_position(self, dicom_file) -> float:
        if hasattr(dicom_file, 'ImagePositionPatient'):
            return dicom_file.ImagePositionPatient[2]
        elif hasattr(dicom_file, 'SliceLocation'):
            return dicom_file.SliceLocation
        else:
            raise TypeError #replace with custom error

    def return_positions(self, dicom_files: List[dcm.dataset.Dataset]) -> List[float]:
        return [self.return_position(file) for file in dicom_files]

    def approximate_best_locations(self, dicom_files) -> List[float]:
        average_step: float = np.mode(self.return_step_sizes(dicom_files))
        slice_positions = self.return_step_sizes(dicom_files)
        return range(np.amin(slice_positions), np.amax(slice_positions), average_step)

    
    def closest(lst, K):
        return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]


    def filter_files(self, dicom_files: List[dcm.dataset.Dataset]):
        best_locations: List[float] = self.approximate_best_locations(dicom_files)
        


        return [file for num, file in enumerate(dicom_files) if file.ImagePositionPatient[2] - dicom_files[num-1]]

        for dicom_file in dicom_files:
            

   scan_fix = [scan[0]]
            for file_num in range(1,len(scan)):
                if abs(scan[file_num].ImagePositionPatient[2] - scan[file_num-1].ImagePositionPatient[2]) > (0.5*scan[0].SliceThickness):
                    scan_fix.append(scan[file_num])
            scan = scan_fix.copy()

