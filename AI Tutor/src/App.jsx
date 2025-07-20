import React from 'react';
import { BrowserRouter as Router, Routes, Route} from "react-router-dom";
import './App.css'
import QuestionsPage from './QuestionsPage.jsx'
import TrainModel from './TrainModel.jsx'


const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<QuestionsPage />} />
        <Route path="/train" element={<TrainModel />} />
      </Routes>
    </Router>
  )
}

export default App
