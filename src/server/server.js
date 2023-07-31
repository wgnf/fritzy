import express from 'express';
import dotenv from 'dotenv';
import { MongoClient, ServerApiVersion } from 'mongodb';

const app = express();
dotenv.config();

const port = 8081;

const mongoUrl = process.env.MONGO_URL;
const mongoDb = process.env.MONGO_DB;
const mongoCollection = process.env.MONGO_COLLECTION;

const client = new MongoClient(mongoUrl, {
        serverApi: {
            version: ServerApiVersion.v1,
            strict: true,
            deprecationErrors: true
        }
    })

app.get('/total', async (request, response) => {
    const allData = client.db(mongoDb).collection(mongoCollection).find();
    client.db(mongoDb).collection(mongoCollection).aggregate

    let totalMegabytes = 0;
    for await (const data of allData) {
        totalMegabytes += data.megabytes_total;
    }

    const data = {
        totalMegabytes: totalMegabytes
    };

    response.status(200).send(data);
});

const server = app.listen(port, async () => {
    console.log(`fritzy-server listening on port ${port}`);

    try {
        console.log(`trying to connect to mongodb (url=${mongoUrl}, db=${mongoDb}, collection=${mongoCollection})...`);
        await client.connect();

        // send a ping to confirm successful connection
        await client.db('admin').command({ ping: 1 });

        console.log('successfully connected to the mongodb!');
    } catch (error) {
        console.error(`there was an error connecting to the mongodb: ${error}!`);
        process.exit(1);
    }
});

process.on('exit', () => {
    if (client != undefined) {
        console.log('closing mongodb connection...');
        client.close();
    }
});
