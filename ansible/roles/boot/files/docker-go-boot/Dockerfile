# ethereum go bootnode
FROM ethereum/client-go

WORKDIR $GOPATH/src/github.com/ethereum/go-ethereum
RUN git checkout develop
RUN GOPATH=$GOPATH:$GOPATH/src/github.com/ethereum/go-ethereum/Godeps/_workspace go install -v ./cmd/bootnode


ENTRYPOINT ["bootnode"]
