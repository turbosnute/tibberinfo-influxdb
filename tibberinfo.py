import asyncio
import os
import pprint
from datetime import datetime

import click
import tibber
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


def if_string_zero(val: str) -> float:
    val = str(val).strip()
    res = None
    if val.replace(".", "", 1).isdigit():
        res = float(val)

    return res


def str_to_bool(v: str) -> bool:
    """Interpret string as bool"""
    return v.lower() in ("yes", "true", "t", "1")


def map_level_to_int(level: str) -> int:
    if level == "VERY_CHEAP":
        numlevel = 0
    elif level == "CHEAP":
        numlevel = 1
    elif level == "NORMAL":
        numlevel = 2
    elif level == "EXPENSIVE":
        numlevel = 3
    elif level == "VERY_EXPENSIVE":
        numlevel = 4
    else:
        numlevel = -1

    return numlevel


def get_current_price(home: tibber.TibberHome) -> list[dict]:
    current_price_info = home.info["viewer"]["home"]["currentSubscription"]["priceInfo"]["current"]  # fmt: skip

    total = current_price_info["total"]
    starts_at = current_price_info["startsAt"]
    level = current_price_info["level"]
    level_pretty = level.lower().replace("_", " ").title()
    numlevel = map_level_to_int(level)

    cur_price_info = [
        {
            "measurement": "price",
            "time": starts_at,
            "tags": {"address": home.address1},
            "fields": {
                "startsAt": starts_at,
                "price": if_string_zero(total),
                "level": level,
                "displaylevel": level_pretty,
                "numberlevel": numlevel,
            },
        }
    ]

    return cur_price_info


async def main(
    influx_url: str,
    influx_token: str,
    influx_org: str,
    influx_bucket: str,
    influx_dry_run: bool,
    tibber_token: str,
    tibber_homes_only_active: bool,
    load_history: bool,
    verbose: bool,
):
    pprint.PrettyPrinter(indent=2, compact=True)

    # Initialize the InfluxDB connection
    client = InfluxDBClient(url=influx_url, token=influx_token)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    query_api = client.query_api()

    # Initialize the Tibber connection
    tibber_connection = tibber.Tibber(tibber_token, user_agent="tibberinfo-influxdb")
    await tibber_connection.update_info()
    if not tibber_connection.name:
        print(
            "Error: Connection to Tibber could not be established. Check token or network connectivity."
        )
        await tibber_connection.close_connection()
        exit(1)
    if verbose:
        print(f"Connected to Tibber, user '{tibber_connection.name}'")

    homes = tibber_connection.get_homes(only_active=tibber_homes_only_active)

    for home in homes:
        await home.update_info_and_price_info()
        if verbose:
            print("=== Home Address: {}".format(home.address1))

        await home.update_current_price_info()

        #
        # Price ingest
        #

        cur_price_info = get_current_price(home)
        if verbose:
            print("Current price info from Tibber:")
            pprint.pp(cur_price_info[0])
        if not influx_dry_run:
            if verbose:
                print("Writing above record to InfluxDB...\n---")
            write_api.write(
                bucket=influx_bucket, org=influx_org, record=cur_price_info[0]
            )

        price_records = list()
        for entry in home.info["viewer"]["home"]["currentSubscription"]["priceInfo"]["today"]:  # fmt: skip
            starts_at = entry["startsAt"]
            total = entry["total"]
            level = entry["level"]
            level_pretty = level.lower().replace("_", " ").title()
            numlevel = map_level_to_int(level)

            price_records.append(
                {
                    "measurement": "price",
                    "time": starts_at,
                    "tags": {"address": home.address1},
                    "fields": {
                        "startsAt": starts_at,
                        "price": if_string_zero(total),
                        "level": level,
                        "displaylevel": level_pretty,
                        "numberlevel": numlevel,
                    },
                }
            )

        if verbose:
            if verbose > 1:
                print(f"Price records from Tibber ({len(price_records)})")
                pprint.pp(price_records)
            else:
                print(
                    f"First and last price records from Tibber, of {len(price_records)} total:"
                )
                pprint.pp(price_records[0])
                print(f"[... {len(price_records) - 2} records ...]")
                pprint.pp(price_records[-1])
        if not influx_dry_run:
            if verbose:
                print(
                    f"Writing above {len(price_records)} record(s) to InfluxDB...\n---"
                )
            write_api.write(bucket=influx_bucket, org=influx_org, record=price_records)

        #
        # Consumption ingest
        #

        # Look for data from the latest 3 hours:
        result = None
        if not influx_dry_run:
            query = f'from(bucket: "{influx_bucket}") |> range(start: -3h) |> filter(fn: (r) => r._measurement == "consumption" )'
            result = query_api.query(org=influx_org, query=query)

            if verbose:
                print("InfluxDB returned these entries for the last 3 hours:")
                lines = []
                for table in result:
                    for record in table.records:
                        lines.append(
                            # Translating UTC to local timezone to avoid confusion when
                            # comparing with the Tibber records which are also in local time
                            f"{datetime.astimezone(record.get_time())} {record.get_field()} {record.get_value()}"
                        )
                pprint.pp(sorted(lines))

        if load_history or not result:
            # Get 720 hours worth of data (API maximum on hour level)
            numhours = 720
        else:
            # Just get the last two hours, this is probably being run from a cronjob
            numhours = 2

        consumption_records = []
        lasthoursdata = await home.get_historic_data(numhours)
        for hourdata in lasthoursdata:
            last_time = hourdata["from"]
            timestamp = last_time
            last_consumption = hourdata["consumption"]
            last_total_cost = hourdata["totalCost"]
            # Example:
            # [{'from': '2020-05-22T15:00:00+02:00', 'totalCost': 0.1532024798387097, 'cost': 0.100783125, 'consumption': 0.855}]
            if last_consumption is not None:
                consumption_records.append(
                    {
                        "measurement": "consumption",
                        "time": timestamp,
                        "tags": {"address": home.address1},
                        "fields": {
                            "cost": if_string_zero(last_total_cost),
                            "consumption": if_string_zero(last_consumption),
                        },
                    }
                )

        if verbose:
            if verbose > 1:
                print(f"Consumption records from Tibber ({len(consumption_records)})")
                pprint.pp(consumption_records)
            else:
                print(
                    f"First and last consumption records from Tibber, of {len(consumption_records)} total:"
                )
                pprint.pp(consumption_records[0])
                print(f"[... {len(consumption_records) - 2} records ...]")
                pprint.pp(consumption_records[-1])
        if not influx_dry_run:
            if verbose:
                print(
                    f"Writing above {len(consumption_records)} record(s) to InfluxDB..."
                )
            write_api.write(
                bucket=influx_bucket, org=influx_org, record=consumption_records
            )

    await tibber_connection.close_connection()
    client.close()


@click.command(
    epilog='\n\b\n\
    \nThe following environment variables need to be set:\
    \nINFLUXDB_URL   e.g. "http://influxdb:8086",\
    \nINFLUXDB_TOKEN,\
    \nINFLUXDB_ORG_ID,\
    \nINFLUXDB_BUCKET - optional (can be provided as argument --influx-bucket),\
    \nTIBBER_TOKEN - optional (can be provided as argument --tibber-token)\
    '
)
@click.option(
    "--tibber-token",
    default=lambda: os.getenv("TIBBER_TOKEN"),
    prompt=False,
    required=True,
    hide_input=True,
    help="Tibber API token (alternatively set TIBBER_TOKEN env. variable)",
)
@click.option(
    "--influx-bucket",
    default=lambda: os.getenv("INFLUXDB_BUCKET"),
    prompt=False,
    required=True,
    hide_input=False,
    help="InfluxDB Bucket name (create the bucket in InfluxDB first; alternatively set INFLUXDB_BUCKET env. variable)",
)
@click.option(
    "--load-history",
    is_flag=True,
    help="Load historical data",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Get lots of information printed",
)
@click.option(
    "--tibber-homes-only-active",
    is_flag=True,
    default=True,
    help="Only use active Tibber homes",
)
@click.option(
    "--influx-dry-run",
    is_flag=True,
    help="Dry run for InfluxDB (do not write data)",
)
def cli(
    tibber_token: str,
    influx_bucket: str,
    load_history: bool,
    verbose: bool,
    tibber_homes_only_active: bool,
    influx_dry_run: bool,
):
    # Check for required environment variables
    required_env_vars = ["INFLUXDB_URL", "INFLUXDB_TOKEN", "INFLUXDB_ORG_ID"]

    for var in required_env_vars:
        if os.getenv(var) is None:
            print(f"Error: Environment variable {var} is required.")
            exit(1)

    influx_url = os.getenv("INFLUXDB_URL")
    influx_token = os.getenv("INFLUXDB_TOKEN")
    influx_org = os.getenv("INFLUXDB_ORG_ID")
    if not influx_bucket:
        influx_bucket = os.getenv("INFLUXDB_BUCKET")
    if not tibber_token:
        tibber_token = os.getenv("TIBBER_TOKEN")

    if verbose:
        print(f"InfluxDB URL: {influx_url}")
        print("InfluxDB Token: *****")
        print(f"InfluxDB Org ID: {influx_org}")
        print(f"InfluxDB Bucket: {influx_bucket}")
        print(f"Tibber Token: {tibber_token}")
        print(f"Only Active Homes: {tibber_homes_only_active}")
        print(f"Load History: {load_history}")

    asyncio.run(
        main(
            influx_url,
            influx_token,
            influx_org,
            influx_bucket,
            influx_dry_run,
            tibber_token,
            tibber_homes_only_active,
            load_history,
            verbose,
        )
    )


if __name__ == "__main__":
    cli()
