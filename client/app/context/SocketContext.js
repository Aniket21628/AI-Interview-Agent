'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { io } from 'socket.io-client'
import toast from 'react-hot-toast'

const SocketContext = createContext()

export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider')
  }
  return context
}

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [interviewSession, setInterviewSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [interviewStatus, setInterviewStatus] = useState({
    phase: 'greeting',
    questionCount: 0,
    maxQuestions: 15,
    complete: false
  })

  useEffect(() => {
    const serverUrl = process.env.NEXT_PUBLIC_SERVER_URL || 'http://localhost:5000'
    
    const socketInstance = io(serverUrl, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
    })

    // Connection events
    socketInstance.on('connect', () => {
      console.log('Connected to server')
      setConnected(true)
      toast.success('Connected to interview server')
    })

    socketInstance.on('disconnect', () => {
      console.log('Disconnected from server')
      setConnected(false)
      toast.error('Disconnected from server')
    })

    socketInstance.on('connect_error', (error) => {
      console.error('Connection error:', error)
      setConnected(false)
      toast.error('Failed to connect to server')
    })

    // Interview events
    socketInstance.on('interviewStarted', (data) => {
      console.log('Interview started:', data)
      setInterviewSession({
        sessionId: data.sessionId,
        active: true
      })
      setInterviewStatus({
        phase: data.phase,
        questionCount: data.questionCount,
        maxQuestions: data.maxQuestions,
        complete: false
      })
      
      // Add initial message
      setMessages([{
        id: Date.now(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString()
      }])
      
      toast.success('Interview started successfully!')
    })

    socketInstance.on('agentResponse', (data) => {
      console.log('Agent response:', data)
      
      setInterviewStatus({
        phase: data.phase,
        questionCount: data.questionCount,
        maxQuestions: data.maxQuestions,
        complete: data.complete
      })

      // Add agent message
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString(),
        evaluation: data.evaluation
      }])

      if (data.complete) {
        toast.success('Interview completed!')
      }
    })

    socketInstance.on('interviewCompleted', (data) => {
      console.log('Interview completed:', data)
      setInterviewStatus(prev => ({ ...prev, complete: true }))
      toast.success('Interview completed successfully!')
    })

    socketInstance.on('interviewEnded', (data) => {
      console.log('Interview ended:', data)
      setInterviewSession(null)
      setMessages([])
      setInterviewStatus({
        phase: 'greeting',
        questionCount: 0,
        maxQuestions: 15,
        complete: false
      })
      toast.info('Interview session ended')
    })

    socketInstance.on('error', (data) => {
      console.error('Socket error:', data)
      toast.error(data.message || 'An error occurred')
    })

    setSocket(socketInstance)

    return () => {
      socketInstance.disconnect()
    }
  }, [])

  const startInterview = (candidateProfile) => {
    if (socket && connected) {
      socket.emit('startInterview', { candidateProfile })
    } else {
      toast.error('Not connected to server')
    }
  }

  const sendMessage = (message) => {
    if (socket && connected && interviewSession) {
      // Add user message immediately
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, userMessage])
      
      // Send to server
      socket.emit('userMessage', { message })
    } else {
      toast.error('Cannot send message - not connected or no active session')
    }
  }

  const endInterview = () => {
    if (socket && connected) {
      socket.emit('endInterview')
    }
  }

  const getInterviewStatus = () => {
    if (socket && connected) {
      socket.emit('getInterviewStatus')
    }
  }

  const value = {
    socket,
    connected,
    interviewSession,
    messages,
    interviewStatus,
    startInterview,
    sendMessage,
    endInterview,
    getInterviewStatus
  }

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  )
}