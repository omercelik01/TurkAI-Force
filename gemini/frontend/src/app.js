import React, { useState } from "react";
import axios from "axios";

function App() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);

  const handleSubmit = async () => {
    try {
      const res = await axios.post("http://localhost:8000/ask", { query });
      setResponse(res.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      setResponse(null);
    }
  };

  return (
    <div>
      <h1>Hukuki Eğitim Chatbotu</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Soru sor..."
      />
      <button onClick={handleSubmit}>Sor</button>
      {response && (
        <div>
          <h2>Cevap:</h2>
          
          
          <p>Metin: {response.text}</p>
        </div>
      )}
    </div>
  );
}

export default App;
