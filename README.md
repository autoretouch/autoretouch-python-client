# autoretouch Python Client

Work in Progress Python client implementation for the most important public API endpoints for https://www.autoretouch.com.

API documentation: https://docs.api.autoretouch.com


## Installation 

```shell script
python3 -m venv venv 
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

This package exposes a single class `AutoretouchClient` allowing high- and low-level interactions with the autoRetouch API.

### High-level

#### Batch 

In most cases, you would like to process images according to some workflow within the scope of an organization.
To do so, you can simply

```python3
from autoretouch_api_client.client import AutoRetouchAPIClient

organization_id = "e722e62e-5b2e-48e1-8638-25890e7279e3"

ar_client = AutoRetouchAPIClient(
    organization_id=organization_id,
    # by default the client saves and reloads your credentials here:
    credentials_path="~/.config/autoretouch-credentials.json"
)

workflow_id = "26740cd0-3a04-4329-8ba2-e0d6de5a4aaf"
input_dir = "images_to_retouch/"
output_dir = "retouched_images/"

# starts a thread for each image and download the results to output_dir
ar_client.process_batch(workflow_id, input_dir, output_dir)
```
---
**Note**

- Get your `organization_id` from https://app.autoretouch.com/organization > Copy Organization ID.
- Get your `workflow_id` from https://app.autoretouch.com/workflows > `⋮` > Workflow API Information > id.
---

#### Single Image

If you wish to process a single image with a workflow, you can do

```python
ar_client.process_image("my_image.png", workflow_id, output_dir)
```

This is the method called internally by `proces_batch`. It will 
1. upload the image
2. start an execution
3. poll every 2 seconds for the status of the execution
4. download the result to `output_dir` or return `False` if the execution failed 

This is the recommended way to efficiently process images through our asynchronous api.  

#### Authentication

The `AutoRetouchAPIClient` authenticates itself with the [device flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/device-authorization-flow) of `auth0`.
Upon instantiation of the client, you can configure
- whether credentials should be persisted or not through `save_credentials=`
- where credentials should be persisted/loaded from through `credentials_path=`

If you don't pass a `credentials_path`, the client will first check if you passed a `refresh_token` with which it can obtain credentials.

If this argument is also `None`, the client will trigger a device flow from the top.
It will open a window in your browser asking you to confirm a device code.
The client will be authenticated once you confirmed.

By default, `credentials_path` and `refresh_token` are `None` but `save_credentials=True`.
The first time you use the client, this triggers the device flow and saves the obtained credentials to `~/.config/autoretouch-credentials.json`.
After that, it automatically falls back to this path and authenticates itself without you having to do anything :wink:


### Low-level Endpoints

for finer interactions with the API, the client exposes methods corresponding to endpoints.

TODO : table with `method name & signature | api docs link`