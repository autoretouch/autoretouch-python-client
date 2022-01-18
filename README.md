# autoretouch Python Client

API documentation: https://docs.api.autoretouch.com


## Installation 

```shell script
python3 -m venv venv 
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
```

## Tests
```shell script
pip install -r requirements-test.txt
python -m unittest discover test
```

## Authentication

Create a device connection in the autoretouch app at https://app.autoretouch.com/profile > API Information and copy the refresh token. 
Store it securely, e.g. in an environment variable or your keychain.

```python
import os
from autoretouch_api_client.authenticated_client import AutoretouchClientAuthenticated

refresh_token = os.getenv('AUTORETOUCH_REFRESH_TOKEN')
client = AutoretouchClientAuthenticated(refresh_token)
```

If you want to create the device connection within your application without using the autoretouch app:

```python
from autoretouch_api_client.authenticated_client import AutoretouchClientAuthenticated
from autoretouch_api_client.device_authentication import authenticate_device_and_get_refresh_token

refresh_token = authenticate_device_and_get_refresh_token()
client = AutoretouchClientAuthenticated(refresh_token)
```

## Usage

Usually, you are using the autoretouch API within the scope of an organization.
To get the organization id you need to refer: https://app.autoretouch.com/organization > Copy Organization ID.

To refer to a workflow, retrieve the workflow id at: https://app.autoretouch.com/workflows > ⋮ > Workflow API Information > id.

Example to upload an image and process it through a workflow: 

```python
# ...
organization_id = "e722e62e-5b2e-48e1-8638-25890e7279e3"
workflow_id = "26740cd0-3a04-4329-8ba2-e0d6de5a4aaf"

input_image_content_hash = client.upload_image(organization_id, "input_image.jpg")
workflow_execution_id = client.create_workflow_execution_for_image_reference(
        workflow_id, organization_id, input_image_content_hash, "input_image.jpeg", "image/jpeg", {"myLabel": "myValue"})
result_image_bytes = client.download_workflow_execution_result_blocking(organization_id, workflow_execution_id)
with open("result_image.jpg", "wb") as f:
    f.write(result_image_bytes)
```
