'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { 
  MicrophoneIcon, 
  StopIcon,
  SpeakerWaveIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

export default function VoiceControls({ onVoiceMessage, disabled }) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [isSupported, setIsSupported] = useState(false)
  const [error, setError] = useState('')
  const [audioLevel, setAudioLevel] = useState(0)

  const recognitionRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const microphoneRef = useRef(null)
  const animationFrameRef = useRef(null)
  const submittedTranscriptRef = useRef('')

  useEffect(() => {
    // Check for Web Speech API support
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        setIsSupported(true)
        initializeSpeechRecognition(SpeechRecognition)
      } else {
        setError('Speech recognition is not supported in this browser')
      }
    }

    return () => {
      cleanup()
    }
  }, [])

  const initializeSpeechRecognition = (SpeechRecognition) => {
    const recognition = new SpeechRecognition()
    
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setIsListening(true)
      setError('')
      console.log('Speech recognition started')
    }

    recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const currentTranscript = event.results[i][0].transcript

        if (event.results[i].isFinal) {
          finalTranscript += currentTranscript + ' '
        } else {
          interimTranscript += currentTranscript
        }
      }

      const cleanedFinal = finalTranscript.trim()
      setTranscript(prev => `${prev} ${cleanedFinal}`.trim())
      setInterimTranscript(interimTranscript.trim())

      if (cleanedFinal && cleanedFinal !== submittedTranscriptRef.current) {
        submittedTranscriptRef.current = cleanedFinal
        setTimeout(() => {
          handleSendTranscript(cleanedFinal)
        }, 400)
      }
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setError(`Speech recognition error: ${event.error}`)
      setIsListening(false)
      cleanup()
    }

    recognition.onend = () => {
      setIsListening(false)
      setInterimTranscript('')
      console.log('Speech recognition ended')
    }

    recognitionRef.current = recognition
  }

  const startListening = async () => {
    if (!isSupported || disabled) return

    try {
      // Request microphone permission and start audio level monitoring
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      await initializeAudioContext(stream)
      
      // Start speech recognition
      if (recognitionRef.current) {
        submittedTranscriptRef.current = ''
        setTranscript('')
        setInterimTranscript('')
        setError('')
        recognitionRef.current.start()
      }
    } catch (err) {
      console.error('Error starting voice recognition:', err)
      setError('Microphone access denied or not available')
    }
  }

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
    }
    cleanup()
  }

  const initializeAudioContext = async (stream) => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const analyser = audioContext.createAnalyser()
      const microphone = audioContext.createMediaStreamSource(stream)
      
      analyser.smoothingTimeConstant = 0.8
      analyser.fftSize = 1024
      
      microphone.connect(analyser)
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      microphoneRef.current = microphone
      
      monitorAudioLevel()
    } catch (err) {
      console.error('Error initializing audio context:', err)
    }
  }

  const monitorAudioLevel = () => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    
    const updateLevel = () => {
      if (!isListening) return

      analyserRef.current.getByteFrequencyData(dataArray)
      
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length
      const normalizedLevel = Math.min(average / 128, 1)
      
      setAudioLevel(normalizedLevel)
      
      animationFrameRef.current = requestAnimationFrame(updateLevel)
    }
    
    updateLevel()
  }

  const cleanup = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
    
    setAudioLevel(0)
  }

  const handleSendTranscript = (text) => {
    if (text && onVoiceMessage) {
      onVoiceMessage(text)
      setTranscript('')
      setInterimTranscript('')
      stopListening()
    }
  }

  const handleManualSend = () => {
    const fullText = (transcript + interimTranscript).trim()
    if (fullText) {
      handleSendTranscript(fullText)
    }
  }

  if (!isSupported) {
    return (
      <div className="flex items-center justify-center p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 mr-2" />
        <span className="text-sm text-yellow-800">
          Voice input is not supported in this browser
        </span>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-700">Voice Input</h3>
        <div className="flex items-center space-x-2">
          {isListening && (
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="flex items-center text-red-600"
            >
              <div className="w-2 h-2 bg-red-600 rounded-full mr-1"></div>
              <span className="text-xs">Listening...</span>
            </motion.div>
          )}
        </div>
      </div>

      {/* Voice Visualization */}
      {isListening && (
        <div className="flex items-center justify-center mb-4">
          <div className="flex items-end space-x-1 h-8">
            {[...Array(5)].map((_, i) => (
              <motion.div
                key={i}
                className="voice-wave"
                style={{
                  height: `${Math.max(4, audioLevel * 32 + Math.random() * 8)}px`,
                }}
                animate={{
                  height: [
                    `${Math.max(4, audioLevel * 32)}px`,
                    `${Math.max(4, audioLevel * 32 + 16)}px`,
                    `${Math.max(4, audioLevel * 32)}px`,
                  ],
                }}
                transition={{
                  duration: 0.5 + i * 0.1,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Transcript Display */}
      {(transcript || interimTranscript) && (
        <div className="mb-4 p-3 bg-white border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-900">
            {transcript}
            <span className="text-gray-500 italic">{interimTranscript}</span>
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center justify-center space-x-4">
        {!isListening ? (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={startListening}
            disabled={disabled}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-full text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <MicrophoneIcon className="w-5 h-5 mr-2" />
            Start Speaking
          </motion.button>
        ) : (
          <div className="flex space-x-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={stopListening}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-full text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <StopIcon className="w-5 h-5 mr-2" />
              Stop
            </motion.button>
            
            {(transcript || interimTranscript) && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleManualSend}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-full text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                Send Now
              </motion.button>
            )}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500">
          {isListening 
            ? "Speak clearly into your microphone. I'll automatically send your response when you finish speaking."
            : "Click 'Start Speaking' and answer the question using your voice."
          }
        </p>
      </div>
    </div>
  )
}