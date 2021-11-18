from abc import ABC, abstractmethod
from typing import List

import pydicom as dcm


class DicomFilter(ABC):
    def __init__(self, filter_arg) -> None:
        pass

    @abstractmethod
    def filter_files(self, dicom_files: List[dcm.dataset.Dataset]) -> List[dcm.dataset.Dataset]:
        """Sort or filter DICOM files."""


class SortSlicesFilter(DicomFilter):

    def sort_tags(self, dicom_files) -> list:
        try:
            if isinstance(self.filter_arg, str):
                return [getattr(file, self.filter_arg) for file in dicom_files]
            elif isinstance(self.filter_arg, dict):
                (tag, ind), = self.filter_arg.items()
                return [getattr(file, tag)[ind] for file in dicom_files]
            else:
                raise TypeError("ERROR: [filter_arg] enter either string or dict type as arg")
        except TypeError as e:
                print(f'{e}')

    def filter_files(self, dicom_files):
        sorted_tags = self.sort_tags(dicom_files)
        return [x for (_,x) in sorted(zip(sorted_tags,dicom_files), key=lambda pair: pair[0])]

    
class RemoveDuplicatesFilter(DicomFilter):
    """Remove DICOM files with dupliate slice locations."""
   

    # get all SpacingBetweenSlices (or SliceThickness)
    # get all slice locations, get mean/median? get min/max
    # approximate best locations 

    def get_slice_step(ls
    )

    def list_best_slices(self, dicom_files) -> List[float]:
        

    def return_all_values(self, dicom_files: List[dcm.dataset.Dataset], attr: str) -> list:
        return [file.ImagePositionPatient[2] for file in dicom_files]


    def filter_files(self, dicom_files: List[dcm.dataset.Dataset]):
        return [file for num, file in enumerate(dicom_files) if file.ImagePositionPatient[2] - dicom_files[num-1]]

        for dicom_file in dicom_files:
            

   scan_fix = [scan[0]]
            for file_num in range(1,len(scan)):
                if abs(scan[file_num].ImagePositionPatient[2] - scan[file_num-1].ImagePositionPatient[2]) > (0.5*scan[0].SliceThickness):
                    scan_fix.append(scan[file_num])
            scan = scan_fix.copy()

