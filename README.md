
### easy_access

This repository contains code for a project of the Brown University Library to make getting books and articles easier.

It contains code for the landing pages users see when they click links for books or articles.

It contains code for the handling of article-delivery (easyArticle); for books it hands off to an easyBorrow project.


##### Notes

- This code is not yet in production; it is based on work which is in production.

- The main purpose of this code is to merge together two separate projects.


##### Installation

(runserver only at moment)

- create a directory like `easyaccess_stuff`
- git clone this project in the `stuff` directory, like `easyaccess_project`
- create a virtual environment at the sibling level of easyaccess_project
- from the dev-server, get the easyaccess_env_settings.sh file, and update as needed
- have the env/bin/activate file source the settings file
- manually create the necessary dbs
- activate the virtual environment
- run python ./manage.py migrate to populate the tables
- run python ./manage.py check
- run python ./manage.py runserver


##### Acknowledgements

Not shown in the commit history is the fact that this entire project was implemented by [Ted Lawless](https://github.com/lawlesst) from 2012 through 2015. It has made the work of thousands of Brown University students and faculty vastly easier.
