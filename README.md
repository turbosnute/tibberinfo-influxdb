# tibberinfo-influxdb
Gets the current energy price, consumption and cost from Tibber's API and pushes it to InfluxDB.

## How to obtain a Tibber Token
- Go to https://developer.tibber.com/ and Sign in.
- Generate a new token (referred to as `<tibber-token>` below).

## InfluxDB Prerequisites
We assume that you already have
- an InfluxDB 2.x server running at `<influxdb-url>`,
- that you have created a bucket `<influxdb-bucket>` in the
- organization with the ID `<influxdb-org-id>` to which the
- token `<influxdb-token>` has read and write access.

If that is not the case, please head over to [InfluxDB V2 getting started](https://docs.influxdata.com/influxdb/v2/get-started/).


## Different ways to run tibberinfo-influxdb

Depending on your preferences, there are different ways to run tibberinfo-influxdb:

1. Without container, i.e. [run in a uv-managed Python virtual environment](#run-in-a-uv-managed-python-virtual-environment)
2. With container and [docker compose](#docker-compose)

### Run in a uv-managed Python virtual environment
1. If you don't have it yet, install [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation), an extremely fast Python package and project manager.
2. Place the necessary information in your shell's environment.
   ```bash
   export INFLUXDB_URL=<influxdb-url>
   export INFLUXDB_ORG_ID=<influxdb-org-id>
   export INFLUXDB_BUCKET=<influxdb-bucket>
   export INFLUXDB_TOKEN=<influxdb-token>
   export TIBBER_TOKEN=<tibber-token>
   ```
   It is probably a good idea to save this into a file named `~/.tibberinfo-influxdb_credentials` or similar, and source it in the future, so that you do not have to type it again and again.
3. ```bash
   uv run tibberinfo-influxdb
   ```

   (try `--help` and `--verbose` to see something - the script is designed to be quiet otherwise, so that it can be run in a cronjob without sending an e-mail every day).

   If you have created a `~/.tibberinfo-influxdb_credentials` file as advised, the command would be
   ```bash
   source ~/.tibberinfo-influxdb_credentials && uv run tibberinfo-influxdb
   ```
   Place it in your crontab to run it every few hours.


### Docker compose
Utilises the docker-compose.yml to get everything you need up and running.

#### Config
If you want to avoid getting git diffs, and still be able keep your config in the project directory, create a `docker-compose.override.yml` together with a `tibberinfo-influxdb.env` like this:

In the root of the repository, run:
```bash
cat << EOF > docker-compose.override.yml
services:
  tibberinfo-influxdb:
    env_file:
      - tibberinfo-influxdb.env
EOF

cat << EOF > tibberinfo-influxdb.env
INFLUXDB_URL=<influxdb-url>
INFLUXDB_ORG_ID=<influxdb-org-id>
INFLUXDB_BUCKET=<influxdb-bucket>
INFLUXDB_TOKEN=<influxdb-token>
TIBBER_TOKEN=<tibber-token>
EOF

```
Then adjust tibberinfo-influxdb.env so that it contains your values.

#### Build and start tibberinfo-influxdb container
Once tibberinfo-influxdb.env is in place with the correct data, run the following command:
```
docker-compose up -d
```
It will run the `tibberinfo.py` script in a loop every 12h.


## Usage

```
Usage: tibberinfo-influxdb [OPTIONS]

Options:
  --tibber-token TEXT         Tibber API token (alternatively set TIBBER_TOKEN
                              env. variable)  [required]
  --influx-bucket TEXT        InfluxDB Bucket name (create the bucket in
                              InfluxDB first; alternatively set
                              INFLUXDB_BUCKET env. variable)  [required]
  --load-history              Load historical data
  --verbose                   Get lots of information printed
  --tibber-homes-only-active  Only use active Tibber homes
  --influx-dry-run            Dry run for InfluxDB (do not write data)
  --help                      Show this message and exit.

      
  The following environment variables need to be set:    
  INFLUXDB_URL   e.g. "http://influxdb:8086",    
  INFLUXDB_TOKEN,    
  INFLUXDB_ORG_ID,    
  INFLUXDB_BUCKET - optional (can be provided as argument --influx-bucket),    
  TIBBER_TOKEN - optional (can be provided as argument --tibber-token)
```
(from `tibberinfo-influxdb --help`)

### Force loading consumption data for the last 720 hours
If you want to force loading the consumption statistics for the last 720 hours, use the `--load-history` option.

### Try to get data when your Tibber Subscription is not active yet
If you just signed up for Tibber, you can be in a situation where your subscription is not active yet. In that case you can use the `--tibber-homes-only-active` option, it might help you get some data.


## Crontab example

- Run every day
- Please randomize the minute (first number in the line) to reduce API load
- Run after 13:00 when prices for next day are usually set

```
23 13 * * * export INFLUXDB_URL=<influxdb-url>; export INFLUXDB_ORG_ID=<influxdb-org-id>; export INFLUXDB_BUCKET=<influxdb-bucket>; export INFLUXDB_TOKEN=<influxdb-token>; export TIBBER_TOKEN=<tibber-token>; uv run tibberinfo-influxdb
```