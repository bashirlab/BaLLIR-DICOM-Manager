from typing import Tuple

import nibabel as nib
import numpy as np


def clip_values(nifti_file: nib.nifti1.Nifti1Image, clip_range:Tuple[float, float]) -> nib.nifti1.Nifti1Image:
    """Clip voxel values of NIFTI pixel array."""
    clipped_arr = np.clip(nifti_file.get_fdata(), min(clip_range), max(clip_range))
    return nib.Nifti1Image(clipped_arr, nifti_file.affine, nifti_file.header)