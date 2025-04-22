import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [command, setCommand] = useState('');
  const [response, setResponse] = useState(null);

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("command", command);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setResponse(data);

      if (data.download_url) {
        const link = document.createElement('a');
        link.href = data.download_url;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (error) {
      console.error("Error:", error);
      setResponse({ error: "Upload failed. Try again." });
    }
  };

  return (
    <div className="App">
      <h1>CleanAI: Data Preprocessing Agent</h1>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <input
        type="text"
        placeholder="Enter command (e.g., clean and download)"
        value={command}
        onChange={(e) => setCommand(e.target.value)}
      />
      <button onClick={handleSubmit}>Submit</button>

      {response && (
        <div className="response">
          <h2>Response:</h2>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
