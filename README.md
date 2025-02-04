# tibberinfo-influxdb
Gets the current energy price, consumption and cost from Tibber's API and pushes it to InfluxDB.

## How to obtain a Tibber Token
- Go to https://developer.tibber.com/ and Sign in.
- Generate a new token (referred to as <tibber-token> below).

## InfluxDB Prerequisites
We assume that you already have
- an InfluxDB 2.x server running at `<influxdb-url>`,
- that you have created a bucket `<influxdb-bucket>` in the
- organization `<influxdb-org>` to which the
- token `<influxdb-token>` has read and write access.

If that is not the case, please head over to [InfluxDB V2 getting started](https://docs.influxdata.com/influxdb/v2/get-started/).


## Run using docker-compose
Utilises the docker-compose.yml to get everything you need up and running.

### Config
If you want to avoid getting git diffs, and still be able keep your config in project director, create a `docker-compose.override.yml`
together with a `tibberinfo-influxdb.env` like this:
```
# In root of repository

cat << EOF > docker-compose.override.yml
version: '3'
services:
  tibberinfo-influxdb:
    env_file:
      - tibberinfo-influxdb.env
EOF

cat << EOF > tibberinfo-influxdb.env
INFLUXDB_URL=<influxdb-url>
INFLUXDB_ORG=<influxdb-org>
INFLUXDB_BUCKET=<influxdb-bucket>
INFLUXDB_TOKEN=<influxdb-token>
TIBBER_TOKEN=<tibber-token>
EOF

```

### Start tibberinfo-influxdb and dependencies.
Will run in a loop every 12h by default.
```
docker-compose up -d
```

## Run using pure docker
If you prefer to use docker directly.
### Create and Influxdb database
Create the influxdb instance which data will be pushed to.

#### Run InfluxDB in Docker
If you don't have a Influxdb server yet you can run one in Docker:
```
$ docker run -d -p 8086:8086 \
      -v influxdb:/var/lib/influxdb \
      influxdb
```

#### Create the database
```
$ curl -G http://<INFLUXDB_SERVER or DOCKER_HOST>:8086/query --data-urlencode "q=CREATE DATABASE tibber"
```

### Start tibberinfo-influxdb
```
docker run -d \
 -e INFLUXDB_HOST="influxdb" \
 -e INFLUXDB_DATABASE="tibber" \
 -e TIBBER_TOKEN="your tibber token" \
 --name "tibberinfo-influxdb" \
turbosnute/tibberinfo-influxdb:latest
```

## Run locally
```
export INFLUXDB_HOST=<hostname>; export INFLUXDB_DATABASE=<influx-db>; export TIBBER_TOKEN=<tibber-token>; python tibberinfo.py
```

## Options

| Option                    | Description                                                     | Default     |
|---------------------------|-----------------------------------------------------------------|-------------|
| `INFLUXDB_HOST`           | Influxdb hostname                                               | `influxdb`  |
| `INFLUXDB_PORT`           | Port that Influxdb is listening on                              | `8086`      |
| `INFLUXDB_USER`           | Influxdb user                                                   | `root`      |
| `INFLUXDB_PW`             | Influxdb password                                               | `root`      |
| `INFLUXDB_DATABASE`       | Influxdb database name                                          | `tibber`    |
| `INFLUXDB_DRY_RUN`        | Only emulate writing to Influxdb                                | `False`     |
| `TIBBER_TOKEN`            | Your Tibber development API token                               | `None`      |
| `VERBOSE`                 | Print more verbose information                                  | `False`     |
| `LOAD_HISTORY`            | Force Load Consumption data for last 100 hours                  | `False`     |
| `TIBBER_HOMES_ONLYACTIVE` | Try to get data when your Tibber Subscription is not active yet | `True`      |

## Options detailed description
### Force Load Consumption data for last 100 hours
If you want to force the container to load the consumption statistics for the last 100 hours. This will load data for the 100 last hours and then exit the container. So remember to start the container again without this variable after it's done.
```
LOAD_HISTORY="True"
```

### Try to get data when your Tibber Subscription is not active yet
If you just signed up for Tibber, you can be in a situation where your subscription is not active yet. In that case you can use the following settings, it might help you get some data.
```
TIBBER_HOMES_ONLYACTIVE="False"
```

## Crontab example


- Randomize the minute to offload api
- Run after 13 when prices for next day are usually set

```
23 13 * * * export INFLUXDB_HOST=<hostname>; export INFLUXDB_DATABASE=<influx-db>; export TIBBER_TOKEN=<tibber-token>; python /path/to/tibberinfo.py >> /path/to/tibberinfo.log 2>&1
```