#!/bin/bash

docker build test/waf_bypass -t waf_bypass:latest

docker run --rm --network="host" -it -v ./target/reports:/app/reports \
  wallarm/gotestwaf --url=https://admin.tooka.com.br -noEmailReport

docker run --rm -it -v ./target/reports:/app/reports \
  waf_bypass:latest --host https://admin.tooka.com.br