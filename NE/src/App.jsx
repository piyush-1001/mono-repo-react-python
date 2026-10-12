import { Routes, Route, Link } from 'react-router-dom';
import TaskManager from './pages/TaskManager';
import About from './pages/About';

function App() {
  return (
    <>
      <nav className="nav">
        <Link to="/" className="nav-brand">NE App</Link>
        <div className="nav-links">
          <Link to="/">Tasks</Link>
          <Link to="/about">About</Link>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<TaskManager />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </>
  );
}

export default App;
