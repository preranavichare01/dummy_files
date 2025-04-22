import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [command, setCommand] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Handle file selection
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  // Handle command input change
  const handleCommandChange = (e) => {
    setCommand(e.target.value);
  };

  // Handle file upload and processing
  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    
    // Prepare form data for file upload
    const formData = new FormData();
    formData.append('file', file);
    formData.append('command', command);

    try {
      const res = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResponse(res.data);
    } catch (err) {
      setError('Error uploading file. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Data Preprocessing Tool</h1>
      <input type="file" onChange={handleFileChange} />
      <input
        type="text"
        placeholder="Enter command (e.g., 'clean dataset')"
        value={command}
        onChange={handleCommandChange}
      />
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? 'Processing...' : 'Submit'}
      </button>

      {response && (
        <div>
          <h3>Processed Data Info:</h3>
          <p>Rows: {response.rows}</p>
          <p>Columns: {response.columns}</p>
          <p>Command used: {response.command_used}</p>
          <a href={response.download_url} download>
            Download Processed File
          </a>
        </div>
      )}

      {error && <p>{error}</p>}
    </div>
  );
}

export default App;
