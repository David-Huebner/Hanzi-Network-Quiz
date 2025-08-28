

const express = require('express');
const fs = require('fs');
const path = require('path');
const PORT = 3000;
const quizStatusPath = path.join(__dirname, 'quiz_status.json');
const https = require('https');

const app = express();

const dbPath = path.join(__dirname, 'database.json');

app.use(express.json());
app.use(express.static(__dirname)); // Serve static files (HTML, JS, etc.)

// Get database
app.get('/api/database', (req, res) => {
    fs.readFile(dbPath, 'utf8', (err, data) => {
        if (err) return res.status(500).json({ error: 'Failed to read database.' });
        // Create backup
        const backupPath = path.join(__dirname, 'database_backup.json');
        fs.writeFile(backupPath, data, backupErr => {
            if (backupErr) console.error('Failed to create backup:', backupErr);
        });
        res.json(JSON.parse(data));
    });
});

// Update database (replace whole file)
app.post('/api/database', (req, res) => {
    fs.writeFile(dbPath, JSON.stringify(req.body, null, 2), err => {
        if (err) return res.status(500).json({ error: 'Failed to write database.' });
        res.json({ success: true });
    });
});

// Update a single entry
app.patch('/api/database/:key', (req, res) => {
    fs.readFile(dbPath, 'utf8', (err, data) => {
        if (err) return res.status(500).json({ error: 'Failed to read database.' });
        let db = JSON.parse(data);
        db[req.params.key] = req.body;
        fs.writeFile(dbPath, JSON.stringify(db, null, 2), err => {
            if (err) return res.status(500).json({ error: 'Failed to write database.' });
            res.json({ success: true });
        });
    });
});

// Get last completed date
app.get('/api/quiz-status', (req, res) => {
    fs.readFile(quizStatusPath, 'utf8', (err, data) => {
        if (err) return res.status(500).json({ error: 'Failed to read quiz status.' });
        res.json(JSON.parse(data));
    });
});

// Update last completed date
app.post('/api/quiz-status', (req, res) => {
    fs.writeFile(quizStatusPath, JSON.stringify(req.body, null, 2), err => {
        if (err) return res.status(500).json({ error: 'Failed to write quiz status.' });
        res.json({ success: true });
    });
});

/* app.listen(PORT, () => {
    console.log(`Server running at http://0.0.0.0:${PORT}/`);
}); */

// Read certificate and key
const options = {
  key: fs.readFileSync('/home/david/localhost+2-key.pem'),
  cert: fs.readFileSync('/home/david/localhost+2.pem')
};

// Bind to 0.0.0.0 so other devices can reach it
https.createServer(options, app).listen(3001, '0.0.0.0', () => {
  console.log('HTTPS server running at https://localhost:3001');
  console.log('Accessible on LAN at https://192.168.0.249:3001');
});