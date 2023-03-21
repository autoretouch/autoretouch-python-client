# autoRetouch client

## Installation

Prerequisites: Sign up for free at https://app.autoretouch.com.

### from pypi

```shell
pip install autoretouch
```

### for development

clone this repo and then
```
pip install -e .
```

## CLI

CLI for interacting with [autoretouch: the ai-powered image editing platform](https://app.autoretouch.com).

Process images straight from your terminal.

### Features 

* auto-completion for bash, zsh

### Usage
```
Usage: autoretouch [OPTIONS] COMMAND [ARGS]...

Options:
  -h, --help  Show this message and exit.

Commands:
  balance        show your organization's current balance
  config         configure/show which organization and workflow are used by default
    get          show the organization and workflow that are currently used by default
    set          configure the organization and/or workflow that are used by default
  login          authenticate with your autoretouch account
  logout         revoke and remove stored refresh token from disk
  organization   show details of given organization
  organizations  list all your organizations
  process        process an image or a folder of images and wait for the result
  upload         upload an image from disk
  workflows      show workflows
```


## python client

Work in Progress Python client implementation for the most important public API endpoints for https://www.autoretouch.com.

API documentation: https://docs.api.autoretouch.com


### Usage

This package exposes a single class `AutoretouchClient` allowing high- and low-level interactions with the autoRetouch API.

#### High-level

##### Batch 

In most cases, you would like to process images according to some workflow within the scope of an organization.
To do so, you can simply

```python3
from autoretouch.api_client.client import AutoRetouchAPIClient
from uuid import UUID

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
ar_client.process_folder(input_dir, output_dir, UUID(workflow_id))
```
---
**Note**

- Get your `organization_id` from https://app.autoretouch.com/organization > Copy Organization ID.
- Get your `workflow_id` from https://app.autoretouch.com/workflows > `⋮` > Workflow API Information > id.
---

##### Single Image

If you wish to process a single image with a workflow, you can do

```python
from autoretouch.api_client.client import AutoRetouchAPIClient
from uuid import UUID

organization_id = "e722e62e-5b2e-48e1-8638-25890e7279e3"

ar_client = AutoRetouchAPIClient(
    organization_id=organization_id,
    # by default the client saves and reloads your credentials here:
    credentials_path="~/.config/autoretouch-credentials.json"
)
workflow_id = "26740cd0-3a04-4329-8ba2-e0d6de5a4aaf"
output_dir = "retouched_images/"
ar_client.process_image("my_image.png", output_dir, UUID(workflow_id))
```

This is the method called internally by `proces_batch`. It will 
1. upload the image
2. start an execution
3. poll every 2 seconds for the status of the execution
4. download the result to `output_dir` or return `False` if the execution failed 

This is the recommended way to efficiently process images through our asynchronous api.  

##### Authentication

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


#### Low-level Endpoints

for finer interactions with the API, the client exposes methods corresponding to endpoints.

TODO: table with `method name & signature | api docs link`
