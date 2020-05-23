import os
import json
import tibber
import arrow
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
loadHistory=os.getenv('LOAD_HISTORY', 'FALSE')
debug=os.getenv('DEBUG', 'false')

if str2bool(debug):
  print("Influxdb Host: " + influxuser + "@" + influxhost + ":" + str(influxport))
  print("Influxdb DB: " + influxdb)
  print("Hourly data DB: " + hourlydb)
  print("Tibber Token: " + tibbertoken)
  print("Only Active Homes: " + tibberhomes_only_active)
  print("Load History: " + loadHistory)

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
  if str2bool(debug):
    print("Home Address: " + address)
  #print(home.address1)
  home.sync_update_price_info()
  #print(home.current_price_info)
  
  #
  # Current price:
  #
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
  
  #
  # Consumption last hour
  #

  #first check if it is nessecary to load more historic data...
  #Look for data from the latest 3 hours:
  result=client.query("select COUNT(cost) from consumption WHERE time > now() - 10h AND time < now()")

  if str2bool(loadHistory) or result.raw['series'] == []:
    #not much data. Lets add some
    numhours = 100
  elif result.raw['series'][0]['values'][0][1] < 8:
    # too litle. lets add.
    numhours = 100
  else:
    numhours = 2

  lasthoursdata = home.sync_get_historic_data(numhours)
  for hourdata in lasthoursdata:
    #print(lasthourdata)
    lastTime = hourdata['from']
    #print(lastTime)
    timestamp = (arrow.get(lastTime).timestamp)
    #print(timestamp)
    lastConsumption = hourdata['consumption']
    lastTotalCost = hourdata['totalCost']
    #[{'from': '2020-05-22T15:00:00+02:00', 'totalCost': 0.1532024798387097, 'cost': 0.100783125, 'consumption': 0.855}]
    if lastConsumption is not None:
      lastConsumption = [{
         "measurement": "consumption",
         "time": timestamp,
         "fields": {
           "cost": lastTotalCost,
           "consumption": lastConsumption
         }
      }]
      
      print(lastConsumption)
      client.write_points(lastConsumption,time_precision='s')

tibber_connection.sync_close_connection()

if str2bool(loadHistory):
  exit
