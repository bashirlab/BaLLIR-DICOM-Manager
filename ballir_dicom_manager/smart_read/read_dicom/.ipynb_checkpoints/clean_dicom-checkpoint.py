
# FIX SLICE INCONSISTENCIES

def stepSizes(dicom_files):
    
    slice_locs = []
    for dicom_file in dicom_files:
        slice_locs.append(dicom_file.ImagePositionPatient[2])

    slice_steps = [float(round(slice_locs[num+1] - slice_locs[num])) for num in range(len(slice_locs) -1)]; slice_steps_set = set(slice_steps); slice_steps_unq = list(slice_steps_set)
    slice_locs_set = set(slice_locs); slice_locs_unq = list(slice_locs_set) 
    
    return slice_steps, slice_steps_unq, slice_locs, slice_locs_unq





def resetSlices(dicom_files, slice_steps, slice_steps_unq):
    
    print('ERROR RESETTING SLICE POSITIONS')
    step_counts = []
    for step in slice_steps_unq:
        step_counts.append(slice_steps.count(step))
    step_size = slice_steps_unq[step_counts.index(max(step_counts))]
    print('STEP SIZE: ', step_size)
    print('SLICE STEPS: ', slice_steps)
    print('SLICE STEPS UNIQUE: ', slice_steps_unq)
    slice_start = float(round(dicom_files[0].ImagePositionPatient[2],1))
    print('SLICE START: ', slice_start)
    for num in range(1, len(dicom_files)):
        dicom_files[num].ImagePositionPatient[2] = float(round(slice_start + (num * step_size),1))
    
    return dicom_files


def removeDuplicates(dicom_files, slice_steps, slice_locs):
    
    print('ERROR: DUPLICATE SLICE LOCATIONS')
    slice_breaks = [0]
    for num in range(1, len(slice_steps)):
        if slice_steps[num
                      ] != slice_steps[num - 1]:
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


def sortDicoms(dicom_files):
    
    print('SORTING DICOM FILES')
    dicom_files = sorted(dicom_files, key=lambda s: s.ImagePositionPatient[2])
    dicom_files.reverse()
#     dicom_files = [x for _, x in sorted(zip(slice_locs, dicom_files))]
    
    return dicom_files


def fixDicoms(dicom_files):
    
    # round patient positions
    slice_steps, slice_steps_unq, slice_locs, slice_locs_unq = stepSizes(dicom_files)
    print(slice_locs_unq)
    #if len(slice_steps_unq) > 1:
    dicom_files = roundPositionPatient(dicom_files)
    
        
    # remove duplicate slice locations
    slice_steps, slice_steps_unq, slice_locs, slice_locs_unq = stepSizes(dicom_files)
    print(slice_locs_unq)
    if len(slice_locs) > len(slice_locs_unq):
        print('DUPLICATES')
        dicom_files = removeDuplicates(dicom_files, slice_steps, slice_locs)
        
    # sort files
    slice_steps, slice_steps_unq, slice_locs, slice_locs_unq = stepSizes(dicom_files)
#     dicom_files = sortDicoms(dicom_files)

    # final fix --rewrte slice position with most common thickness
    if len(slice_steps_unq) > 1:
        print('SLICE FIX')
        resetSlices(dicom_files, slice_steps, slice_steps_unq)
        
    return dicom_files