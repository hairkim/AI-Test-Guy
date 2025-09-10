import React from 'react'
import './TaskComponent.css'
import PropTypes from 'prop-types'

export default function TaskComponent({text, completed, onToggleComplete}) {
    return (
        <div className='task-component'>
            <li>
                <span>{text}</span>
                <div>
                    <input type="checkbox" checked={completed} onChange={onToggleComplete} />
                </div>
            </li>
        </div>
    )
}

TaskComponent.propTypes = {
    text: PropTypes.string.isRequired,
    completed: PropTypes.bool.isRequired,
    onToggleComplete: PropTypes.func.isRequired
}
