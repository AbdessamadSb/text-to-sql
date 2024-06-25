import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [databaseUploaded, setDatabaseUploaded] = useState(false);

  const handleDatabaseUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      setLoading(true);
      setError("");
      const formData = new FormData();
      formData.append("file", file);
      try {
        await axios.post("http://localhost:8080/upload_database", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
        setDatabaseUploaded(true);
        setError("");
      } catch (error) {
        console.error("Error uploading database:", error);
        setError("Failed to upload database. Please try again.");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!databaseUploaded) {
      setError("Please upload a database first.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await axios.post(
        "http://localhost:8080/process_question",
        { question }
      );
      setResult(response.data);
    } catch (error) {
      console.error("Error:", error);
      setError("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>SQL Query Generator Demo</h1>
      <div>
        <h2>Upload Database</h2>
        <input
          type="file"
          accept=".db"
          onChange={handleDatabaseUpload}
          disabled={loading}
        />
        {databaseUploaded && <p>Database uploaded successfully!</p>}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Enter your question about the database"
          disabled={loading || !databaseUploaded}
        />
        <button type="submit" disabled={loading || !databaseUploaded}>
          Submit
        </button>
      </form>
      {loading && <p>Processing...</p>}
      {error && <p className="error">{error}</p>}
      {result && (
        <div>
          <h2>Generated SQL Query:</h2>
          <pre>{result.query}</pre>
          <h2>Query Result:</h2>
          <pre>{JSON.stringify(result.result, null, 2)}</pre>
          <h2>Interpretation:</h2>
          <p>{result.interpretation}</p>
        </div>
      )}
    </div>
  );
}

export default App;
