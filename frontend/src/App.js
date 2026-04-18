import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [operation, setOperation] = useState("simplify");
  const [language, setLanguage] = useState("hindi");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const API = "http://127.0.0.1:8000";

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setResult("");

      let response;

      // -------- PDF --------
      if (file) {
        const formData = new FormData();
        formData.append("file", file);

        if (operation === "simplify") {
          response = await axios.post(`${API}/pdf/simplify`, formData);
          setResult(response.data.simplified);
        }

        if (operation === "summarize") {
          response = await axios.post(`${API}/pdf/summarize`, formData);
          setResult(response.data.summary);
        }

        if (operation === "translate") {
          response = await axios.post(
            `${API}/pdf/translate?target_lang=${language}`,
            formData
          );
          setResult(response.data.translated_text);
        }
      }

      // -------- TEXT --------
      else {
        if (!text.trim()) {
          alert("Please enter text or upload PDF");
          return;
        }

        if (operation === "simplify") {
          response = await axios.post(`${API}/simplify`, { text });
          setResult(response.data.simplified);
        }

        if (operation === "summarize") {
          response = await axios.post(`${API}/summarize`, { text });
          setResult(response.data.summary);
        }

        if (operation === "translate") {
          response = await axios.post(`${API}/translate`, {
            text,
            target_lang: language,
          });
          setResult(response.data.translated_text);
        }
      }
    } catch (error) {
      console.error(error);
      alert("Backend not connected ⚠️");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result);
    alert("Copied to clipboard ✅");
  };

  return (
    <div className="container">
      <h1>⚖️ Legal Document AI Assistant</h1>

      <textarea
        placeholder="Paste legal text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <input type="file" onChange={(e) => setFile(e.target.files[0])} />

      <select onChange={(e) => setOperation(e.target.value)}>
        <option value="simplify">Simplify</option>
        <option value="summarize">Summarize</option>
        <option value="translate">Translate</option>
      </select>

      {operation === "translate" && (
        <select onChange={(e) => setLanguage(e.target.value)}>
          <option value="hindi">Hindi</option>
          <option value="telugu">Telugu</option>
          <option value="tamil">Tamil</option>
          <option value="malayalam">Malayalam</option>
          <option value="kannada">Kannada</option>
          <option value="marathi">Marathi</option>
          <option value="bengali">Bengali</option>
          <option value="gujarati">Gujarati</option>
          <option value="punjabi">Punjabi</option>
          <option value="urdu">Urdu</option>
        </select>
      )}

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Processing..." : "Run 🚀"}
      </button>

      {loading && <div className="loader">⏳ Processing your request...</div>}

      <div className="output">
        <h3>Output:</h3>
        {result || "Your result will appear here..."}
      </div>

      {result && (
        <button className="copy-btn" onClick={copyToClipboard}>
          Copy Output 📋
        </button>
      )}
    </div>
  );
}

export default App;