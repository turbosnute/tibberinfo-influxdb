import asyncio
import os
import tibber
import arrow
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import click


# Helper functions remain the same
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
    # Initialize the client
    client = InfluxDBClient(url=influx_url, token=influx_token)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    query_api = client.query_api()

    tibber_connection = tibber.Tibber(tibber_token)
    await tibber_connection.update_info()
    print(tibber_connection.name)

    homes = tibber_connection.get_homes(only_active=tibber_homes_only_active)

    for home in homes:
        # await home.update_info()
        # address = home.address1
        # if verbose:
        #     print("Home Address: " + address)
        # await home.update_price_info()
        await home.update_info_and_price_info()
        if verbose:
            print("Home Address: {}".format(home.address1))

        cur_price_info = get_current_price(home)
        print(cur_price_info)
        if not influx_dry_run:
            write_api.write(bucket=influx_bucket, org=influx_org, record=cur_price_info)

        entries = list()
        for entry in list(
            zip(home.price_total, home.price_total.values(), home.price_level.values())
        ):
            startsAt = entry[0]
            total = entry[1]
            level = entry[2]
            level_pretty = level.lower().replace("_", " ").title()
            numlevel = map_level_to_int(level)

            entries.append(
                {
                    "measurement": "price",
                    "time": int(arrow.get(startsAt).timestamp()),
                    "tags": {"address": home.address1},
                    "fields": {
                        "startsAt": startsAt,
                        "price": if_string_zero(total),
                        "level": level,
                        "displaylevel": level_pretty,
                        "numberlevel": numlevel,
                    },
                }
            )

        print(entries)
        if not influx_dry_run:
            write_api.write(bucket=influx_bucket, org=influx_org, record=entries)

        #
        # Consumption last hour
        #

        # first check if it is nessecary to load more historic data...
        # Look for data from the latest 3 hours:
        query = f'from(bucket: "{influx_bucket}") |> range(start: -10h) |> filter(fn: (r) => r._measurement == "consumption")'
        result = query_api.query(org=influx_org, query=query)

        if load_history or not result.get_points():
            # not much data. Lets add some
            numhours = 100
        else:
            numhours = 2

        lasthoursdata = await home.get_historic_data(numhours)
        for hourdata in lasthoursdata:
            lastTime = hourdata["from"]
            timestamp = int(arrow.get(lastTime).timestamp())
            lastConsumption = hourdata["consumption"]
            lastTotalCost = hourdata["totalCost"]
            # Example:
            # [{'from': '2020-05-22T15:00:00+02:00', 'totalCost': 0.1532024798387097, 'cost': 0.100783125, 'consumption': 0.855}]
            if lastConsumption is not None:
                lastConsumption = [
                    {
                        "measurement": "consumption",
                        "time": timestamp,
                        "tags": {"address": home.address1},
                        "fields": {
                            "cost": if_string_zero(lastTotalCost),
                            "consumption": if_string_zero(lastConsumption),
                        },
                    }
                ]

                print(lastConsumption)
                if not influx_dry_run:
                    write_api.write(
                        bucket=influx_bucket, org=influx_org, record=lastConsumption
                    )

    await tibber_connection.close_connection()
    client.close()


def get_current_price(home: tibber.TibberHome) -> list:
    #
    # Current price:
    #
    total = home.current_price_info["total"]
    startsAt = home.current_price_info["startsAt"]
    level = home.current_price_info["level"]
    level_pretty = level.lower().replace("_", " ").title()
    numlevel = map_level_to_int(level)

    CurPriceInfo = [
        {
            "measurement": "price",
            "time": int(arrow.get(startsAt).timestamp()),
            "tags": {"address": home.address1},
            "fields": {
                "startsAt": startsAt,
                "price": if_string_zero(total),
                "level": level,
                "displaylevel": level_pretty,
                "numberlevel": numlevel,
            },
        }
    ]

    return CurPriceInfo


@click.command(
    epilog='\n\b\n\
    \nThe following environment variables need to be set if you need other values than the default values:\
    \n"INFLUXDB_URL": "http://influxdb:8086",\
    \n"INFLUXDB_TOKEN": "your-token",\
    \n"INFLUXDB_ORG_ID": "your-organization-id",\
    \n"Optional: INFLUXDB_BUCKET": "your-bucket",\
    \n"Optional: TIBBER_TOKEN": "your-token",\
    '
)
@click.option(
    "--tibber-token",
    default=lambda: os.getenv("TIBBER_TOKEN"),
    prompt=False,
    hide_input=True,
    help="Tibber API token",
)
@click.option(
    "--influx-bucket",
    default=lambda: os.getenv("INFLUXDB_BUCKET"),
    prompt=False,
    hide_input=False,
    help="InfluxDB Bucket",
)
@click.option(
    "--load-history",
    is_flag=True,
    help="Load historical data",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose mode",
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
    required_env_vars = {
        "INFLUXDB_URL": "http://influxdb:8086",
        "INFLUXDB_TOKEN": "your-token",
        "INFLUXDB_ORG_ID": "your-organization-id",
    }

    for var in required_env_vars.keys():
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
