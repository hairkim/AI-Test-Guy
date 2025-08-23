import React from 'react';
import { BrowserRouter as Router, Routes, Route} from "react-router-dom";
import './PageComponents/App.css'
import QueryPage from './PageComponents/QueryPage.jsx'
import TrainModel from './PageComponents/TrainModel.jsx'
import HomePage from './PageComponents/HomePage.jsx'
import Login from './PageComponents/Login.jsx'
import { AuthProvider } from './ClientStuff/AuthContext.jsx'
// import PlaceholderPage from './PlaceholderPage';


const App = () => {
  return (
    <Router>
      <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<Login />} />
        
        <Route path="/query" element={<QueryPage />} />
        <Route path="/train" element={<TrainModel />} /> {/* this is TrainModel page */}
      </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
