# tibberinfo-rpi
BETA. Currently only gets the current energy price from tibber and pushes it to your influxdb.

# How to obtain a Tibber Token
- Go to https://developer.tibber.com/ and Sign in.
- Genrerate a new token.

# How to run
```
docker run -d \
 -e INFLUXDB_HOST="influxdb" \
 -e INFLUXDB_DATABASE="tibber" \
 -e TIBBER_TOKEN="your tibber token" \
 --name "tibberinso-influxdb" \
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
 -e DEBUG="true" \
```
### Force Load Consumption data for last 100 hours
If you want to force the container to load the consumption statistics for the last 100 days you can use:
```
-e LOAD_HISTORY='True' \
```

### Try to get data even thou your Tibber Subscription is not active
If you just signed up for Tibber, you can be in a situation where your subscription is not active yet. In that case you can use the following settings, it might help you get some data.
```
-e TIBBER_HOMES_ONLYACTIVE='False' \
```
