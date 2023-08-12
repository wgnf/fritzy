# the context to build this Dockerfile is in the parent-folder './src/'!

FROM node:18

WORKDIR /usr/src/fritzy

COPY ./server/package*.json ./
RUN npm install

COPY ./server .
COPY .env .

EXPOSE 8081

CMD [ "node", "server.js" ]