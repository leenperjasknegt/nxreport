import requests
from PIL import Image
from io import BytesIO
from datetime import datetime
import base64
import os

# Variables to change
ip_address = "localhost"
login = "admin"
password = "Jasfien007@"

# Function to fetch camera IDs and names
def get_camera_ids_and_names():
    try:
        print("Fetching camera IDs and names...")
        url = f"https://{ip_address}:7001/ec2/getCamerasEx"
        response = requests.get(url, auth=(login, password), verify=False)
        response.raise_for_status()
        data = response.json()
        
        camera_info = [(camera_data["id"], camera_data.get("name", "")) for camera_data in data]
        print("Camera IDs and names fetched successfully.")
        return camera_info
    except requests.RequestException as e:
        print(f"Error fetching camera IDs and names: {e}")
        return []

# Function to check camera diagnostics
def check_camera_diagnostics(camera_id):
    try:
        print(f"Checking camera diagnostics for ID: {camera_id}...")
        url = f"https://{ip_address}:7001/api/doCameraDiagnosticsStep?cameraId={camera_id}&type=mediaStreamAvailability"
        response = requests.get(url, auth=(login, password), verify=False)
        response.raise_for_status()
        data = response.json()
        
        error_code = data.get("reply", {}).get("errorCode", None)
        status = "OK" if error_code == 0 else "Error"
        
        print(f"Camera ID: {camera_id} - Status: {status}")
        return error_code == 0, status
    except requests.RequestException as e:
        print(f"Error checking camera diagnostics for ID {camera_id}: {e}")
        return False, "Unknown"

# Function to download thumbnail for a camera
def download_thumbnail(camera_id):
    try:
        print(f"Downloading thumbnail for camera ID: {camera_id}...")
        url = f"https://{ip_address}:7001/ec2/cameraThumbnail?cameraId={camera_id}"
        response = requests.get(url, auth=(login, password), verify=False)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type')
        if 'image' in content_type:
            image = Image.open(BytesIO(response.content))
            print(f"Thumbnail downloaded for camera ID: {camera_id}")
            return image
        else:
            print(f"Content for camera ID {camera_id} is not an image.")
            return None
    except requests.RequestException as e:
        print(f"Error downloading thumbnail for camera ID {camera_id}: {e}")
        return None
    except Exception as ex:
        print(f"An error occurred while processing thumbnail for camera ID {camera_id}: {ex}")
        return None

# Function to check server storage status
def check_storage_status():
    try:
        print("Checking server storage...")
        url = f"https://{ip_address}:7001/rest/v2/servers/this/storages/*/status"
        response = requests.get(url, auth=(login, password), verify=False)
        response.raise_for_status()
        data = response.json()
        
        error_count = 0  # Counter for storage status errors
        for storage in data:
            storage_status = storage.get("storageStatus", "")
            if "used|dbReady" not in storage_status:
                print(f"Error in storage status for storage ID {storage.get('storageId')}: {storage_status}")
                error_count += 1
        
        storage_status = "OK" if error_count == 0 else "Error"
        print(f"Server storage status: {storage_status}")
        return storage_status
    except requests.RequestException as e:
        print(f"Error checking server storage: {e}")
        return "Error"

# Function to convert image to base64
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# Fetch camera IDs and names
camera_info = get_camera_ids_and_names()
# Sort the camera_info list by camera name
camera_info.sort(key=lambda x: x[1].lower())

# Fetch camera IDs and names
camera_info = get_camera_ids_and_names()
# Initialize dictionary to store camera statuses
camera_statuses = {}

# Check the status for each camera
for camera_id, _ in camera_info:
    success, status = check_camera_diagnostics(camera_id)
    camera_statuses[camera_id] = status

# Now you can use camera_statuses to count OK and Error cameras
# ...
# Calculate the count of cameras with errors
camera_error_count = sum(1 for status in camera_statuses.values() if status == "Error")
# Calculate the count of cameras without errors
camera_ok_count = len(camera_statuses) - camera_error_count
# ...

# Generate HTML report
html_report = f"""<html>
<head>
    <title>Camera server report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
            background-color: #f4f4f4;
            color: #333;
        }}
        h1, h2, p {{
            margin: 0;
            padding: 0;
        }}
        h1 {{
            color: #009688;
            margin-bottom: 15px;
        }}
        h2 {{
            color: #3f51b5;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        p {{
            margin-bottom: 5px;
        }}
        img {{
            max-width: 300px;
            height: auto;
            border: 1px solid #ccc;
            margin-top: 10px;
        }}
        .status {{
            margin-left: 0;
            font-size: 0.9em;
        }}
        .separator {{
            margin-top: 20px;
            border-top: 1px solid #ccc;
            border-bottom: 1px solid #ccc;
        }}
        .generated-text {{
            font-size: 0.8em;
        }}
        /* Modified styles for OK and Error statuses */
        .status-ok {{
            margin-left: 0;
            font-size: 0.9em;
            color: green;
        }}
        .status-error {{
            margin-left: 0;
            font-size: 0.9em;
            color: red;
        }}
    </style>
</head>
<body>
<h1>Server Report</h1>
<p class='generated-text'>Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<div class='separator'></div>
"""


# Check server storage status
storage_status = check_storage_status()
# Modify the HTML to apply the classes based on status
error_count = storage_status.count("Error")
ok_count = len(camera_info) - error_count
status_class = "status-error" if error_count > 0 else "status-ok"
html_report += f"<h2>Server Storage Status: <span class='{status_class}'>{storage_status}</span></h2>"


# Check the camera status and display the count
camera_error_count = sum(1 for _, status in camera_statuses.items() if status == "Error")
camera_ok_count = len(camera_statuses) - camera_error_count
camera_status_class = "status-error" if camera_error_count > 0 else "status-ok"
camera_status_text = f"Camera Errors: {camera_error_count}"
html_report += f"<p class='generated-text {camera_status_class}'>{camera_status_text}</p>"
html_report += f"<div class='separator'></div>"




# Folder to save reports
reports_folder = "reports"
os.makedirs(reports_folder, exist_ok=True)  # Create the folder if it doesn't exist

# Fetch camera IDs and names
camera_info = get_camera_ids_and_names()
# Sort the camera_info list by camera name
camera_info.sort(key=lambda x: x[1].lower())

for idx, (camera_id, camera_name) in enumerate(camera_info):
    if idx != 0:
        html_report += f"<div class='separator'></div>"
    
    html_report += f"<h2>Camera: {camera_name}</h2>"
    html_report += f"<p>ID: {camera_id[1:-1]}</p>"
    
    success, status = check_camera_diagnostics(camera_id)
    
    # Modify the HTML to apply the classes based on status
    status_class = "status-ok" if success else "status-error"
    html_report += f"<p class='{status_class}'>Status: {status}</p>"
    
    thumbnail = download_thumbnail(camera_id)
    if thumbnail:
        # Convert image to base64
        img_data = image_to_base64(thumbnail)
        html_report += f"<p><img src='data:image/jpeg;base64,{img_data}' /></p>"

# Write HTML report to a file within the 'reports' folder with date and time
report_filename = f"{reports_folder}/camera_server_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.html"
with open(report_filename, "w") as file:
    file.write(html_report)

print("Report generated successfully.") 
