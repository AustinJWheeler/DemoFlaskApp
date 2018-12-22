#Demo Catalog App
This Flask app provides a simple catalog of items that can be created, edited, and deleted by its users. The items can also be sorted into pre-determined categories for better organization.

##Prerequisite Packages
This app has only been tested with `python 3.6+`. Assuming you have python installed, the following command will install all of the python packages required to run this app.
```
pip3 install  flask authlib sqlalchemy requests
```

##Installation
1) pull the code from git `git clone https://github.com/AustinJWheeler/DemoFlaskApp.git`
2) download your client secrets from the [google api console](https://console.developers.google.com/apis/credentials) and rename the file to `client_secrets.json` before placing it in the project direcroty next to `server.py`
3) run the command `python3 server.py` from the project directory to start the server
