# Custom Dockerfile for elasticsearch, that, other than dockerfile/elasticsearch, 
# runs elasticsearch as user.

## <cacheable header>
FROM dockerfile/java:oracle-java7

MAINTAINER Konrad Feldmeier <konrad@brainbot.com>

# Upgrading is not necessary
# RUN echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list &&\
#         apt-get update &&\
#         apt-get upgrade -y &&\
#         rm -rf /var/lib/apt/lists/*
## </cacheable header>


# Create elasticsearch user
RUN groupadd --gid 1001 elasticsearch
RUN useradd -ms /bin/bash --gid 1001 --uid 1001 elasticsearch
RUN chown elasticsearch. /home/elasticsearch

USER elasticsearch
ENV HOME /home/elasticsearch

# Install elasticsearch
#
RUN cd /home/elasticsearch &&\
wget -O - https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.4.4.tar.gz | tar xzf -

EXPOSE 9200
EXPOSE 9300

ENTRYPOINT ["/home/elasticsearch/elasticsearch-1.4.4/bin/elasticsearch"]

# Define volume
VOLUME ["/data", "/backup"]

