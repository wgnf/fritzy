# fritzy

A little project to gather internet-stats from a fritz-box

## how to run

first you have to rename `scripts.env.template` to `scripts.env` and enter the values that fit your needs.  
  
to run you need to first build the docker-image of fritzy:  

```bash
cd ./src/
sudo docker build -t fritzy .
```

and then you can use docker-compose start the whole thing:

```bash
sudo docker-compose up -d
```
