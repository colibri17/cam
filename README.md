This Python library allows you to automatically record ip-cam videos on your Google Drive storage. 
You are allowed to record videos from an arbitrary number of cams you might have installed on your local network. 
The records are performed on the RSTP protocol.

# Configuration

### Install the cams
The first step is to have installed the ip-cams you want to use on your local network.
Depending on the cam, you might need to perform different operations. Please follow
your cam vendor's instruction to install your cams.  
After installing, you should be able to access to your cam connecting to the local ip address on the port RSTP.
For example, if you have installed your cam at IP 192.168.1.44 on port 554 (the usual port used for 
handling RSTP connection), you should be able to open your browser and connect your cam
when inserting 192.168.1.44:554 on the search bar.

### Set up Google Drive API access
The second step is to allow the program to interact with the Google Drive API. 
In order to do that, you need to have a valid Google Cloud account. Then, you need
to create a new project and set up the credentials. Finally you can enable the Google Drive API on the project.
* to create a project: [here](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
* To set up the credentials: [here](https://cloud.google.com/iam/docs/creating-managing-service-account-keys). When you are setting up the service account,
you are required to download a json file containing the private key which allows to connect to the google cloud project.
The downloaded json must be named *credentials.json* and be placed in the path *./configs/credentials/credentials.json*.
* To enable the Google Drive API: [here](https://developers.google.com/drive/api/v3/enable-drive-api)

### Create storage folders on Google Drive
Next, you need to create the folders you want to store data on Google Drive. To do that, it is enough 
to connect to [google drive](https://drive.google.com/drive/my-drive) and create the folders you want 
to use to store your recorded videos. You might want to create a different folder for each cam you want 
to record from. When creating the folder, take note of the folder id. This can be retrieved by looking at the 
last part of the url you see when entering in the google drive folder. For example, in the following url
```
https://drive.google.com/drive/folders/78643Yd_YjwDoFnPIbzdI82ACT0K
```
the folder id is `78643Yd_YjwDoFnPIbzdI82ACT0K`

### Configure the cam details
You need to tell the application which is the local ip address used by the cams, the RSTP port, the password and username
which can be used to connect to the cam. You need to create a json file storing this information on the
path *./configs/cams*. Each cam has to have its json file saved in this path. The name of the json file is not important.
The json file has to have the following structure:
```
{
  "name": "30",
  "url": "192.168.1.30",
  "port": "554",
  "user": "admin_12345",
  "pwd": "54321",
  "folder_id": "123DvMivY_jUDoIUYNRPOLKQQbDQ"
}
```
This will tell to the program that there is a cam which we name 30 on the url 192.168.1.30 and port 554. To access the cam
the user is *admin_12345* and the password is *54321*. The videos should be saved on the google drive folder having id
*123DvMivY_jUDoIUYNRPOLKQQbDQ*

# Set up parameters
The application can be customed according to different parameters. These can all be specified by modifying the YAML 
file contained in the path *config/confs.yaml*. The following is a list of the parameters which can be changed, reported
with their default values:
* check_bdw = False: this specifies if the application should turn-off when the internet bandwidth is not large enough. 
By default, when the cam is recording this option is disabled. Set true to enable it.