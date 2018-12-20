# Autograder.io Contrib
A collection of community-written scripts that utilize the autograder.io API.

We also recommend Amir Kamil's [autograder-tools](https://gitlab.eecs.umich.edu/akamil/autograder-tools/tree/master) scripts for determining the IDs of courses and projects.

# Obtaining a Token
Log in to the autograder in Chrome and open up the developer tools
from the Chrome menu (View->Developer->Developer Tools on a Mac).
Click on a course link. In the developer console, click on a request
(e.g. my_roles/ or projects/). Under Request Headers, there is an
Authorization entry that looks like "Token ". Copy
the hex string and save it to the file .agtoken in your home
directory.

# Scripts
## create_course.py (Python >= 3.6)
__You must be granted permission to create courses in order to use this script. Contact jameslp at umich.edu for more information.__

Creates an empty course and adds you to it as an admin. Courses must have a unique combination of name, semester, and year.

Examples:
```
./create_course "EECS 280" Winter 2019
```

## clone_course.py (Python >= 3.6)
__You must be granted permission to create courses in order to use this script. Contact jameslp at umich.edu for more information.__

Clones an existing course that you are an admin for. The new course will also contain copies of all the projects in the original course (including test case settings, but not including groups, submissions, or results). Courses must have a unique combination of name, semester, and year.

Examples:
```
./clone_course 42 "EECS 280" Winter 2019
```

## clone_project.py (Python >= 3.6)
Clones an existing project (including test case settings, but not including groups, submissions, or results). The new project can be added to the same course as the original or to another course you are an admin for.

Examples:
```
# Clone a project into the same course. The project must be given a new name.
# ./clone_project.py project_id target_course_id [new_project_name]
./clone_project.py 42 43 "Copy of Project"

# Clone a project into a different course. A new name is optional.
./clone_project.py 42 44
```
