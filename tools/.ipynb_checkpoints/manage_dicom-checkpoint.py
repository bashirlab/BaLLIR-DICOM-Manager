#standard imports
import pydicom as dcm
from glob import glob


#custom imports
from ..tools.shortcuts import *
from ..tools.ManageDicom import ManageDicom



## CLEAN DICOM


def saveDicoms(dicom_files, save_dir):
    
    for num, file in enumerate(dicom_files):
        save_loc = os.path.join(save_dir, str(num).zfill(4) + '.dcm')
        buildDir(save_dir)
        file.save_as(save_loc)
    
    return



def buildDCM():

    ds = dcm.dcmread('/DataMount/tmp.dcm')
    ds.PatientName = "Test^Firstname"
    ds.PatientID = "123456"
    ds.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1' #dcm.uid.ExplicitVRBigEndian
    ds.BitsAllocated = 16
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = 'MONOCHROME2'
    
    return ds

        
# FIX SLICE INCONSISTENCIES

def stepSizes(dicom_files):
    
    slice_locs = []
    for dicom_file in dicom_files:
        slice_locs.append(dicom_file.ImagePositionPatient[2])

    slice_steps = [slice_locs[num] - slice_locs[num+1] for num in range(len(slice_locs) -1)]; slice_steps_set = set(slice_steps); slice_steps_unq = list(slice_steps_set)
    slice_locs_set = set(slice_locs); slice_locs_unq = list(slice_locs_set) 
    
    return slice_steps, slice_steps_unq, slice_locs, slice_locs_unq





def resetSlices(dicom_files, slice_steps, slice_steps_unq):
    
    print('ERROR RESETTING SLICE POSITIONS')
    step_counts = []
    for step in slice_steps_unq:
        step_counts.append(slice_steps.count(step))
    step_size = slice_steps_unq[step_counts.index(max(step_counts))]
    
    slice_start = float(round(dicom_files[0].ImagePositionPatient[2],1))
    for num in range(1, len(dicom_files)):
        dicom_files[num].ImagePositionPatient[2] = float(round(slice_start + (num * step_size),1))
    
    return dicom_files


def removeDuplicates(dicom_files, slice_steps, slice_locs):
    
    print('ERROR: DUPLICATE SLICE LOCATIONS')
    slice_breaks = [0]
    for num in range(1, len(slice_steps)):
        if slice_steps[num] != slice_steps[num - 1]:
            if slice_breaks[-1] != (num):
                slice_breaks.append(num + 1)
    slice_breaks.append(len(slice_steps))
    section_sizes = []
    for i in range(1,len(slice_breaks)):
        section_sizes.append(slice_breaks[i] - slice_breaks[i-1])
    slice_max = section_sizes.index(max(section_sizes))
    list_max = [num for num in range(slice_breaks[slice_max], slice_breaks[slice_max+1])]
    for num in range(len(dicom_files) -1, -1, -1):
        if slice_locs.count(slice_locs[num]) > 1 and not num in list_max:
            del dicom_files[num]
        
    return dicom_files


def sortDicoms(dicom_files, reverse = True, sortby = ['ImagePositionPatient', 2]):
    
    #add alternate sorting methods
    
    if len(sortby) == 1:
        dicom_files = sorted(dicom_files, key=lambda s: getattr(s, sortby))
    elif len(sortby == 2):
        dicom_files = sorted(dicom_files, key=lambda s: getattr(s, sortby[0])[1])
    else:
        print('ERROR: wrong number of variables supplied to sortby arg')
    
    if reverse:
        dicom_files.reverse()
#     dicom_files = [x for _, x in sorted(zip(slice_locs, dicom_files))]
    
    return dicom_files


def fixDicoms(dicom_files):
    
    # round patient positions
    slice_steps, slice_steps_unq, slice_locs, slice_locs_unq = stepSizes(dicom_files)
    if len(slice_steps_unq) > 1:
        dicom_files = roundPositionPatient(dicom_files)
        
    # remove duplicate slice locations
    slice_steps, slice_steps_unq, slice_locs, slice_locs_unq = stepSizes(dicom_files)
    if len(slice_locs) > len(slice_locs_unq):
        dicom_files = removeDuplicates(dicom_files, slice_steps, slice_locs)
        
    # sort files
    slice_steps, slice_steps_unq, slice_locs, slice_locs_unq = stepSizes(dicom_files)
    #dicom_files = sortDicoms(dicom_files)
        
    # final fix --rewrte slice position with most common thickness
    if len(slice_locs) > len(slice_locs_unq):
        resetSlices(dicom_files, slice_steps, slice_steps_unq)
        
    return dicom_files


def getROIcoords(roi):

    # get index of ROI
    ind = int(roi['integer'][1])
    # get coordinate data of ROI
    x = roi['array']['dict']['array'][1]['string']
    # convert string coordinates to tuples
    coords = [literal_eval(coord) for coord in x]
    # parse out x and y and make closed loop
    x = [i[0] for i in coords] + [coords[0][0]]
    y = [i[1] for i in coords] + [coords[0][1]]
    # apply parametric spline interpolation
    tck, _ = interpolate.splprep([x,y], s=0, per=True)
    x, y = interpolate.splev(np.linspace(0,1,500), tck)
    
    
    return ind, x, y


# -- CONVERT XML to NUMPY

def xml2numpy(file_xml, loc_save = False, file_save = False, z_reversed = False):
    
    with open(file_xml, 'r') as f: 
        xml_data = xmltodict.parse(f.read())
    
    roi_list = xml_data['plist']['dict']['array']['dict']
    
    if float(roi_list[0]['array']['dict']['string'][0].split('(')[-1].split(')')[0].split(',')[2]) > float(roi_list[1]['array']['dict']['string'][0].split('(')[-1].split(')')[0].split(',')[2]):
        z_reversed = True
    else:
        z_reversed = False
    
    file_npy = np.zeros((int(roi_list[0]['integer'][0]), int(roi_list[0]['integer'][3]), int(roi_list[0]['integer'][2])))
    
    for roi in roi_list:
        ind, x, y = getROIcoords(roi)
        rr, cc = polygon(y, x)
        
        if z_reversed:
            file_npy[rr, cc, int(roi['integer'][1])] = 1.0
        else:
            file_npy[rr, cc, int(file_npy.shape[2] -1 - int(roi['integer'][1]))] = 1.0
        
    if file_save:
        if not loc_save:
            print('NUMPY SAVE LOCATION NOT PROVIDED')
        else:
            np.save(loc_save, file_save)
    
    return file_npy, flipCheck


# -- convert XML to DICOM

def xml2dicom(file_xml, template_dcm = False, dir_save = False, file_save = True, z_reversed = False, step_size = False):
    
    file_npy = xml2numpy(file_xml, file_save = False, z_reversed = z_reversed)
    file_npy = file_npy.astype('uint16')
    file_dcm = []
    
    if  file_save and dir_save:
        buildDIR(dir_save)
      
    for num_slice in range(file_npy.shape[2]):
        
        slice_dcm = buildDCM()
#         slice_dcm = copy.deepcopy(template_dcm)#buildDCM()
        slice_dcm.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'
        slice_dcm.Rows = file_npy.shape[0]
        slice_dcm.Columns = file_npy.shape[1]
        slice_dcm.InstanceNumber = num_slice
        slice_dcm.PixelSpacing = template_dcm.PixelSpacing
        slice_dcm.ImagePositionPatient[0] = template_dcm.ImagePositionPatient[0]
        slice_dcm.ImagePositionPatient[1] = template_dcm.ImagePositionPatient[1]
        slice_dcm.ImageOrientationPatient = [1, 0, 0, 0, 1, 0] #template_dcm.ImageOrientationPatient
        
        if template_dcm and step_size:
#             slice_dcm = copy.deepcopy(template_dcm)
            slice_dcm.ImagePositionPatient[2] = float(template_dcm.ImagePositionPatient[2] + (num_slice*step_size))
            slice_dcm.SliceThickness = template_dcm.SliceThickness
        else:
            print('ERROR: no template provided')
            slice_dcm.ImagePositionPatient[2] = -float(num_slice)
            slice_dcm.SliceThickness = 5.0
            
        
        slice_dcm.PixelData = file_npy[..., num_slice].tobytes()#np.ascontiguousarray(file_npy[..., num_slice])
        file_dcm.append(slice_dcm)
        
#         if not template_dcm:
#             slice_dcm['PixelData'].VR = 'OW'
            
#         file_dcm.append(slice_dcm)
        
        if file_save:
            if not dir_save:
                print('DICOM SAVE DIRECTORY NOT PROVIDED')
            else:
                loc_save = os.path.join(dir_save, str(num_slice).zfill(4) + '.dcm')
                slice_dcm.save_as(loc_save)
    
    return file_dcm


def saveDicoms(dicom_files, save_dir, overwrite = False):
    
    buildDir(save_dir, overwrite = overwrite)
    
    for num, file in enumerate(dicom_files):
        save_loc = os.path.join(save_dir, str(num).zfill(4) + '.dcm')
        file.save_as(save_loc)
    
    return


def findScanFlip(dicom_files):
    
    if dicom_files[1].ImagePositionPatient[2] > dicom_files[0].ImagePositionPatient[2]:
        flipCheck = True
    else:
        flipCheck = False
    
    return flipCheck


def filterDicoms(dicom_files, attr = ['SeriesNumber', 2]):
    
    #attr = [attribute name, filter value]
    
    dicom_filtered = [file for file in dicom_files if getattr(file, attr[0]) == attr[1]]
    
    return dicom_filtered


def prepDicoms(dicom_files):
    
    for num, file in enumerate(dicom_files):
        file.InstanceNumber = num
        file.Manufacturer = 'GE'# []
        file.Modality = 'MR'
        file.ImagePositionPatient[0] = dicom_files[0].ImagePositionPatient[0]
        file.ImagePositionPatient[1] = dicom_files[0].ImagePositionPatient[1]
        file.PixelSpacing = dicom_files[0].PixelSpacing
        file.ImageOrientationPatient = [float(round(orient,0)) for orient in file.ImageOrientationPatient]
        
    return dicom_files


def findMissingSlices(dir_mask):
    
    list_glob_masks = glob(os.path.join(dir_mask, '**/*.dcm'), recursive = True); list_glob_masks.sort()
    mask_array = np.array([dcm.dcmread(file).pixel_array for file in list_glob_masks])
    list_val = []
    for num in range(1, mask_array.shape[0]):
        if np.amax(mask_array[num-1, ...]) != np.amax(mask_array[num, ...]):
            list_val.append(num)

    if len(list_val) >2:
        missing_slice = True
    else:
        missing_slice = False
    
    return missing_slice, list_val


# add function for comparing dicom file tag values -- within the same case, series, between different cases etc.
