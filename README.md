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
## sandbox_docker_image.py (Python >= 3.6)
Contains commands for displaying, editing, and creating sandbox Docker image metadata. Editing and creating can only be performed by superusers.

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
