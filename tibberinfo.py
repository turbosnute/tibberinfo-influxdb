import asyncio
import os
import tibber
import arrow
from influxdb import InfluxDBClient


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


async def main(access_token):
    client = InfluxDBClient(influx_host, influx_port, influx_user, influx_pw, influx_db)
    tibber_connection = tibber.Tibber(access_token)
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
            client.write_points(cur_price_info, time_precision="s")

        entries = list()
        for entry in list(zip(home.price_total, home.price_total.values(), home.price_level.values())):
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
            client.write_points(entries, time_precision="s")

        #
        # Consumption last hour
        #

        # first check if it is nessecary to load more historic data...
        # Look for data from the latest 3 hours:
        result = client.query("select COUNT(cost) from consumption WHERE time > now() - 10h AND time < now()")

        if load_history or result.raw["series"] == []:
            # not much data. Lets add some
            numhours = 100
        elif result.raw["series"][0]["values"][0][1] < 8:
            # too little. lets add.
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
                        "fields": {"cost": if_string_zero(lastTotalCost), "consumption": if_string_zero(lastConsumption)},
                    }
                ]

                print(lastConsumption)
                if not influx_dry_run:
                    client.write_points(lastConsumption, time_precision="s")

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


if __name__ == "__main__":
    # Settings from env
    influx_host = os.getenv("INFLUXDB_HOST", "influxdb")
    influx_port = os.getenv("INFLUXDB_PORT", 8086)
    influx_user = os.getenv("INFLUXDB_USER", "root")
    influx_pw = os.getenv("INFLUXDB_PW", "root")
    influx_db = os.getenv("INFLUXDB_DATABASE", "tibber")
    influx_dry_run = str_to_bool(os.getenv("INFLUXDB_DRY_RUN", "False"))
    tibber_token = os.getenv("TIBBER_TOKEN")
    tibber_homes_only_active = str_to_bool(os.getenv("TIBBER_HOMES_ONLYACTIVE", "True"))
    load_history = str_to_bool(os.getenv("LOAD_HISTORY", "False"))
    verbose = str_to_bool(os.getenv("VERBOSE", "False"))

    if verbose:
        print("Influxdb Host: " + influx_user + "@" + influx_host + ":" + str(influx_port))
        print("Influxdb Password: *****")
        print("Influxdb DB: " + influx_db)
        print("Tibber Token: " + tibber_token)
        print("Only Active Homes: {}".format(tibber_homes_only_active))
        print("Load History: {}".format(load_history))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(tibber_token))
