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

Warning! The integration tests run real workflow executions in your autoretouch account which will cost money.

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

Or more convenient:

```python
from autoretouch_api_client.authenticated_client import authenticate_device_and_get_client

client = authenticate_device_and_get_client()
```

There is also a basic implementation of credential storage.
The credentials are stored in a JSON file, this may or may not be sufficient for your security requirements.
Use it with caution.

```python
from autoretouch_api_client.authenticated_client import AutoretouchClientAuthenticatedPersistent

refresh_token = authenticate_device_and_get_refresh_token()
client = AutoretouchClientAuthenticatedPersistent(
        credentials_path="path/to/credentials/file.json", refresh_token=refresh_token)
```

Or more convenient:

```python
from autoretouch_api_client.authenticated_client import authenticate_device_and_get_client_with_persistence

client = authenticate_device_and_get_client_with_persistence("path/to/credentials/file.json")
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

input_image_content_hash = client.upload_image( 
        organization_id=organization_id,
        filepath="input_image.jpg")

workflow_execution_id = client.create_workflow_execution_for_image_reference(
        workflow_id=workflow_id, 
        organization_id=organization_id, 
        image_content_hash=input_image_content_hash, 
        image_name="input_image.jpg", 
        mimetype="image/jpeg", 
        labels={"myLabel": "myValue"})

workflow_execution_status = client.get_workflow_execution_details(
        organization_id=organization_id, 
        workflow_execution_id=workflow_execution_id
).status

if workflow_execution_status == "COMPLETED":    
    result_image_bytes = client.download_workflow_execution_result_blocking( 
            organization_id=organization_id,
            workflow_execution_id=workflow_execution_id)
    
    with open("result_image.jpg", "wb") as f:
        f.write(result_image_bytes)

```
