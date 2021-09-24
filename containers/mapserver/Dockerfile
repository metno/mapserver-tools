FROM ubuntu:20.04

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
ENV MAPSERVER_VERSION 7.4.\*


RUN apt-get update \
  && DEBIAN_FRONTEND="noninteractive" TZ="Europe/Oslo" apt-get -y install tzdata \
  && apt-get install -y apache2 cgi-mapserver=$MAPSERVER_VERSION libapache2-mod-fcgid dumb-init \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && a2enmod fcgid headers \
  && a2dismod -f auth_basic authn_file authn_core authz_host authz_user autoindex dir status \
  && rm /etc/apache2/mods-enabled/alias.conf \
  && mkdir -p $APACHE_RUN_DIR $APACHE_LOCK_DIR $APACHE_LOG_DIR \
  && ln -s ../../var/log/apache2 ${APACHE_CONFDIR}/logs \
  && mkdir -p /data/mapserver/map-files \
  && mkdir -p /data/mapserver/tile-index \
  && find "$APACHE_CONFDIR" -type f -exec sed -ri ' \
       s!^(\s*CustomLog)\s+\S+!\1 /proc/self/fd/1!g; \
       s!^(\s*ErrorLog)\s+\S+!\1 /proc/self/fd/2!g; \
       ' '{}' ';' \
  && sed -ri 's!<VirtualHost\s\*:80>!<VirtualHost *:8080>!g' /etc/apache2/sites-available/000-default.conf \
  && sed -ri 's!Listen\s80$!Listen 8080!g' /etc/apache2/ports.conf

EXPOSE 8080

COPY mapserver.conf /etc/apache2/conf-enabled/

ENV MS_DEBUGLEVEL 5
ENV MS_ERRORFILE stderr
ENV MAX_REQUESTS_PER_PROCESS 1000
ENV IO_TIMEOUT=40
ENV MIN_PROCESSES=1
ENV MAX_PROCESSES=5
ENV BUSY_TIMEOUT=300
ENV IDLE_TIMEOUT=300

CMD ["/usr/bin/dumb-init", "--", "apache2", "-DFOREGROUND"]
