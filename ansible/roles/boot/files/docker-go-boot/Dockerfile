# ethereum go bootnode
FROM ethereum/client-go

ENV GOPATH /root/go

RUN apt-get install -q -y build-essential pkg-config libgmp3-dev golang

RUN mkdir -p $GOPATH/src/github.com/ethereum/
RUN git clone https://github.com/ethereum/go-ethereum $GOPATH/src/github.com/ethereum/go-ethereum
WORKDIR $GOPATH/src/github.com/ethereum/go-ethereum
RUN git checkout develop
RUN GOPATH=$GOPATH:$GOPATH/src/github.com/ethereum/go-ethereum/Godeps/_workspace go install -v ./cmd/bootnode

CMD [""]
ENTRYPOINT ["bootnode"]
