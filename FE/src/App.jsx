import { Routes, Route, Link } from 'react-router-dom';
import TaskManager from './pages/TaskManager';
import MLLab from './pages/MLLab';
import Models from './pages/Models';
import TaskInsights from './pages/TaskInsights';
import History from './pages/History';
import About from './pages/About';

function App() {
  return (
    <>
      <nav className="nav">
        <Link to="/" className="nav-brand">Task Manager</Link>
        <div className="nav-links">
          <Link to="/">Tasks</Link>
          <Link to="/ml">ML Lab</Link>
          <Link to="/models">Models</Link>
          <Link to="/insights">Insights</Link>
          <Link to="/history">History</Link>
          <Link to="/about">About</Link>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<TaskManager />} />
        <Route path="/ml" element={<MLLab />} />
        <Route path="/models" element={<Models />} />
        <Route path="/insights" element={<TaskInsights />} />
        <Route path="/history" element={<History />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </>
  );
}

export default App;
