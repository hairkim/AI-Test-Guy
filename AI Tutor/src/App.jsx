import React from 'react';
import { BrowserRouter as Router, Routes, Route} from "react-router-dom";
import './App.css'
import HomePage from './HomePage.jsx'
import TrainModel from './TrainModel.jsx'
// import PlaceholderPage from './PlaceholderPage';


const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/train" element={<TrainModel />} /> {/* this is TrainModel page */}
      </Routes>
    </Router>
  )
}

export default App
