FROM alpine:3.21

WORKDIR /app

COPY readme.md .

RUN apk update && apk add bash
RUN echo SIMPLE1 OVERRIDEN DOCKERFILE BUILD

RUN cat readme.md

ENTRYPOINT ["bash"]