#!/bin/sh

sudo docker stop $(docker ps -q)
sudo docker rm $(docker ps -aq)
sudo docker rmi $(docker images -aq)
sudo docker build -t dual-sensor-therm-web .
sudo docker run -d --name web --network host \
-v /run/dbus/system_bus_socket:/run/dbus/system_bus_socket \
-v /mnt/data/dual-sensors-therm/db:/usr/src/app/db \
-e DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket \
--cap-add=NET_ADMIN --cap-add=NET_RAW \
web