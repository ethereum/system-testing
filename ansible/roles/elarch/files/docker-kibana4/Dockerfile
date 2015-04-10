# Custom Dockerfile for kibana4.
FROM dockerfile/java:oracle-java7

MAINTAINER Konrad Feldmeier <konrad@brainbot.com>

RUN wget -q -O- http://download.elastic.co/kibana/kibana/kibana-4.1.0-snapshot-linux-x64.tar.gz | tar xzvf -

RUN mv /data/kibana-4.1.0-snapshot-linux-x64 /kibana

# Add config file
ADD config/kibana.yml /kibana/config/kibana.yml

# http port for kibana, as defined in config file kibana.yml
EXPOSE 5601

ENTRYPOINT ["/kibana/bin/kibana"]
