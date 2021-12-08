import logging

from ballir_dicom_manager.preprocess.dicom_tag_parser import DicomTagParser
from ballir_dicom_manager.preprocess.slice_manager import SliceManager

log = logging.getLogger(__name__)

class DicomVolumeValidator(DicomTagParser):
    
    slice_manager = SliceManager()
    
    def __init__(self, allow: list):
        self.allow = allow
    
    def check_tag_consistent(self, dicom_files, tag: str) -> bool:
        return len(self.get_all_tag_unique(dicom_files, tag)) <= 1

    def check_tag_consistent_idx(self, dicom_files, tag: str, idx: int) -> bool:
        return len(self.get_all_tag_unique_idx(dicom_files, tag, idx)) <= 1

    def check_tag_unique(self, dicom_files, tag: str) -> bool:
        return len(self.get_all_tag_unique(dicom_files, tag)) == len(self.get_all_tag(dicom_files, tag))

    def check_tag_unique_idx(self, dicom_files, tag: str, idx: int) -> bool:
        return len(self.get_all_tag_unique_idx(dicom_files, tag, idx)) == len(self.get_all_tag(dicom_files, tag))

    def get_instance_count(self, dicom_files, tag: str) -> dict:
        all_tags = self.get_all_tag(dicom_files, tag)
        return {tag: all_tags.count(tag) for tag in all_tags}

    def get_instance_count_idx(self, dicom_files, tag: str, idx: int) -> dict:
        all_tags = self.get_all_tag_idx(dicom_files, tag, idx)
        return {tag: all_tags.count(tag) for tag in all_tags}

    def handle_failure(self, tag: str, warning_message: str) -> None:
        log.warning(warning_message)
        if not tag in self.allow:
            assert False, warning_message

    def validate(self, dicom_files) -> None:

        if not self.check_tag_consistent(dicom_files, 'SeriesNumber'):
            warning_message = f'mulitple SeriesNumber values found: {self.get_all_tag_unique(dicom_files, "SeriesNumber")}'
            self.handle_failure('SeriesNumber', warning_message)

        if not self.check_tag_consistent_idx(dicom_files, 'PixelSpacing', 0):
            warning_message = f'PixelSpacing in Y-dim inconsistent: {self.get_instance_count_idx(dicom_files, "PixelSpacing", 0)}'
            self.handle_failure('PixelSpacing', warning_message)

        if not self.check_tag_consistent_idx(dicom_files, 'PixelSpacing', 1):
            warning_message = f'PixelSpacing in X-dim inconsistent: {self.get_instance_count_idx(dicom_files, "PixelSpacing", 1)}'
            self.handle_failure('PixelSpacing', warning_message)

        if not self.check_tag_consistent_idx(dicom_files, 'ImagePositionPatient', 0):
            warning_message = f'ImagePositionPatient in Y-dim inconsistent: {self.get_instance_count_idx(dicom_files, "ImagePositionPatient", 0)}'
            self.handle_failure('ImagePositionPatient', warning_message)

        if not self.check_tag_consistent_idx(dicom_files, 'ImagePositionPatient', 1):
            warning_message = f'ImagePositionPatient in X-dim inconsistent: {self.get_instance_count_idx(dicom_files, "ImagePositionPatient", 1)}'
            self.handle_failure('ImagePositionPatient', warning_message)

        if not self.check_tag_unique_idx(dicom_files, 'ImagePositionPatient', 2):
            warning_message = f'ImagePositionPatient Z position is non-unique: {self.get_instance_count_idx(dicom_files, "ImagePositionPatient", 2)}'
            self.handle_failure('ImagePositionPatient', warning_message)

        if not self.check_tag_consistent(dicom_files, 'SpacingBetweenSlices'):
            warning_message = f'SpacingBetweenSlices is non-unique: {self.get_instance_count(dicom_files, "SpacingBetweenSlices")}'
            self.handle_failure('SpacingBetweenSlices', warning_message)

        if not self.check_tag_consistent(dicom_files, 'Modality'):
            warning_message = f'Modality is non-unique: {self.get_instance_count(dicom_files, "SpacingBetweenSlices")}'
            self.handle_failure('Modality', warning_message)

        if not self.check_tag_consistent(dicom_files, 'RescaleIntercept'):
            warning_message = f'RescaleIntercept is non-unique: {self.get_instance_count(dicom_files, "RescaleIntercept")}'
            self.handle_failure('RescaleIntercept', warning_message)