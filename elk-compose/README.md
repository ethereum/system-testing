ELK stack with docker-compose
===

Elasticsearch. Logstash. Kibana. Nginx. Docker.

All with logstash-forwarder, secured with nginx, and gift wrapped with docker-compose.

Yesh. That's some serious awesomesauce.

## Grab it
```
git clone https://github.com/caktux/elk-compose.git
cd elk-compose
```

## Configure it

#### Create a logstash-forwarder key and certificate

Replace `your.logstashdomain.tld` in there.

```
openssl req -x509  -batch -nodes -newkey rsa:2048 \
-keyout logstash/conf/logstash-forwarder.key \
-out logstash/conf/logstash-forwarder.crt \
-subj /CN=your.logstashdomain.tld
```

#### Create an htpasswd file for nginx/kibana
```
htpasswd -c nginx/conf/htpasswd username
```
Add the `htpasswd` file to the `conf` folder.

### Configure logstash for greatness

Add your filters in `logstash/conf.d`, which get linked as a volume in the logstash container to `/etc/logstash/conf.d`. Patterns can be added in `logstash/patterns` and can be used with `patterns_dir => '/opt/logstash/patterns_extra'` in `grok` sections of your filters.

### Install logstash-forwarder everywhere

Keep the certificate and key you created earlier handy, you'll need those.

On every machine you need to send logs from, install logstash-forwarder:
```
wget -O - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb http://packages.elasticsearch.org/logstashforwarder/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch.list
sudo apt-get update && sudo apt-get install logstash-forwarder
```

## Launch it
```
docker-compose up
```
Use with `-d` once you like what you're seeing.

Your data and indices get stored in `/var/lib/elasticsearch`, also mounted as a volume.


## License

Released under the MIT License, see LICENSE file.
