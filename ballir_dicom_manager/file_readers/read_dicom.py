import pathlib
from typing import List

import numpy as np
import pydicom as dcm

from ballir_dicom_manager.file_viewers.array_viewer import ArrayViewer
from ballir_dicom_manager.file_readers.read_image_volume import ReadImageVolume
from ballir_dicom_manager.file_loaders.dicom_loader import DicomLoader
from ballir_dicom_manager.file_writers.dicom_writer import DicomWriter
from ballir_dicom_manager.preprocess.dicom_tag_parser import DicomSorter, DicomTagParser
from ballir_dicom_manager.preprocess.dicom_validator import DicomVolumeValidator
from ballir_dicom_manager.preprocess.fix_dicom_for_nifti import FixDicomForNifti


class ReadDicom(ReadImageVolume):

    loader = DicomLoader()
    sorter = DicomSorter()
    writer = DicomWriter()
    nifti_fixer = FixDicomForNifti(fill_missing_with_adjacent=False)

    def __init__(self, target_path: pathlib.Path, value_clip=False, allow: list = []):
        super().__init__(target_path)

        self.files = self.sorter.sort_dicom_files(self.files)
        self.validator = DicomVolumeValidator(allow)
        self.validator.validate(self.files)

        self.parser = DicomTagParser(allow)
        # self.modality = self.parser.get_consistent_tag(self.files, 'Modality')
        self.value_clip = value_clip  # self.configure_value_clip(value_clip)
        self.spacing = self.parser.get_dicom_spacing(self.files)

        self.set_arr()

    def convert_clip_range_to_hounsfield(
        self, value_clip: list, dicom_file: dcm.dataset.Dataset
    ) -> list:
        return [
            (val - dicom_file.RescaleIntercept) / dicom_file.RescaleSlope
            for val in value_clip
        ]

    def clip_pixel_array(
        self,
        dicom_files: List[dcm.dataset.Dataset],
        value_clip: dict,
        pixel_array: np.array,
    ) -> np.array:

        """Have to do slice by slice for instances where RescaleIntercept varies across volume."""
        for slice_num in range(pixel_array.shape[0]):
            if (
                "Modality" in dicom_files[slice_num]
                and dicom_files[slice_num].Modality in value_clip
            ):
                # print(self.value_clip)
                slice_value_clip = self.convert_clip_range_to_hounsfield(
                    value_clip[dicom_files[slice_num].Modality], dicom_files[slice_num]
                )
                # print(slice_value_clip)
                pixel_array[slice_num, ...] = np.clip(
                    pixel_array[slice_num, ...],
                    slice_value_clip[0],
                    slice_value_clip[1],
                )
        return pixel_array

    def set_arr(self) -> None:
        self.arr = np.array([file.pixel_array for file in self.files])
        if self.value_clip:
            self.arr = self.clip_pixel_array(self.files, self.value_clip, self.arr)
        self.arr = np.swapaxes(self.arr, 0, 2)
        print(np.amin(self.arr))
        print(np.amax(self.arr))
        self.viewer = ArrayViewer(self.arr, self.spacing)
        self.writer.write_array_volume_to_dicom(self.arr, self.files)

    def prep_for_nifti(self) -> None:
        self.files = self.nifti_fixer.validate_for_nifti(self.files)
        self.set_arr()
