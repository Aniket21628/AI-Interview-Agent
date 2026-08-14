'use client'

import { useState, useEffect } from 'react'
import InterviewInterface from './components/InterviewInterface'
import WelcomeScreen from './components/WelcomeScreen'
import { SocketProvider } from './context/SocketContext'

export default function Home() {
  const [interviewStarted, setInterviewStarted] = useState(false)
  const [candidateProfile, setCandidateProfile] = useState({
    name: '',
    position: '',
    experience: '',
    skills: []
  })

  const handleStartInterview = (profile) => {
    setCandidateProfile(profile)
    setInterviewStarted(true)
  }

  const handleEndInterview = () => {
    setInterviewStarted(false)
    setCandidateProfile({
      name: '',
      position: '',
      experience: '',
      skills: []
    })
  }

  return (
    <SocketProvider>
      <main className="min-h-screen">
        {!interviewStarted ? (
          <WelcomeScreen onStartInterview={handleStartInterview} />
        ) : (
          <InterviewInterface 
            candidateProfile={candidateProfile}
            onEndInterview={handleEndInterview}
          />
        )}
      </main>
    </SocketProvider>
  )
}