import React from 'react'
import { useParams } from 'react-router-dom'
import MathTestPage from '../pages/MathTestPage'
import EnglishTestPage from '../pages/EnglishTestPage'
import FullExamPage from '../pages/FullExamPage'

function ExamRouter() {
  const { examType } = useParams()
  
  switch(examType) {
    case 'math_only':
      return <MathTestPage examType={examType} />
    case 'english_only':
      return <EnglishTestPage examType={examType} />
    case 'full_exam':
      return <FullExamPage examType={examType} />
    default:
      return <div>Invalid exam type</div>
  }
}

export default ExamRouter
