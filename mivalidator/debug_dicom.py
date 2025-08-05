
import os
import pydicom

file_path = '/app/uploads/MRI_CHEST_1.2.826.0.1.3680043.8.498.28705623287650840537270826504560346716/1.2.826.0.1.3680043.8.498.66696762928089512893121922737985917240/1.2.826.0.1.3680043.8.498.91718219329719214929577226386540417487.dcm'

print(f'os.path.exists: {os.path.exists(file_path)}')

try:
    with open(file_path, 'rb') as f:
        print('File opened successfully with open()')
    ds = pydicom.dcmread(file_path)
    print('DICOM read successfully with pydicom.dcmread()')
except Exception as e:
    print(f'Error: {e}')
