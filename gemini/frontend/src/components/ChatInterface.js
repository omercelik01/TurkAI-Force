import React, { useState } from "react";
import axios from "axios";

function ChatInterface() {
    const [query, setQuery] = useState("");
    const [response, setResponse] = useState("");

    const handleInputChange = (e) => {
        setQuery(e.target.value);
    };

    const handleSubmit = async () => {
        try {
            const result = await axios.get("http://localhost:8000/ask", {
                params: { query: query }
            });
            setResponse(result.data.answer);
        } catch (error) {
            setResponse("Bir hata oluştu: " + error.message);
        }
    };

    return (
        <div>
            <h1>PDF Soru-Cevap Sistemi</h1>
            <input
                type="text"
                value={query}
                onChange={handleInputChange}
                placeholder="Sorunuzu buraya yazın..."
            />
            <button onClick={handleSubmit}>Gönder</button>
            <div>
                <h2>Cevap:</h2>
                <p>{response}</p>
            </div>
        </div>
    );
}

export default ChatInterface;
