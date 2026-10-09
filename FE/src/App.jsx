import { Routes, Route, Link } from 'react-router-dom';
import SentimentAnalyzer from './pages/SentimentAnalyzer';
import About from './pages/About';
import History from './pages/History';

function App() {
  return (
    <>
      <nav className="nav">
        <Link to="/" className="nav-brand">Smart App</Link>
        <div className="nav-links">
          <Link to="/">Analyzer</Link>
          <Link to="/history">History</Link>
          <Link to="/about">About</Link>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<SentimentAnalyzer />} />
        <Route path="/about" element={<About />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </>
  );
}

export default App;
