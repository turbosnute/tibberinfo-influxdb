# tibberinfo-influxdb
Gets the current energy price and the consumption and cost for the past hour and pushes it to your influxdb.

# How to obtain a Tibber Token
- Go to https://developer.tibber.com/ and Sign in.
- Genrerate a new token.

## Create Influxdb database

### Run InfluxDB in Docker
If you don't have a Influxdb server yet you can run one in Docker:
```
$ docker run -d -p 8086:8086 \
      -v influxdb:/var/lib/influxdb \
      influxdb
```

### Create Dabatase
```
$ curl -G http://<INFLUXDB_SERVER or DOCKER_HOST>:8086/query --data-urlencode "q=CREATE DATABASE tibber"
```

# How to run
```
docker run -d \
 -e INFLUXDB_HOST="influxdb" \
 -e INFLUXDB_DATABASE="tibber" \
 -e TIBBER_TOKEN="your tibber token" \
 --name "tibberinfo-influxdb" \
turbosnute/tibberinfo-influxdb:latest
```

## Advanced Options

### Specify InfluxDB Port and authentication
You  can specify the InfluxDB port, username and password:
```
 -e INFLUXDB_PORT="8086" \
 -e INFLUXDB_USER="root" \
 -e INFLUXDB_PW="root" \
```
### Debug
To get more debug data add:
```
 -e DEBUG="True" \
```
### Force Load Consumption data for last 100 hours
If you want to force the container to load the consumption statistics for the last 100 hours. This will load data for the 100 last hours and then exit the container. So remember to start the container again without this variable after it's done.
```
-e LOAD_HISTORY="True" \
```

### Try to get data when your Tibber Subscription is not active yet
If you just signed up for Tibber, you can be in a situation where your subscription is not active yet. In that case you can use the following settings, it might help you get some data.
```
-e TIBBER_HOMES_ONLYACTIVE="False" \
```
