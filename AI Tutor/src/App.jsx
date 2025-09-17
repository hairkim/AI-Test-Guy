import React from 'react';
import { BrowserRouter as Router, Routes, Route} from "react-router-dom";
import './PageComponents/CSS/App.css'
import TrainModel from './PageComponents/MainPages/TrainModel.jsx'
import HomePage from './PageComponents/MainPages/HomePage.jsx'
import Login from './PageComponents/MainPages/Login.jsx'
import Signup from './PageComponents/MainPages/SignupPage.jsx'
import Profile from './PageComponents/MainPages/Profile.jsx'
import TestPage from './PageComponents/MainPages/TestPage.jsx'
import ExamHistory from './PageComponents/MainPages/ExamHistory.jsx'
import TakeATest from './PageComponents/MainPages/TakeATest.jsx'
import MainPracticePage from './PageComponents/MainPages/MainPracticePage.jsx'
import PracticeQuestions from './PageComponents/MainPages/PracticeQuestions.jsx'
import QuestionsPage from './PageComponents/MainPages/QuestionsPage.jsx'
import EnglishPage from './PageComponents/MainPages/EnglishPage.jsx'
import { AuthProvider } from './ClientStuff/AuthContext.jsx'
// import PlaceholderPage from './PlaceholderPage';


const App = () => {
  return (
    <Router>
      <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<Login />} />
        <Route path='/signup' element={<Signup />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/train" element={<TrainModel />} /> {/* this is TrainModel page */}
        <Route path="/take_a_test" element={<TakeATest />} />
        <Route path="/test/:examType" element={<TestPage /> } />
        {/* <Route path="/english_test" element={<EnglishTestPage /> } /> */}
        <Route path="/exam_history" element={<ExamHistory /> } />
        <Route path="/practice" element={<MainPracticePage/> } />
        <Route path="/practice-questions" element={<PracticeQuestions/> } />
        <Route path="/query" element={<QuestionsPage/> } />
        <Route path="/english" element={<EnglishPage/> } />
      </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
