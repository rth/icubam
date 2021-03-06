# Installing

ICUBAM can be used by either installing it natively or using docker. To use docker see [following section](./docker.md)).

## Installing

This explains how to run a local instance of `icubam` on a developer's machine. We use conda, but you might choose virtualenv.

Steps:

- create a conda environment (e.g. `conda create -n icubam python=3.8`)
- activate the environment (`conda activate icubam`)
- install deps with `pip install -r requirements.txt`
- install the package in edit mode by running `pip install -e .`

**Note:** in addition to the python dependencies described in `requirements.txt`, `icubam` requires SQLite >= 3.24.0 as it uses upsert statements.

### Configuration

Create a `resources/icubam.env` file containing the following keys:
```
SECRET_COOKIE=random_secret
JWT_SECRET=another_secret
GOOGLE_API_KEY=a google maps api key
TW_KEY=
TW_API=
DB_SALT=
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=
```

N.B.: You can name and move this file as you want but you will have to add
`--dotenv_path=path/to/my_icubam.env` to the scripts when launching them.

### Pre-populate DB with test data

Create a fake database in order to be able to play with it:
`python scripts/populate_db_fake.py --config=resources/config.toml`

The database will be named `test.db`, cf. `resources/config.toml`.

## Running unit tests

To run unit tests, see the [contributing section](./contributing.md#testing).

## Running locally

### User id

Get one user identifier:
`python scripts/get_id_url.py`

This very long identifier will be required to access the main server.

To get all identifiers:
`python scripts/get_id_url.py --all`

### Main server

Start the main server locally:
`python scripts/run_server.py --config=resources/config.toml`

Will produce the following logs:
```
I0324 19:02:15.784908 139983874058048 server.py:32] UpdateHandler serving on /update
I0324 19:02:15.785018 139983874058048 server.py:32] HomeHandler serving on /
I0324 19:02:15.785090 139983874058048 server.py:49] Running WWWServer on port 8888
I0324 19:02:15.788751 139983874058048 server.py:51] http://localhost:8888/update?id=<A_VERY_LONG_ID>
```

Follow the proposed link `http://localhost:8888/update?id=<A_VERY_LONG_ID>`

### Backoffice server

Start the backoffice server locally,
```
python scripts/run_server.py --server=backoffice
```

Then open backoffice at [http://localhost:8890/bo/](http://localhost:8890/bo/)
(cf. `backoffice.dev` `root` value in `resources/config.toml`) and
login with user credentials created by the `populate_db_fake.py` script,
 - user: `admin@test.org`
 - password: `password`
