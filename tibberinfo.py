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

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

# settings from EnvionmentValue
influxhost=os.getenv('INFLUXDB_HOST', "influxdb")
influxport=os.getenv('INFLUXDB_PORT', 8086)
influxuser=os.getenv('INFLUXDB_USER', 'root')
influxpw=os.getenv('INFLUXDB_PW', 'root')
influxdb=os.getenv('INFLUXDB_DATABASE', 'tibberPulse')
tibbertoken=os.getenv('TIBBER_TOKEN')
tibberhomes_only_active=str(os.getenv('TIBBER_HOMES_ONLYACTIVE', 'True'))

client = InfluxDBClient(influxhost, influxport, influxuser, influxpw, influxdb)

tibber_connection = tibber.Tibber(tibbertoken)
tibber_connection.sync_update_info()
#print(tibber_connection.name)

if str2bool(tibberhomes_only_active):
  homes=tibber_connection.get_homes(only_active=True)
else:
  homes=tibber_connection.get_homes(only_active=False)

for home in homes:
  home.sync_update_info()
  address=home.address1
  #print(home.address1)
  home.sync_update_price_info()
  #print(home.current_price_info)
  
  
  total = home.current_price_info['total']
  startsAt = home.current_price_info['startsAt']
  level = home.current_price_info['level']
  level_pretty = level.lower().replace('_',' ').capitalize()
  CurPriceInfo = [{
	"measurement": "price",
        "tags": {
                "address": address
        },
	"fields": {
		"startsAt": startsAt,
		"price": ifStringZero(total),
                "level": level,
                "displaylevel": level_pretty
	}
  }]
  
  print(CurPriceInfo)
  client.write_points(CurPriceInfo)

tibber_connection.sync_close_connection()
