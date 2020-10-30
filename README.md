# Autograder.io Contrib
Contains utilities for writing applications that use the autograder.io API.

We recommend Amir Kamil's [autograder-tools](https://gitlab.eecs.umich.edu/akamil/autograder-tools/tree/master) for a larger collection of applications.

# Obtaining a Token
Log in to autograder.io in Chrome and open up the developer tools
from the Chrome menu (View->Developer->Developer Tools on a Mac).
Click on a course link. In the developer console, click on a request
(e.g. my_roles/ or projects/). Under Request Headers, there is an
Authorization entry that looks like "Token ". Copy
the hex string and save it to the file .agtoken in your home
directory.

# The Command Line Interface
This library provides a simple command line interface for sending requests:
```
$ ag_contrib get /api/users/current/
```

This interface notably does not support delete requests for safety reasons. If you wish to delete something, please do so through the autograder.io website or (at your own risk) you may use the HTTPClient class described in the next section.

# The HTTPClient
The `HTTPClient` class is a starting point for sending custom requests in Python applications.
```
import json
from ag_contrib.http_client import HTTPClient, check_response_status

client = HTTPClient.make_default()
response = client.get('/api/users/current/')
check_response_status(response)
print(json.dumps(response.json(), indent=4))
```

# Scripts
## Import/Export Project (Experimental)
These two scripts can be used to save a project's settings to the local filesystem and later create a new project from those same settings.
The data is stored mostly as JSON. Instructor files are downloaded and stored in a subdirectory.

Examples:
```
# Export project settings. Data is saved in a new folder called "my_project" in this case.
./export_project.py 42 my_project

# Create a new project in a different course with those settings. Note that the first argument is the course ID.
./import_project.py 10 my_project

# Create a new project with the same settings but on a local instance of autograder.io. URL schema and domain are required.
./import_project.py 2 --base_url http://localhost:9001 my_project
```

## sandbox_docker_image.py (Python >= 3.6)
You MUST specify a tag (other than "latest") in your docker image in order for it to be used by the autograder:

```
# ./sandbox_docker_image.py <id> --tag <imagename>:<tag>
./sandbox_docker_image.py 4 --tag myimage:0
```

Images tagged "latest" will still be visible in the drop-down menu in the test suite interface, but won't run.

`sandbox_docker_image.py` contains commands for displaying, editing, and creating sandbox Docker image metadata. Editing and creating can only be performed by superusers.

Examples:
```
# List image data.
./sandbox_docker_image.py list

# Examine a specific image.
# ./sandbox_docker_image.py detail [image_id]
./sandbox_docker_image detail 3

# Creates a new image.
# ./sandbox_docker_image.py create [name] [display_name] [tag]
./sandbox_docker_image.py create eecs9001 "EECS 9001" jameslp/eecs9001:1.0

# Edits an existing image. --display_name and --tag can be used individually.
# ./sandbox_docker_image.py [image_id] --display_name [new_display_name] --tag [new_tag]
./sandbox_docker_image.py 4 --display_name "EECS 9002" --tag jameslp/eecs9002:1.0
./sandbox_docker_image.py 4 --display_name "EECS 9002"
./sandbox_docker_image.py 4 --tag jameslp/eecs9001:2.0
```
