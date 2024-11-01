import React, { useState } from 'react';
import './App.css';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');

  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const result = await axios.get('http://localhost:8000/ask', {
        params: {
          query: query,
        },
      });
      setResponse(result.data.answer);
    } catch (error) {
      setResponse('Bir hata oluştu, lütfen tekrar deneyin.');
      console.error('Error:', error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Chatbot Uygulaması</h1>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Bir soru sorun..."
          />
          <button type="submit">Sor</button>
        </form>
        {response && (
          <div className="response">
            <h3>Cevap:</h3>
            <p>{response}</p>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
