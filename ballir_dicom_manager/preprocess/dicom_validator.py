from ballir_dicom_manager.preprocess.dicom_tag_parser import DicomTagParser
from ballir_dicom_manager.preprocess.slice_manager import SliceManager

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

    def print_instance_count(self, dicom_files, tag: str) -> None:
        all_tags = self.get_all_tag(dicom_files, tag)
        print({tag: all_tags.count(tag) for tag in all_tags})

    def print_instance_count_idx(self, dicom_files, tag: str, idx: int) -> None:
        all_tags = self.get_all_tag_idx(dicom_files, tag, idx)
        print({tag: all_tags.count(tag) for tag in all_tags})

    def validate(self, dicom_files):
        if not 'SeriesNumber' in self.allow:
            assert self.check_tag_consistent(dicom_files, 'SeriesNumber'), f'mulitple SeriesNumber values found: {self.get_all_tag_unique(dicom_files, "SeriesNumber")}'
        if not 'PixelSpacing' in self.allow:
            assert self.check_tag_consistent_idx(dicom_files, 'PixelSpacing', 0), f'PixelSpacing in Y-dim inconsistent: {self.print_instance_count_idx(dicom_files, "PixelSpacing", 0)}'
            assert self.check_tag_consistent_idx(dicom_files, 'PixelSpacing', 1), f'PixelSpacing in X-dim inconsistent: {self.print_instance_count_idx(dicom_files, "PixelSpacing", 1)}'
        if not 'ImagePositionPatient' in self.allow:
            assert self.check_tag_consistent_idx(dicom_files, 'ImagePositionPatient', 0), f'ImagePositionPatient in Y-dim inconsistent: {self.print_instance_count_idx(dicom_files, "ImagePositionPatient", 0)}'
            assert self.check_tag_consistent_idx(dicom_files, 'ImagePositionPatient', 0), f'ImagePositionPatient in X-dim inconsistent: {self.print_instance_count_idx(dicom_files, "ImagePositionPatient", 0)}'
            assert self.check_tag_unique_idx(dicom_files, 'ImagePositionPatient', 2), f'ImagePositionPatient Z position is non-unique: {self.print_instance_count_idx(dicom_files, "ImagePositionPatient", 2)}'
        if not 'SpacingBetweenSlices' in self.allow:
            assert self.check_tag_consistent(dicom_files, 'SpacingBetweenSlices'), f'SpacingBetweenSlices is non-unique: {self.print_instance_count(dicom_files, "SpacingBetweenSlices")}'
        if not 'Modality' in self.allow:
            assert self.check_tag_consistent(dicom_files, 'Modality'), f'Modality is non-unique: {self.print_instance_count(dicom_files, "SpacingBetweenSlices")}'
        if not 'RescaleIntercept' in self.allow:
            assert self.check_tag_consistent(dicom_files, 'RescaleIntercept'), f'RescaleIntercept is non-unique: {self.print_instance_count(dicom_files, "SpacingBetweenSlices")}'