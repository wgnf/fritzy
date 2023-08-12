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
    });

app.use(express.json());

app.get('/total', async (request, response) => {
    try {
        const days = parseInt(request.query.days);
        let pipeline = [];

        if (days) {
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - days);

            pipeline.push({
                $match: {
                    date: { $gte: startDate }
                }
            });
        }

        pipeline = [
            ...pipeline,
            {
                $group: {
                    _id: null, // i don't want to transform the _id in any way!
                    total_connections: { $sum: '$connections' },
                    total_online_time: { $sum: '$online_time' },
                    total_megabytes_sent: { $sum: '$megabytes_sent' },
                    total_megabytes_received: { $sum: '$megabytes_received' },
                    total_megabytes: { $sum: '$megabytes_total' },
                    since_date: { $min: '$date' },
                    items: { $sum: 1 }
                }
            },
            // to transform the result in a format that i want
            {
                $project: {
                    _id: 0, // i don't need the _id
                    since_date: 1,
                    items: 1,
                    total_connections: 1,
                    total_online_time: 1,
                    total_megabytes_sent: 1,
                    total_megabytes_received: 1,
                    total_megabytes: 1
                }
            }
        ];
    
        const result = await client
            .db(mongoDb)
            .collection(mongoCollection)
            .aggregate(pipeline)
            .toArray();
    
        response.json(result[0]);
    } catch(error) {
        console.error('Error determining the total stats', error);
        response.status(500).send('Internal server error');
    }
});

app.get('/items', async (request, response) => {
    try {
        const days = parseInt(request.query.days);
        let query = {};

        if (days) {
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - days);

            query = {
                'date': {
                    $gte: startDate
                }
            };
        }

        const result = await client
            .db(mongoDb)
            .collection(mongoCollection)
            .find(query)
            .toArray();

        response.json(result);
    } catch(error) {
        console.error('Error determining the items', error);
        response.status(500).send('Internal server error');
    }
});

app.listen(port, async () => {
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
