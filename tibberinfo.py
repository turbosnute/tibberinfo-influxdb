import os
import json
import tibber
from influxdb import InfluxDBClient

# functions
def ifStringZero(val):
    val = str(val).strip()
    if val.replace('.','',1).isdigit():
      res = float(val)
    else:
      res = None
    return res

# settings from EnvionmentValue
influxhost=os.getenv('INFLUXDB_HOST', "localhost")
influxport=os.getenv('INFLUXDB_PORT', 8086)
influxuser=os.getenv('INFLUXDB_USER', 'root')
influxpw=os.getenv('INFLUXDB_PW', 'root')
influxdb=os.getenv('INFLUXDB_DATABASE', 'tibberPulse')
tibbertoken=os.getenv('TIBBER_TOKEN')

client = InfluxDBClient(influxhost, influxport, influxuser, influxpw, influxdb)

tibber_connection = tibber.Tibber(tibbertoken)
tibber_connection.sync_update_info()
#print(tibber_connection.name)

home = tibber_connection.get_homes()[0]
home.sync_update_info()
#print(home.address1)

home.sync_update_price_info()

#print(home.current_price_info)

total = home.current_price_info['total']
startsAt = home.current_price_info['startsAt']
level = home.current_price_info['level']

CurPriceInfo = [{
	"measurement": "price",
	"fields": {
		"startsAt": startsAt,
		"price": ifStringZero(total),
                "level": level
	}
}]

print(CurPriceInfo)
client.write_points(CurPriceInfo)

tibber_connection.sync_close_connection()
