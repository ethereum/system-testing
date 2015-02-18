# ethereum go bootnode
FROM ethereum/client-go

WORKDIR $GOPATH/src/github.com/ethereum/go-ethereum
RUN git checkout develop
RUN godep restore
RUN go install -v ./cmd/bootnode

ENTRYPOINT ["bootnode"]
