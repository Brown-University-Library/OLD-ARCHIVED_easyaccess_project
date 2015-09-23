
#easyA

This project contains the easyArticle and easyBorrow (front-end) applications.  Previously these were in two separate projects - findit and delivery.

##Install
 - set up a virtualenvironment
 - obtain `easyaccess_env_settings.sh` from the development server, and adjust for your environment
 - have the env_eaz/bin/activate file source the `easyaccess_env_settings.sh` file
 - clone the repository
 - `pip install -r requirements` - this will install a number of libraries, both locally developed and external, required for the project.
 - `python manage.py runserver`


##Notes
 - sample items are available for manual testing at the root path for each app.  These are helpful for testing.
   - `/` - for findit
   - `/borrow` - for delivery
