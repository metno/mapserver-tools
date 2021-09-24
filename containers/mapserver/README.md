# CGI-mapserver Docker container with apache2 and fast cgi

## Usage:
Should come up with something like this:
```
docker run --rm -it  -p 80:80/tcp -v /home/trygveas/Git/mapserver-container/data/polar/senda/rgb:/data/polar/senda/rgb mapservercontainer:latest
```

Trick is here to spply the volume for the data. It is expected in /data/polar/senda/rgb or any other location configured in your shapefile. The shape file itself is generated outside the container and copied inside. This needs to be improved.

You can test your server with something like this:
```
curl "http://localhost/cgi-bin/mapserv?map=/etc/mapserver/senda_polar_satdata.map&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities"
```