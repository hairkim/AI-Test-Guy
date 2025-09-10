import React from 'react';
import { BrowserRouter as Router, Routes, Route} from "react-router-dom";
import './PageComponents/App.css'
import QueryPage from './PageComponents/QueryPage.jsx'
import TrainModel from './PageComponents/TrainModel.jsx'
import HomePage from './PageComponents/HomePage.jsx'
import Login from './PageComponents/Login.jsx'
import Profile from './PageComponents/Profile.jsx'
import MathTestPage from './PageComponents/MathTestPage.jsx'
import ExamHistory from './PageComponents/ExamHistory.jsx'
import TakeATest from './PageComponents/TakeATest.jsx'
import EnglishTestPage from './PageComponents/EnglishTestPage.jsx'
import { AuthProvider } from './ClientStuff/AuthContext.jsx'
// import PlaceholderPage from './PlaceholderPage';


const App = () => {
  return (
    <Router>
      <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/query" element={<QueryPage />} />
        <Route path="/train" element={<TrainModel />} /> {/* this is TrainModel page */}
        <Route path="/take_a_test" element={<TakeATest />} />
        <Route path="/math_test" element={<MathTestPage /> } />
        <Route path="/english_test" element={<EnglishTestPage /> } />
        <Route path="/exam_history" element={<ExamHistory /> } />
      </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
