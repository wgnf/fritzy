# fritzy

A little project to gather internet-stats from a fritz-box

## how to run

first you have to rename `.env.template` to `.env` and enter the values that fit your needs.  
  
to run you need to first build the docker-image of fritzy:  

```bash
sudo docker build -t fritzy-script ./src/scripts/
```

and then you can use docker-compose start the whole thing:

```bash
sudo docker-compose -f ./src/docker-compose.yml up -d
```
