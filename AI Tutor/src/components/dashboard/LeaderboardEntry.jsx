import React from 'react'
import PropTypes from 'prop-types'
import '../../PageComponents/CSS/LeaderboardEntry.css'

export default function LeaderboardEntry( { entry } ) {
    return (
        <div className='leaderboard_entry'>
            {entry.rank}. {entry.user_name}: {entry.questions_correct}
        </div>
    )
}

LeaderboardEntry.propTypes = {
    entry: PropTypes.object.isRequired
}
