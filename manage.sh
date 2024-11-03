#!/bin/bash

case "$1" in
  "start")
    docker-compose up -d
    ;;
  "stop")
    docker-compose down
    ;;
  "logs")
    docker-compose logs -f
    ;;
  "restart")
    docker-compose restart
    ;;
  *)
    echo "Usage: $0 {start|stop|logs|restart}"
    exit 1
    ;;
esac 