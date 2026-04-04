const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3000;

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

// API endpoint to get questions
app.get('/api/questions', (req, res) => {
    const questionsPath = path.join(__dirname, 'data', 'questions.json');
    fs.readFile(questionsPath, 'utf8', (err, data) => {
        if (err) {
            console.error('Error reading questions file:', err);
            res.status(500).json({ error: 'Unable to load questions' });
        } else {
            res.json(JSON.parse(data));
        }
    });
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
});
