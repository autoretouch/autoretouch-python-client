# autoretouch Python Client

Work in Progress Python client implementation for the most important public API endpoints for https://www.autoretouch.com.

API documentation: https://docs.api.autoretouch.com


## Installation 

```shell script
python3 -m venv venv 
source venv/bin/activate
pip install -r requirements.txt
```

## Authentication

### Prerequisites

You need a free account at https://app.autoretouch.com.

### Authenticate with Refresh Token

### Authenticate with Device Connection

### Credential Storage

## Usage

This package exposes a single class `AutoretouchClient` allowing high and low level interactions with the autoRetouch API.
In most cases, you would like to process images according to some workflows within the scope of an organization.

Once you copied your `organization_id` from (https://app.autoretouch.com/organization) > Copy Organization ID.

To refer to a workflow, retrieve the workflow id at: https://app.autoretouch.com/workflows > ⋮ > Workflow API Information > id.

Example to upload an image and process it through a workflow:

```python
# ...
organization_id = "e722e62e-5b2e-48e1-8638-25890e7279e3"
workflow_id = "26740cd0-3a04-4329-8ba2-e0d6de5a4aaf"

input_image_content_hash = client.upload_image(image_path="input_image.jpg", organization_id=organization_id)

workflow_execution_id = client.create_workflow_execution_for_image_reference(workflow_id=workflow_id,
                                                                             image_content_hash=input_image_content_hash,
                                                                             image_name="input_image.jpg",
                                                                             mimetype="image/jpeg",
                                                                             labels={"myLabel": "myValue"},
                                                                             workflow_version_id=,
                                                                             organization_id=organization_id)

workflow_execution_status = client.get_workflow_execution_details(workflow_execution_id=workflow_execution_id,
                                                                  organization_id=organization_id).status

if workflow_execution_status == "COMPLETED":
    result_image_bytes = client.download_result_blocking(workflow_execution_id=workflow_execution_id,
                                                         organization_id=organization_id)

    with open("result_image.jpg", "wb") as f:
        f.write(result_image_bytes)

```
