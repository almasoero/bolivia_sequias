__author__ = 'lauro'

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os


product_dir = "/home/sequia/drought/products/RDI/"

gauth = GoogleAuth()
#gauth.LocalWebserverAuth() # Creates local webserver and auto handles authentication.
gauth.CommandLineAuth()
drive = GoogleDrive(gauth)

#file1 = drive.CreateFile({'title': 'Hello.txt'})  # Create GoogleDriveFile instance with title 'Hello.txt'.
#file1.SetContentString('Hello World!') # Set content of the file from given string.
#file1.Upload()

file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

for file1 in file_list:
	print (file1['title'])
	if file1['title'] == 'NDWI-Poopo':
		folder_id = file1['id']

#get every file in 'folder'

file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(folder_id)}).GetList()

#download every file in 'folder'

for i, file1 in enumerate(sorted(file_list, key = lambda x: x['title']), start=1):

	filename = file1['title']
	date = filename.split("_")[1].split(".")[0]
	print(date)
	yy = date[0:4]
	mm = date[4:6]
	dd = date[6:8]
	dest_dir = os.path.join(product_dir,yy,mm,dd)
	filename2 = filename.split(".")[0]+ "000000.tif"

	if not os.path.exists(os.path.join(dest_dir,filename2)):
		print ("File does not exist: "+os.path.join(dest_dir,filename2))
		print('Downloading {} from GDrive ({}/{})'.format(file1['title'], i, len(file_list)))
		file1.GetContentFile(file1['title'])
		os.system ("mkdir -p "+dest_dir)
		os.system ("mv "+filename+" "+os.path.join(dest_dir,filename2))
	else:
		print ("File already exists: "+os.path.join(dest_dir,filename2))
 