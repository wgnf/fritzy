# fritzy

A small project to gather internet-stats from a fritz-box

## how to develop

### scripts

TODO

### server

TODO

### website

TODO

## how to fritz-box einrichten

TODO

## how to run

first you have to rename `.env.template` to `.env` and enter the values that fit your needs.  
  
to run you simply have to use `docker-compose` like so:  

```bash
docker compose -f ./src/docker-compose.yml up --build -d
```

to stop the docker-containers simply use:

```bash
docker compose -f ./src/docker-compose.yml stop
```

and to remove the docker-containers entirely use:

```bash
docker compose -f ./src/docker-compose.yml down
```
