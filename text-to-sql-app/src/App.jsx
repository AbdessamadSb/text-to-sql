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
          className="textInp"
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
        <div >
          <div>
            <h2 >
              Generated SQL Query
            </h2>
            <pre >
              {result.query}
            </pre>
          </div>

          <div>
            <h2 >
              Query Result
            </h2>
            <div className="table">
              <table >
                <thead>
                  <tr className="text-left">
                    {result.result[0] &&
                      Object.keys(result.result[0]).map((key) => (
                        <th
                          key={key}
                          className="bg-gray-200 sticky top-0 border-b border-gray-300 px-6 py-3 text-gray-700 font-bold tracking-wider uppercase text-xs"
                        >
                          {key}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody>
                  {result.result.map((row, index) => (
                    <tr key={index}>
                      {Object.values(row).map((value, i) => (
                        <td
                          key={i}
                          className="border-dashed border-t border-gray-300 px-6 py-4 text-gray-700"
                        >
                          {value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h2 className="text-2xl font-semibold mb-4 text-gray-800">
              Interpretation
            </h2>
            <p className="text-gray-700 bg-gray-100 p-4 rounded-lg">
              {result.interpretation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
