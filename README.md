# tibberinfo-rpi
BETA. Currently only gets the current energy price from tibber and pushes it to your influxdb.

# How to run
```
docker run -d \
 -e INFLUXDB_HOST="localhost" \
 -e INFLUXDB_PORT="8086" \
 -e INFLUXDB_USER="root" \
 -e INFLUXDB_PW="root" \
 -e INFLUXDB_DATABASE="tibberPulse" \
 -e TIBBER_TOKEN="" \
 --name "tibberinso-influxdb" \
turbosnute/tibberinfo-influxdb:latest
```

