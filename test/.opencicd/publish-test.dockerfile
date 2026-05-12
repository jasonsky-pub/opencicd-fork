FROM alpine:3.21

WORKDIR /app

RUN apk update && apk add bash
RUN echo SIMPLE1 OVERRIDEN DOCKERFILE BUILD
