'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { MicrophoneIcon, StopIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline'

const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL || 'http://localhost:5000'

export default function VoiceControls({ onVoiceMessage, disabled }) {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState('')
  const [recognitionSupported, setRecognitionSupported] = useState(false)

  const transcriptRef = useRef('')
  const recognitionRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    setRecognitionSupported(Boolean(SpeechRecognition))

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onresult = null
        recognitionRef.current.onend = null
        recognitionRef.current.onerror = null
        recognitionRef.current.stop()
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  const resetVoiceState = () => {
    chunksRef.current = []
    transcriptRef.current = ''
    setTranscript('')
  }

  const sendTextToApp = (text) => {
    const cleanText = text?.trim()
    if (!cleanText) return

    onVoiceMessage?.(cleanText)
    resetVoiceState()
  }

  const startWebSpeechCapture = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('This browser does not support Web Speech API. Falling back to microphone upload.')
      return startFallbackCapture()
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setError('')
      setIsListening(true)
      resetVoiceState()
    }

    recognition.onresult = (event) => {
      let finalText = ''
      let interim = ''

      for (let i = 0; i < event.results.length; i += 1) {
        const result = event.results[i]
        const text = result[0]?.transcript || ''

        if (result.isFinal) {
          finalText += `${text} `
        } else {
          interim += `${text} `
        }
      }

      const currentText = (finalText || interim).trim()
      transcriptRef.current = currentText
      setTranscript(currentText)
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setError(`Speech recognition failed: ${event.error}. Please try again.`)
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
      if (!transcriptRef.current.trim()) {
        setError('No transcript captured. Please speak again.')
      }
    }

    recognitionRef.current = recognition
    recognition.start()
  }

  const startFallbackCapture = () => {
    setError('Speech Recognition API is not supported in this browser. Please use Chrome, Edge, or Safari.')
    setIsListening(false)
  }

  const startListening = () => {
    if (disabled) return

    if (recognitionSupported) {
      startWebSpeechCapture()
      return
    }

    startFallbackCapture()
  }

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      return
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }

    setIsListening(false)
  }

  const handleManualSend = () => {
    const value = transcriptRef.current.trim()
    if (!value) {
      setError('There is no transcript ready to send yet.')
      return
    }

    sendTextToApp(value)
  }

  if (isProcessing) {
    return (
      <div className="flex items-center justify-center p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-2" />
        <span className="text-sm text-blue-800">Processing your voice response...</span>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-700">Voice Input</h3>
        {isListening && (
          <div className="flex items-center text-red-600">
            <div className="w-2 h-2 bg-red-600 rounded-full mr-1" />
            <span className="text-xs">Listening...</span>
          </div>
        )}
      </div>

      {transcript && (
        <div className="mb-4 p-3 bg-white border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-900">{transcript}</p>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="flex items-center justify-center space-x-3">
        {!isListening ? (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={startListening}
            disabled={disabled || isProcessing}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-full text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <MicrophoneIcon className="w-5 h-5 mr-2" />
            Start Speaking
          </motion.button>
        ) : (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={stopListening}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-full text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <StopIcon className="w-5 h-5 mr-2" />
            Stop
          </motion.button>
        )}

        {transcript && !isListening && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleManualSend}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-full text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <PaperAirplaneIcon className="w-5 h-5 mr-2" />
            Send Now
          </motion.button>
        )}
      </div>

      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500">
          {recognitionSupported
            ? 'Using browser speech recognition for fast live transcription.'
            : 'Speech recognition is unavailable; using microphone fallback.'}
        </p>
      </div>
    </div>
  )
}