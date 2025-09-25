import React from 'react'
import { useParams } from 'react-router-dom'
import MathTestPage from '../MainPages/MathTestPage'
import EnglishTestPage from '../MainPages/EnglishTestPage'
import FullExamPage from '../MainPages/FullExamPage'

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