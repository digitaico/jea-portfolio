import cors from 'cors';
import express from 'express';
import helmet from 'helmet';
import path from 'path';
import {fileURLToPath} from 'url';

const app = express();

const PORT = process.env.WEB_PORT || 3200;
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../', 'public', 'index.html'));
});

app.listen(
    PORT,
    () => {console.log(
        `>> [ATS FE Server]: Listening at ${process.env.WEB_HOST}:${PORT}`)})
