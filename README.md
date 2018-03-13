# Materials database

Welcome to the webpage of the [`materials_db`](https://materials-db.herokuapp.com) project. `materials_db` is a light-weight open-source platform for storing and searching chemical compounds and their properties. This platform can help analyze the properties of compounds and find relationships between various properties.

## Table of contents

1. [Introduction](README.md#introduction)
2. [Usage](README.md#usage)
    * [API for adding materials](README.md#api-for-adding-materials)
    * [API for searching materials](README.md#api-for-searching-materials)
      * [Full-text `search` query](README.md#full-text-search-query)
      * [Additional `properties` filters](README.md#additional-properties-filters)
3. [Installing locally](README.md#installing-locally)
    * [Install dependencies](README.md#install-dependencies)
    * [Set up a database](README.md#set-up-a-database)
    * [Set up a search engine](README.md#set-up-a-search-engine)
    * [Configure and run the app](README.md#configure-and-run-the-app)
6. [Future work](README.md#future-work)

## Introduction

Materials_db is an open-source web app with functionalities for adding and searching chemical compounds. The project is in its early development stage, and currently has only the backend. The frontend provides access to search/add APIs, as well as gives an option to populate the database through `csv` file upload.

## Usage

The platform may be accessed either through the front page https://materials-db.herokuapp.com, which provides access to the search/add APIs, or by interacting with the APIs directly, using tools such as [Postman](https://www.getpostman.com/) or `curl`. The frontend contains two text fields - for adding and searching materials in the database, and a file upload field for uploading a `csv` file. Both add/search APIs accept requests formatted as JSON, and there are checks to make sure that the request is correctly formatted and is used for correct purposes. The rest of this section describes the usage of the APIs.

### API for adding materials

The add APIs is available at the https://materials-db.herokuapp.com/data/add. It accepts POST requests containing JSON arrays formatted as follows:
```json
[
  {
    "compound": "PbS",
    "properties": [
      {
        "propertyName": "Band gap",
        "propertyValue": "0.41"
      },
      {
        "propertyName": "Color",
        "propertyValue": "Black"
      }
    ]
  }
]
```
Several compounds can be added at once - just do not forget to separate individual JSON objects by commas:
```json
[
  {
    "compound": "...",
    "properties": "..."
  },
  {
    "compound": "...",
    "properties": "..."
  }
]
```
There are several rules that must be followed when adding new compounds:
  * Both `compound` and `properties` keys must be present for each of the materials to be added.
  * The `compound` must be entered as a proper chemical formula. The platform relies on `pyEQL` package to parse chemical formulas, so all the [rules](http://pyeql.readthedocs.io/en/latest/chemistry.html) that apply to that package also apply to `materials_db`. For example, you should add "H2O" but not "h2o" or "H2o". Also, made-up chemical formulas such as "HeLLoU" won't parse correctly and the platform will complain.
  * All numerical values such as the value `"0.41"` for the band gap of PbS above must be entered as strings. The platform will figure out if these strings contain valid floats or integers and will process them appropriately.
  * Note that the `/data/add` API checks the input JSON against a `schemas['add']` [schema](https://github.com/agaiduk/materials-db/blob/master/data/schemas.py), and will complain if the request does not conform to it (or if it is not JSON).

### API for searching materials

The API for searching materials in the database is available at https://materials-db.herokuapp.com/data/search. It accepts POST requests containing search query JSON:
```json
{
  "search": "element:(Pb AND Se)",
  "properties" : [
    {
      "name" : "gap",
      "value" : "0.2",
      "logic" : "lt"
    },
    {
      "name" : "color",
      "value" : "gray",
      "logic" : "imatch"
    }
  ]
}
```
The platform is capable of doing full-text [Lucene](https://en.wikipedia.org/wiki/Apache_Lucene) search in the database, using the [`elasticsearch`](https://www.elastic.co/) engine through [`haystack`](http://haystacksearch.org/) interface, and it includes additional filters for the compound properties through `Django` interface. As such, the search consists of two parts - a general full-text search query is associated with the `search` key, and (optional) one or more filters for the compound properties are associated with the `properties` key. These two mechanisms of finding the compounds operate differently, so I'll discuss them separately.

#### Full-text `search` query
Most searches can be done using just one `search` field:
```json
{
  "search" : "PbS"
}
```
For instance, if you'd like to find the `PbS` material that we've just added, you could search for it the way shown above. Since some compounds in the database could be entered as "Pb1S1", it is useful to be able to search over constituent elements:
```json
{
  "search" : "element:Pb AND element:S"
}
```
This could be written more concisely as `element:(Pb AND S)`.

You can learn more about `elasticsearch` flavor of Lucene syntax on the [Elastic](https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-query-string-query.html#query-string-syntax) official webpage. It supports all the standard features such as `AND`, `OR`, `NOT` keywords, groupings, wildcards, and regular expressions.

Searching without keywords queries the index made of the compound name, the elements it contains, names of the properties and their values (similar to the format of `csv` file that can be used to populate the database, but with the addition of element names).

You can (and should) use keywords to make the search more precise. Keywords that can be used are `compound`, `element`, `group`, and `period`. This also means you can search, for example, for all the A<sup>IV</sup>B<sup>VI</sup> compounds by entering `group:(14 AND 16)` into the `search` field. (The group numbers are stored in the newer CAS format, not IUPAC format.) Groups and periods are determined automatically when a new compound is saved in the database, with the help of `pyEQL` library.

#### Additional `properties` filters
After carrying out a full-text search of the compounds in the database, you can narrow down search results by including one or more property filters:
```json
{
  "search": "",
  "properties" : [
    {
      "name" : "density",
      "value" : "1",
      "logic" : ">"
    }
  ]
}
```
For instance, the search query shown above will return all the materials that have the property called "density" with the value of greater than 1. Again, there are several rules for writing property filter queries:
* The `properties` search query relies on standard `Django` database API, which does not have Lucene goodies such as AND/OR/NOT logical words, groupings, wildcards, etc.
* There must be three fields defined for each property: `name`, `value`, and `logic`. All three should be strings, no floats/integers.
* The `name` is the name of the property. It is used to filter compounds using the `icontains` QuerySet keyword:
```python
Material.objects.filter(properties__propertyName__icontains='density')
```
Be careful with the property names - the request shown above would match both "Density" and "Electron density" fields - use more complete property names if needed.
* Some properties may be numerical, such as the density or the band gap of the material, while other may be purely textual, for example, the color ("Red") or smell ("Rotten eggs"). Still, the `value` keyword must be entered as strings - the app will figure out if the property is numerical and will convert it to a float as needed.
* The field `logic` refers to the logical opertor which will be used to query the database. Some standard `Django` operators - `exact`, `iexact`, `contains`, `icontains`, `gt`, `lt`, `gte`, `lte` are supported, as well as their synonyms such as `==`, `>`, `>=`, `<`, `<=`. The app checks if the correct logical operator is used for each data type, and complains if it's not. (Try filtering by color greater than "red"). The full list of the operators, their effect on the QuerySet, as well as the data type they are appropriate for, is given in the Table below:

|     Logical operators     | Django QuerySet keyword |  Data types  |
| -------------|:-------------|:----------|
| `eq`, `==`, `=`, `match`, `matches`, `exact` | `exact` | text, number |
| `ieq`, `imatch`, `imatches`, `iexact` | `iexact` | text |
| `contain`, `contains`, `contained` | `contains` | text |
| `icontain`, `icontains`, `icontained`, `in` | `icontains` | text |
| `>`, `gt`, `more`, `greater` | `gt` | number |
| `>=`, `gte`, `ge` | `gte` | number |
| `<`, `lt`, `less` | `lt` | number |
| `<=`, `=<`, `lte`, `le` | `lte` | number |
  * Similar to the `/data/add` API, `/data/search` checks the input JSON against a `schemas['search']` [schema](https://github.com/agaiduk/materials-db/blob/master/data/schemas.py), and will complain if the request does not conform to it (or if it is not JSON).

## Installing locally

You are welcome to access the app at its current [web address](https://materials-db.herokuapp.com) but you don't have to! You can install the app locally and play with it. To install, you will need to have necessary dependencies, as well as set up and configure the PostgreSQL database and elasticsearch engine. Earlier versions of this app used easier-to-setup filesystem-based `sqlite3` database and [`whoosh`](http://whoosh.readthedocs.io/en/latest/) search engine, so if you'd like to start with them, you can restore the code from earlier commits. (But be aware that parts of this `readme` will not work for the older version.) The installation instructions given below are for Ubuntu 16.04 system. First, download the `zip` file containing this distribution from https://github.com/agaiduk/materials-db/archive/master.zip, and unpack it on your local computer.

### Install dependencies

The dependencies are managed using `pipenv` utility and are listed in the [Pipfile](https://github.com/agaiduk/materials-db/blob/master/Pipfile) supplied with this distribution. Note that this Pipfile is configured for use with the [Heroku](https://www.heroku.com/) platform - if you are installing the app locally, you can delete these Heroku-specific dependencies:
```bash
urllib3 = "==1.22"
gunicorn = "*"
django-heroku = "*"
dj_database_url = "*"
```
Install the `pipenv` utility if you don't have it yet:
```bash
$ pip install pipenv
```
Then, while in the `materials_db` root directory, create a virtual environment and install dependencies:
```bash
$ pipenv install
```
### Set up a database

The app is using PostgreSQL database. You can follow the rest of this tutorial (and setup the same database) but you don't have to - since all requests are made through `haystack` or `Django` APIs, you can switch to any databases they support. The rest of this subsection is based on this great [tutorial](https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04) for Ubuntu system.

Using `apt` command, install the database and helper packages:
```bash
$ sudo apt-get update
$ sudo apt-get install python-dev libpq-dev postgresql postgresql-contrib
```
Login as a `postgres` user to perform administrative tasks:
```bash
$ sudo su - postgres
```
Then open a Postgres session:
```bash
$ psql
```
Now, let's create a database for our app. I will name it `materials_db`:
```sql
CREATE DATABASE materials_db;
```
Then, create a user:
```sql
CREATE USER <user> WITH PASSWORD '<password>';
```
Replace `<user>` and `<password>` with the username/password of your choice. Note that the password must be in quotes. Now set up user defaults:
```sql
ALTER ROLE <user> SET client_encoding TO 'utf8';
ALTER ROLE <user> SET default_transaction_isolation TO 'read committed';
ALTER ROLE <user> SET timezone TO 'UTC';
```
Give all `materials_db` database privileges to the user we've just created:
```sql
GRANT ALL PRIVILEGES ON DATABASE materials_db TO <user>;
```
Exit the SQL prompt to get back to the `postgres` user session:
```sql
\q
```
And exit the `postgres` session to go back to your shell session:
```bash
$ exit
```

### Set up a search engine

The `materials_db` platform uses the `elasticsearch` search engine (v.2.4.6). (Newer v.5 and v.6 releases cannot be used with the `django-haystack` search interface.) You can download the `deb` package [here](https://www.elastic.co/downloads/past-releases/elasticsearch-2-4-6). Install it on your system as follows:
```bash
$ sudo apt-get update
$ sudo dpkg -i elasticsearch-2.4.6.deb
$ sudo apt-get -f install
```
Now, start the search engine:
```bash
$ sudo /etc/init.d/elasticsearch start
```
You can check the status of the search engine if you wish:
```bash
$ curl "localhost:9200/_nodes?pretty=true&settings=true"
```
We are almost done!

### Configure and run the app

We need to configure the app to let it know where the database and search engine are. Open the `materials_db/settings.py` file and delete the following blocks of code:
```python
import django_heroku
import dj_database_url
from urllib.parse import urlparse
```
```python
es = urlparse(os.environ.get('SEARCHBOX_URL') or 'http://127.0.0.1:9200/')
port = es.port or 80

# Haystack configuration with Elasticsearch

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine',
        'URL': es.scheme + '://' + es.hostname + ':' + str(port),
        'INDEX_NAME': 'materials_db',
    },
}

if es.username:
    HAYSTACK_CONNECTIONS['default']['KWARGS'] = {"http_auth": es.username + ':' + es.password}
```
```python
django_heroku.settings(locals())
DATABASES['default'] = dj_database_url.config(conn_max_age=600, ssl_require=True)
```
Add the database configuration:
```python
# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'materials_db',
        'USER': '<user>',
        'PASSWORD': '<password>',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```
Do not forget to replace `<user>` and `<password>`! Add `haystack` configuration with `elasticsearch` binding:
```python
# Haystack configuration with Elasticsearch
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'materials_db',
    },
}
```
Activate app's virtual environment by typing:
```bash
$ pipenv shell
```
This will also install all necessary dependencies. Now make migrations for the database:
```bash
$ python manage.py makemigrations data
```
Assuming you didn't do any changes to the models, this will output `No changes detected in app 'data'`. Apply the migrations to the database:
```bash
$ python manage.py migrate
```
We're ready to run our app:
```bash
$ python manage.py runserver
```
This should print something like
```bash
Performing system checks...

System check identified no issues (0 silenced).
March 12, 2018 - 22:55:17
Django version 2.0.3, using settings 'materials_db.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```
Open the webpage http://127.0.0.1:8000/ in your browser and try some simple search, for example:
```json
{
  "search" : ""
}
```
This will return an empty array `[]` because there is no data in our database yet. We can populate it quickly by uploading the [`csv` file](https://github.com/agaiduk/materials-db/blob/master/data.csv) supplied with the package. Click on the "Choose file" at the bottom of the http://127.0.0.1:8000/ webpage and select the file; then click on "Upload". If everything is OK, it will reload the `materials_db` webpage with a message "103 of 103 materials added to the database". That's it! Haystack's `RealtimeSignalProcessor` updates the `elasticsearch` index every time something happens to the database, so there is no need to update it manually. You can start using the `materials_db` platform!

## Future work

`materials_db` is an early-stage project! It can and will be developed further. Among the things I will work on next are the front-end (which is pretty much missing currently), to make it more user-friendly. Also, I will extend the full-text functionality to the properties of the compounds. Eventually, there will be only two fields to filter the materials, `compound` and `properties`:
```json
{
  "compounds" : "element:(Pb AND Se)",
  "properties" : "(name:gap AND value:>0.2)"
}
```
I also plan to explore NoSQL databases such as `mongoDB` to provide more uniform search capabilities, potentially moving to a single search field.
