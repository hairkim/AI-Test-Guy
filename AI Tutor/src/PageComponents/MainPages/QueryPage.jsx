import {React, useState} from 'react'
import QuestionsPage from './QuestionsPage.jsx'
import '../CSS/QueryPage.css'
import EnglishPage from './EnglishPage.jsx'

export default function HomePage() {
    const [page, setPage] = useState("math")

    //have two buttons at the top for math and english
    //math is QuestionsPage
    //english is TBD
    return (
        <div>
            <div className='buttons'>
                <button onClick={() => setPage("math")}>Math</button>
                <button onClick={() => setPage("english")}>English</button>
            </div>
            {page === "math" ? (
                <QuestionsPage />
            ) : page === "english" ? (
                <EnglishPage />
            ) : null} 
        </div>
    )
}
