import nibabel as nib
import pydicom as dcm
import copy
import numpy as np
import os



# -- CONVERT XML to NUMPY

def xml2numpy(file_xml, loc_save = False, file_save = True):
    
    with open(file_xml, 'r') as f: 
        xml_data = xmltodict.parse(f.read())
    
    roi_list = xml_data['plist']['dict']['array']['dict']
    file_npy = np.zeros((int(roi_list[0]['integer'][0]), int(roi_list[0]['integer'][3]), int(roi_list[0]['integer'][2])))
    
    for roi in roi_list:
        ind, x, y = getROIcoords(roi)
        rr, cc = polygon(y, x)
        file_npy[rr, cc, int(roi['integer'][1])] = 1.0
        
    if file_save:
        if not loc_save:
            print('NUMPY SAVE LOCATION NOT PROVIDED')
        else:
            np.save(loc_save, file_save)
    
    return file_npy

# -- convert XML to DICOM

def xml2dicom(file_xml, template_dcm = False, dir_save = False, file_save = True):
    
    file_npy = xml2numpy(file_xml, file_save = False)
    file_npy = file_npy.astype('uint16')
    print('npy shape: ', file_npy.shape)
    file_dcm = []
    
    if  file_save and dir_save:
        buildDIR(dir_save)
        
    
        
    for num_slice in range(file_npy.shape[2]):
        
        slice_dcm = buildDCM()
        #slice_dcm = copy.deepcopy(template_dcm)#buildDCM()
        slice_dcm.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'
        #print('slicenum1: ', slice_dcm.pixel_array.shape)
        slice_dcm.Rows = file_npy.shape[0]
        slice_dcm.Columns = file_npy.shape[1]
        slice_dcm.InstanceNumber = num_slice
        
        if template_dcm:
#             slice_dcm = copy.deepcopy(template_dcm)
            slice_dcm.ImagePositionPatient[2] = float(template_dcm.ImagePositionPatient[2] - (num_slice*template_dcm.SliceThickness))
            slice_dcm.SliceThickness = template_dcm.SliceThickness
        else:
            slice_dcm.ImagePositionPatient[2] = -float(num_slice)
            slice_dcm.SliceThickness = 5.0
            
        
        slice_dcm.PixelData = file_npy[..., num_slice].tobytes()#np.ascontiguousarray(file_npy[..., num_slice])
        file_dcm.append(slice_dcm)
        
        if not template_dcm:
            slice_dcm['PixelData'].VR = 'OW'
            
        file_dcm.append(slice_dcm)
        
        if file_save:
            if not dir_save:
                print('DICOM SAVE DIRECTORY NOT PROVIDED')
            else:
                loc_save = os.path.join(dir_save, str(num_slice).zfill(4) + '.dcm')
                slice_dcm.save_as(loc_save)
    
    return file_dcm



# -- convert XML to NIB

def xml2nifti(file_xml, loc_save = False, file_save = True):
    
#     file_npy = xml2numpy(file_xml, file_save = False)
#     xml2dicom(file_xml, loc_save = False, file_save = False)
    
    
    return file_nib


# -- convert NIB to NUMPY

def nifti2numpy(file_nifti, loc_save = False, file_save = True, meta_json = ['']):
    
    file_npy = file_nifti.get_fdata()
    
    if  file_save and dir_save:
        buildDIR(dir_save)
        
    
    
#     file_npy = xml2numpy(file_xml, file_save = False)
#     xml2dicom(file_xml, loc_save = False, file_save = False)
    
    
    return file_nib


## -- NIB to DICOM

def nifti2dicom(nib_loc, template_dcm, dir_save):
    
    if not os.path.exists(dir_save): os.makedirs(dir_save)
    nib_file = nib.load(nib_loc)
    nib_data = np.array(nib_file.get_fdata()).astype('uint16')#np.array(nib_file.get_fdata())
    #print('RANGE-- ', np.amin(nib_data), ' : ', np.amax(nib_data))
    #nib_data += 
    
#     print('nibshape: ', nib_data.shape)
    
    for num_slice in range(nib_data.shape[2]-1,-1,-1):
        
        #slice_dcm = buildDCM()
        slice_dcm = copy.deepcopy(template_dcm)
        slice_dcm.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'
        slice_dcm.Rows = nib_data.shape[0]
        slice_dcm.Columns = nib_data.shape[1]
        slice_dcm.InstanceNumber = num_slice

        slice_dcm.ImagePositionPatient[2] = float(template_dcm.ImagePositionPatient[2] + (nib_data.shape[2]-1-num_slice*template_dcm.SliceThickness))
        slice_dcm.SliceLocation = float(template_dcm.ImagePositionPatient[2] + (nib_data.shape[2]-1-num_slice*template_dcm.SliceThickness))
        
        slice_dcm.BitsAllocated = 16                  
        slice_dcm.BitsStored = 16                       
        slice_dcm.HighBit = 15                            
        slice_dcm.PixelRepresentation = 1     
        slice_dcm.Rows = nib_data.shape[1]
        slice_dcm.Columns = nib_data.shape[0]
        if hasattr(slice_dcm, 'SmallestImagePixelValue'):
            delattr(slice_dcm, 'SmallestImagePixelValue')
        if hasattr(slice_dcm, 'LargestImagePixelValue'):
            delattr(slice_dcm, 'LargestImagePixelValue')
#         slice_dcm.SmallestImagePixelValue = np.amin(nib_data)          
#         slice_dcm.LargestImagePixelValue = np.amax(nib_data)           
    

        slice_dcm.PixelData = np.rot90(nib_data[..., nib_data.shape[2] - num_slice - 1]).tobytes()
#         slice_dcm['PixelData'].VR = 'OW'
#         slice_dcm.PixelData = np.rot90(nib_data[..., num_slice]).tobytes()
        
        loc_save = os.path.join(dir_save, str(num_slice).zfill(4) + '.dcm')
        slice_dcm.save_as(loc_save)
    

    return



# -- convert DICOM to NUMPY + JSON

def dicom2numpy(file_xml, loc_save = False, file_save = True):
    
#     file_npy = xml2numpy(file_xml, file_save = False)
#     xml2dicom(file_xml, loc_save = False, file_save = False)
    
    
    return file_nib
