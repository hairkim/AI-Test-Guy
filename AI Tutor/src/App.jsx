import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import './PageComponents/CSS/App.css'
import TrainModel from './pages/TrainModel.jsx'
import HomePage from './pages/HomePage.jsx'
import HomePageV2 from './pages/HomePageV2.jsx'
import Login from './pages/Login.jsx'
import Signup from './pages/SignupPage.jsx'
import Profile from './pages/Profile.jsx'
import ExamHistory from './pages/ExamHistory.jsx'
import TakeATest from './pages/TakeATest.jsx'
import MainPracticePage from './pages/MainPracticePage.jsx'
import PracticeQuestions from './pages/PracticeQuestions.jsx'
import QuestionsPage from './pages/QuestionsPage.jsx'
import EnglishPage from './pages/EnglishPage.jsx'
import ExamRouter from './routes/ExamRouter.jsx'
import SchoolScroller from './components/dashboard/SchoolScroller.jsx'
import SurvivalMode from './pages/SurvivalMode.jsx'
import SurvivalModeQuestions from './pages/SurvivalModeQuestions.jsx'

// import HomePageTest from './PageComponents/MainPages/HomePageTest.jsx'
import { AuthProvider } from './contexts/AuthContext.jsx'
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
          <Route path="/test/:examType" element={<ExamRouter /> } />
          <Route path="/exam_history" element={<ExamHistory /> } />
          <Route path="/practice" element={<MainPracticePage/> } />
          <Route path="/practice-questions" element={<PracticeQuestions/> } />
          <Route path="/query" element={<QuestionsPage/> } />
          <Route path="/english" element={<EnglishPage/> } />
          <Route path='/placeholder' element={<SchoolScroller/> } />
          <Route path="/survival" element={<SurvivalMode/> } />
          <Route path='/survival/questions' element={<SurvivalModeQuestions/> } />
          <Route path='/home' element={ <HomePage /> }/>
          <Route path='/homeV2' element={ <HomePageV2 /> }/>
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
