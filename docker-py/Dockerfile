FROM sveneh/pyethereum-base

RUN git clone --depth=1 --branch poc7 https://github.com/ethereum/pyethereum.git

# RUN cd pyethereum 

RUN cd pyethereum && curl http://downloads.buildout.org/2/bootstrap.py | python

RUN cd pyethereum && bin/buildout

ENTRYPOINT ["/pyethereum/bin/pyeth"]
