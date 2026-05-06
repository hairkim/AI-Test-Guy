import React from 'react';
import { BrowserRouter as Router, Routes, Route} from "react-router-dom";
import './PageComponents/CSS/App.css'
import TrainModel from './PageComponents/MainPages/TrainModel.jsx'
import HomePage from './PageComponents/MainPages/HomePage.jsx'
import Login from './PageComponents/MainPages/Login.jsx'
import Signup from './PageComponents/MainPages/SignupPage.jsx'
import Profile from './PageComponents/MainPages/Profile.jsx'
import ExamHistory from './PageComponents/MainPages/ExamHistory.jsx'
import TakeATest from './PageComponents/MainPages/TakeATest.jsx'
import MainPracticePage from './PageComponents/MainPages/MainPracticePage.jsx'
import PracticeQuestions from './PageComponents/MainPages/PracticeQuestions.jsx'
import QuestionsPage from './PageComponents/MainPages/QuestionsPage.jsx'
import EnglishPage from './PageComponents/MainPages/EnglishPage.jsx'
import ExamRouter from './PageComponents/MiscComponents/ExamRouter.jsx'
import SchoolScroller from './PageComponents/SupportingComponents/SchoolScroller.jsx'
import SurvivalMode from './PageComponents/MainPages/SurvivalMode.jsx'
import SurvivalModeQuestions from './PageComponents/MainPages/SurvivalModeQuestions.jsx'
import DashboardLayout from './PageComponents/MainPages/DashboardLayout.jsx'

import HomePageTest from './PageComponents/MainPages/HomePageTest.jsx'
import { AuthProvider } from './ClientStuff/AuthContext.jsx'
// import PlaceholderPage from './PlaceholderPage';


const App = () => {
  return (
    <Router>
      <AuthProvider>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path='/signup' element={<Signup />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/train" element={<TrainModel />} /> {/* this is TrainModel page */}
          <Route path="/take_a_test" element={<TakeATest />} />
          <Route path="/test/:examType" element={<ExamRouter /> } />
          <Route path="/exam_history" element={<ExamHistory /> } />
          <Route path="/practice" element={<MainPracticePage/> } />
          <Route path="/practice-questions" element={<PracticeQuestions/> } />
          <Route path="/query" element={<QuestionsPage/> } />
          <Route path="/english" element={<EnglishPage/> } />
          <Route path='/placeholder' element={<SchoolScroller/> } />
          <Route path="/survival" element={<SurvivalMode/> } />
          <Route path='/survival/questions' element={<SurvivalModeQuestions/> } />
          <Route path='/home' element={ <HomePageTest /> }/>
        </Route>
      </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
