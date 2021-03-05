# Autograder.io Contrib
Contains utilities for writing applications that use the autograder.io API.

We recommend Amir Kamil's [autograder-tools](https://gitlab.eecs.umich.edu/akamil/autograder-tools/tree/master) for a larger collection of applications.

# Install with pip
```
pip install autograder-contrib
```

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
$ agcli get /api/users/current/
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
