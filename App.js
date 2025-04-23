import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [action, setAction] = useState('');
  const [processedData, setProcessedData] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleActionChange = (e) => {
    setAction(e.target.value);
  };

  const handleSubmit = () => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("action", action);

    axios.post('http://localhost:5000/process', formData)
      .then(response => {
        setProcessedData(response.data);
      })
      .catch(error => {
        console.error("There was an error processing the file!", error);
      });
  };

  return (
    <div>
      <h1>Data Preprocessing Tool</h1>
      <input type="file" onChange={handleFileChange} />
      <select onChange={handleActionChange}>
        <option value="remove_missing">Remove Missing Values</option>
        <option value="impute">Impute Missing Values</option>
        <option value="normalize">Normalize Data</option>
        <option value="remove_duplicates">Remove Duplicates</option>
      </select>
      <button onClick={handleSubmit}>Submit</button>

      {processedData && (
        <div>
          <h2>Processed Data:</h2>
          <pre>{JSON.stringify(processedData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
