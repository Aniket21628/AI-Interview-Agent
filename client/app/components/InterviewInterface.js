'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSocket } from '../context/SocketContext'
import VoiceControls from './VoiceControls'
import ChatMessage from './ChatMessage'
import ProgressBar from './ProgressBar'
import InterviewStats from './InterviewStats'
import { Toaster } from 'react-hot-toast'
import { 
  PaperAirplaneIcon, 
  XMarkIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon
} from '@heroicons/react/24/outline'

export default function InterviewInterface({ candidateProfile, onEndInterview }) {
  const { 
    connected, 
    interviewSession, 
    messages, 
    interviewStatus, 
    startInterview, 
    sendMessage, 
    endInterview 
  } = useSocket()

  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [showVoiceControls, setShowVoiceControls] = useState(true)
  const [autoSpeak, setAutoSpeak] = useState(true)
  const [isInitialized, setIsInitialized] = useState(false)
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Initialize interview when component mounts
  useEffect(() => {
    if (connected && !interviewSession && !isInitialized) {
      startInterview(candidateProfile)
      setIsInitialized(true)
    }
  }, [connected, interviewSession, candidateProfile, startInterview, isInitialized])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-speak agent messages
  useEffect(() => {
    if (autoSpeak && messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.role === 'assistant' && 'speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(lastMessage.content)
        utterance.rate = 0.9
        utterance.pitch = 1
        utterance.volume = 0.8
        
        // Use a pleasant voice if available
        const voices = speechSynthesis.getVoices()
        const preferredVoice = voices.find(voice => 
          voice.name.includes('Google') || 
          voice.name.includes('Microsoft') ||
          voice.lang.startsWith('en')
        )
        if (preferredVoice) {
          utterance.voice = preferredVoice
        }
        
        speechSynthesis.speak(utterance)
      }
    }
  }, [messages, autoSpeak])

  const handleSendMessage = (e) => {
    e.preventDefault()
    
    if (!inputMessage.trim() || !connected || !interviewSession) {
      return
    }

    sendMessage(inputMessage.trim())
    setInputMessage('')
    setIsTyping(false)
  }

  const handleVoiceMessage = (transcript) => {
    if (transcript && connected && interviewSession) {
      sendMessage(transcript)
    }
  }

  const handleEndInterview = () => {
    if (window.confirm('Are you sure you want to end the interview?')) {
      endInterview()
      onEndInterview()
    }
  }

  const toggleAutoSpeak = () => {
    setAutoSpeak(!autoSpeak)
    if (!autoSpeak) {
      speechSynthesis.cancel() // Stop any current speech
    }
  }

  if (!connected) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to interview server...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-semibold text-gray-900">
                  AI Interview - {candidateProfile.name}
                </h1>
              </div>
              <div className="ml-4">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleAutoSpeak}
                className={`p-2 rounded-lg transition-colors ${
                  autoSpeak 
                    ? 'bg-primary-100 text-primary-600' 
                    : 'bg-gray-100 text-gray-600'
                }`}
                title={autoSpeak ? 'Disable auto-speak' : 'Enable auto-speak'}
              >
                {autoSpeak ? (
                  <SpeakerWaveIcon className="w-5 h-5" />
                ) : (
                  <SpeakerXMarkIcon className="w-5 h-5" />
                )}
              </button>
              
              <button
                onClick={handleEndInterview}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <XMarkIcon className="w-4 h-4 mr-2" />
                End Interview
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <ProgressBar 
        current={interviewStatus.questionCount} 
        max={interviewStatus.maxQuestions}
        phase={interviewStatus.phase}
      />

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            <AnimatePresence>
              {messages.map((message, index) => (
                <ChatMessage 
                  key={message.id || index} 
                  message={message}
                  isLatest={index === messages.length - 1}
                />
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t bg-white p-4">
            <div className="max-w-4xl mx-auto">
              {/* Voice Controls */}
              {showVoiceControls && (
                <div className="mb-4">
                  <VoiceControls 
                    onVoiceMessage={handleVoiceMessage}
                    disabled={!connected || !interviewSession || interviewStatus.complete}
                  />
                </div>
              )}

              {/* Text Input */}
              <form onSubmit={handleSendMessage} className="flex space-x-4">
                <div className="flex-1">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => {
                      setInputMessage(e.target.value)
                      setIsTyping(e.target.value.length > 0)
                    }}
                    placeholder={
                      interviewStatus.complete 
                        ? "Interview completed" 
                        : "Type your response or use voice input..."
                    }
                    disabled={!connected || !interviewSession || interviewStatus.complete}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || !connected || !interviewSession || interviewStatus.complete}
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <PaperAirplaneIcon className="w-5 h-5" />
                </button>
              </form>

              {/* Quick Actions */}
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  onClick={() => handleVoiceMessage("Can you repeat the question?")}
                  disabled={!connected || !interviewSession || interviewStatus.complete}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Repeat Question
                </button>
                <button
                  onClick={() => handleVoiceMessage("Can you clarify what you mean?")}
                  disabled={!connected || !interviewSession || interviewStatus.complete}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Need Clarification
                </button>
                <button
                  onClick={() => setShowVoiceControls(!showVoiceControls)}
                  className="px-3 py-1 text-sm bg-primary-100 text-primary-700 rounded-full hover:bg-primary-200"
                >
                  {showVoiceControls ? 'Hide' : 'Show'} Voice Controls
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-80 bg-white border-l border-gray-200 p-4 space-y-6">
          <InterviewStats 
            candidateProfile={candidateProfile}
            interviewStatus={interviewStatus}
            messages={messages}
          />
        </div>
      </div>
    </div>
  )
}