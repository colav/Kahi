[![Python package](https://github.com/colav-playground/Kahi/actions/workflows/python-package.yml/badge.svg)](https://github.com/colav-playground/Kahi/actions/workflows/python-package.yml)
<center><img src="https://raw.githubusercontent.com/colav/colav.github.io/master/img/Logo.png"/></center>

# Kahi
KAHI is a powerful ETL (Extract, Transform, Load) application designed to construct an academic database by merging databases and files from various sources. It simplifies the database construction process by offering a framework to define a workflow of sequential tasks using a plugin system that KAHI understands.
 

# Description
TODO.

# Plugins
Take a look on plugins examples in the repository
https://github.com/colav/Kahi_plugins 

## Installation

To install KAHI, follow these simple steps:

1. Make sure you have Python installed on your system.
2. Open a terminal or command prompt.
3. Run the following command:

```shell
pip install kahi
```
Additionally, if you require specific plugins, you can install them using the following command:
```shell
pip install kahi[plugin-name]
```
Replace plugin-name with the name of the desired plugin.


# Usage

To use KAHI, you need to define a YAML file that contains the workflow and global configuration variables. Here is an example of a YAML file:
```yaml
config:
  mongodb_url: localhost
  database_name: kahi
  log_db: kahi_log
  log_collection: log

workflow:
  ror_affiliations:
    database_url: localhost:27017
    database_name: ror
    collection_name: stage

  staff_affiliations:
    file_path: data/staff_affiliations.csv

  scienti_affiliations:
    database_url: localhost:27017
    database_name: scienti_2022
    collection_name: products
```
In the config section, you can specify the MongoDB URL, database name, log database, and log collection for KAHI to use.

The workflow section contains the sequential tasks of the workflow. Each task is defined with a unique name and specific configuration options based on the data source. In the example above, three tasks are defined: ror_affiliations, staff_affiliations, and scienti_affiliations.
**Every task should be related to a plugin**

Finally, to run the workflow, use the following command:
```shell
kahi_run --workflow worflow.yaml
```
Replace workflow.yaml with the path to your YAML file.

# Logging
KAHI keeps a detailed log of each task's execution in a mongodb collection, including the name, execution time, elapsed time, execution status, and error messages. This information is valuable for both users and developers, and it enables the ability to resume the workflow from the last successful task.

# Contributing
If you are interested in contributing to KAHI or creating your own plugins, please refer to the kahi-plugins repository. It contains the necessary resources and documentation to implement new plugins easily. Feel free to submit pull requests or report any issues you encounter.

# License
BSD-3-Clause License 

# Links
http://colav.udea.edu.co/



