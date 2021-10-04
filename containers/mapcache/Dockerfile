ARG BASE_IMAGE=ubuntu:20.04
FROM $BASE_IMAGE

# let's copy a few of the settings from /etc/init.d/apache2
ENV APACHE_CONFDIR /etc/apache2
ENV APACHE_ENVVARS $APACHE_CONFDIR/envvars
# and then a few more from $APACHE_CONFDIR/envvars itself
ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_RUN_DIR /var/run/apache2
ENV APACHE_PID_FILE $APACHE_RUN_DIR/apache2.pid
ENV APACHE_LOCK_DIR /var/lock/apache2
ENV APACHE_LOG_DIR /var/log/apache2
ENV LANG C


RUN apt-get update \
  && DEBIAN_FRONTEND="noninteractive" TZ="Europe/Oslo" apt-get -y install tzdata \
  && apt-get install -y git cmake apache2 apache2-dev dumb-init \
  && apt-get install -y libpng-dev libcurl4-gnutls-dev libjpeg8-dev libaprutil1-dev libapr1-dev \
  && apt-get install -y libpixman-1-dev libgdal-dev libpq-dev libsqlite3-dev libtiff-dev libgeotiff-dev libgeos-dev\
  && apt-get install -y libfcgi-dev postgresql-server-dev-all \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && git clone https://github.com/MapServer/mapcache.git /tmp/mapcache \
  && mkdir -p /tmp/mapcache/build && cd /tmp/mapcache/build \
  && cmake .. -DWITH_POSTGRESQL=1 -DWITH_TIFF=1 -DWITH_GEOTIFF=1 \
  && make install \
  && make clean \
  && printf "<IfModule mapcache_module>\n   MapCacheAlias /mapcache \"/etc/apache2/mapcache.xml\"\n</IfModule>\n" > /etc/apache2/mods-available/mapcache.conf \
  && printf "LoadModule mapcache_module /usr/lib/apache2/modules/mod_mapcache.so\n" > /etc/apache2/mods-available/mapcache.load \
  && printf "/usr/local/lib/" > /etc/ld.so.conf.d/mapcache.conf \
  && ldconfig \
  && a2enmod mapcache \
  && a2dismod -f auth_basic authn_file authn_core authz_host authz_user autoindex dir status \
  && rm /etc/apache2/mods-enabled/alias.conf \
  && mkdir -p $APACHE_RUN_DIR $APACHE_LOCK_DIR $APACHE_LOG_DIR \
  && ln -s ../../var/log/apache2 ${APACHE_CONFDIR}/logs \
  && mkdir -p /data/mapcache && chown www-data:www-data /data/mapcache && chmod g+w /data/mapcache\
  && find "$APACHE_CONFDIR" -type f -exec sed -ri ' \
       s!^(\s*CustomLog)\s+\S+!\1 /proc/self/fd/1!g; \
       s!^(\s*ErrorLog)\s+\S+!\1 /proc/self/fd/2!g; \
       ' '{}' ';' \
  && sed -ri 's!<VirtualHost\s\*:80>!<VirtualHost *:8090>!g' /etc/apache2/sites-available/000-default.conf \
  && sed -ri 's!Listen\s80$!Listen 8090!g' /etc/apache2/ports.conf \
  && apt-get -y autoremove

EXPOSE 8090

COPY mapcache.xml /etc/apache2/

ENV MS_DEBUGLEVEL 5
ENV MS_ERRORFILE stderr
ENV MAX_REQUESTS_PER_PROCESS 1000
ENV IO_TIMEOUT=40
ENV MIN_PROCESSES=1
ENV MAX_PROCESSES=5
ENV BUSY_TIMEOUT=300
ENV IDLE_TIMEOUT=300

CMD ["/usr/bin/dumb-init", "--", "apache2", "-DFOREGROUND"]
