import express from 'express';
import type { Request, Response, NextFunction } from 'express';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(express.json());

const API_TOKEN = process.env.API_TOKEN || 'your-secret-token';
const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;

function verifyBearerToken(req: Request, res: Response, next: NextFunction) {
    const auth = req.headers['authorization'] || '';
    const token = auth.replace('Bearer ', '');
    if (!auth.toString().startsWith('Bearer ') || token !== API_TOKEN) {
        return res.status(401).json({
            message: 'Authentication failed',
            error: 'Invalid API token',
            type: 'AUTHENTICATION_ERROR',
        });
    }
    next();
}

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

app.listen(PORT, () => {
    console.log(`Connector listening on port ${PORT}`);
});
