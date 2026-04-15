import express from 'express';
import cors from 'cors';
import compression from 'compression';
import helmet from 'helmet';

if (process.env.NODE_ENV !== 'production') {
  require('dotenv').config();
}

import proCyberneticaDashboardRouter from './routes/procybernetica-dashboard-route';

const app = express();
const port = process.env.PORT || 8080;

app.use(cors());
app.use(helmet());
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

app.use('/', proCyberneticaDashboardRouter);

const server = app.listen(port, () => {
  console.log(`Sherlock-search service listening on port ${port}.`);
});

process.on('SIGINT', () => {
  console.log('SIGINT signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
  });
});
