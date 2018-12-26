# Demo Catalog App
This Flask app provides a simple catalog of items that can be created, edited, and deleted by its users. The items can also be sorted into pre-determined categories for better organization.

## Prerequisite Packages
This app has only been tested with `python 3.6+`. Assuming you have python installed, the following command will install all of the python packages required to run this app.
```
pip3 install  flask authlib sqlalchemy requests
```

## Downloading and Running
1) Pull the code from git `git clone https://github.com/AustinJWheeler/DemoFlaskApp.git`
2) Configure your redirect uris in the [google api console](https://console.developers.google.com/apis/credentials). The catalog app uses the redirect path `/callback`. If you running this on you local machine with the default port of 5000, you'll need to add the redirect uri `http://localhost:5000/callback`
3) Download your client secrets from the google api console and rename the file to `client_secrets.json` before placing it in the project direcroty next to `server.py`
4) Run the command `python3 server.py` from the project directory to start the server

## Populating the database
The app isn't very usable without any categories in the database, and since these are not designed to be user editable, there is no in-app interface for adding or editing them. The easiest way to get some sample data in the database to play around with is to run the file with the following command:
```
python3 populate_database.py
```