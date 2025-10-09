# Simple Connector (TypeScript / Express)

This example shows a minimal NSPS connector implemented with Express and TypeScript. It demonstrates how to receive POST events from NSPS at `/process-event`, verify the Bearer token, validate incoming payload fields, and return responses expected by NSPS.

## What this project is

- A small Express server written in TypeScript that accepts NSPS event requests.
- Demonstrates middleware-based token verification and request body parsing.
- Shows simple validation of incoming event payload and how to read nested fields (for example `data.event_type` and `pb_data.account_info.bill_status`).
- Intended as a quick-start template for building production-ready connectors.

## Technologies used

- Node.js (16+ recommended)
- TypeScript for type safety
- Express for the web framework
- dotenv for environment variable loading

Dependencies (from `package.json`):

```json
"dependencies": {
    "dotenv": "^17.2.3",
    "express": "^5.1.0"
},
"devDependencies": {
    "@types/express": "^5.0.3",
    "@types/node": "^24.6.2",
    "nodemon": "^3.1.10",
    "typescript": "^5.9.3"
}
```

## Project layout (key files)

- `src/index.ts` — main application file: config loading, Express app setup, token verification middleware, and `/process-event` route.
- `.env.example` — example environment variables (API_TOKEN, PORT).
- `package.json`, `tsconfig.json` — project metadata and TypeScript configuration.
- `Dockerfile`, `docker-compose.yaml` — containerization files for running the example in Docker (optional).
- `README.md` — example README with usage and additional notes. See `README.md` in this folder for quick start and examples.

## Code explanation

Bearer token verification middleware:

```ts
import type { Request, Response, NextFunction } from 'express';

const API_TOKEN = process.env.API_TOKEN || 'your-secret-token';

function verifyBearerToken(req: Request, res: Response, next: NextFunction) {
    const auth = req.headers['authorization'] || '';
    const token = auth.toString().replace('Bearer ', '');
    if (!auth.toString().startsWith('Bearer ') || token !== API_TOKEN) {
        return res.status(401).json({
            message: 'Authentication failed',
            error: 'Invalid API token',
            type: 'AUTHENTICATION_ERROR',
        });
    }
    next();
}
```

Processing the event and validating required fields:

```ts
app.post('/process-event', verifyBearerToken, (req: Request, res: Response) => {
    const { data, pb_data } = req.body;

    const eventType = data?.event_type;
    const billStatus = pb_data?.account_info?.bill_status;

    if (!eventType || !billStatus) {
        return res.status(422).json({
            message: 'Validation failed',
            error: 'Validation failed',
            type: 'VALIDATION_ERROR',
        });
    }

    console.log('Received event:', eventType, '| bill status:', billStatus);

    res.status(202).json({ message: 'Event accepted for processing' });
});
```

## How to run locally

1. Copy `.env.example` to `.env` and set `API_TOKEN` and `PORT`.
2. Install dependencies and build (using npm or yarn). Example with npm:

```
npm install; npm run build; npm start
```

3. For development with automatic reload you can use `nodemon`.

## Notes

- This example is intentionally minimal. For production-ready connectors consider adding request validation (e.g., using zod or Joi), structured logging, health checks, graceful shutdown, and tests.
- Ensure the `API_TOKEN` configured in the NSPS Handler matches the connector's `API_TOKEN`.

Also see [README][readme] file

<!-- References -->

[readme]: https://github.com/Mogorno/NSPS-connector-docs/tree/main/docs/examples/typescript/simple-connector-express
