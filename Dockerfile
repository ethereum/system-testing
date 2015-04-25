FROM ubuntu:utopic
MAINTAINER caktux

ENV DEBIAN_FRONTEND noninteractive

# Usual update / upgrade
RUN apt-get update
RUN apt-get upgrade -q -y
RUN apt-get dist-upgrade -q -y

# Install useful tools
RUN apt-get install -q -y wget vim git

# Install requirements
RUN apt-get install -q -y libfreetype6-dev python python-dev python-pygraphviz pkg-config

# Install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py

# Install system-testing
# We add requirements.txt first to prevent unnecessary local rebuilds
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD . system-testing
WORKDIR system-testing

VOLUME ["/root/.boto"]
