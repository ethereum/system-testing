# Custom Dockerfile for kibana4.
FROM dockerfile/java:oracle-java7

MAINTAINER Konrad Feldmeier <konrad@brainbot.com>

RUN wget -q -O- https://download.elasticsearch.org/kibana/kibana/kibana-4.0.0-beta3.tar.gz | tar xzvf -

RUN mv /data/kibana-4.0.0-beta3 /kibana

# Add config file
ADD config/kibana.yml /kibana/config/kibana.yml

# http port for kibana, as defined in config file kibana.yml
EXPOSE 5601

ENTRYPOINT ["/kibana/bin/kibana"]
