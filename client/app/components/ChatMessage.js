'use client'

import { motion } from 'framer-motion'
import { UserIcon, CpuChipIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'

export default function ChatMessage({ message, isLatest }) {
  const isUser = message.role === 'user'
  const timestamp = new Date(message.timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })

  const messageVariants = {
    hidden: { opacity: 0, y: 20, scale: 0.95 },
    visible: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: {
        duration: 0.3,
        ease: "easeOut"
      }
    }
  }

  return (
    <motion.div
      variants={messageVariants}
      initial="hidden"
      animate="visible"
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex max-w-3xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-primary-600 text-white' 
              : 'bg-gray-100 text-gray-600'
          }`}>
            {isUser ? (
              <UserIcon className="w-5 h-5" />
            ) : (
              <CpuChipIcon className="w-5 h-5" />
            )}
          </div>
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          {/* Message Bubble */}
          <div className={`chat-message ${isUser ? 'user' : 'assistant'} ${
            isLatest ? 'shadow-lg' : 'shadow-sm'
          }`}>
            <div className="flex items-start justify-between mb-2">
              <span className={`text-xs font-medium ${
                isUser ? 'text-primary-700' : 'text-gray-500'
              }`}>
                {isUser ? 'You' : 'AI Interviewer'}
              </span>
              <span className={`text-xs ml-2 ${
                isUser ? 'text-primary-600' : 'text-gray-400'
              }`}>
                {timestamp}
              </span>
            </div>
            
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>

            {/* Evaluation Display */}
            {message.evaluation && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 pt-3 border-t border-gray-200"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-gray-600">
                    Response Evaluation
                  </span>
                  <div className="flex items-center">
                    {message.evaluation.quality === 'good' ? (
                      <CheckCircleIcon className="w-4 h-4 text-green-500 mr-1" />
                    ) : (
                      <XCircleIcon className="w-4 h-4 text-yellow-500 mr-1" />
                    )}
                    <span className="text-xs text-gray-600">
                      Score: {message.evaluation.score}/10
                    </span>
                  </div>
                </div>
                
                {message.evaluation.keyPoints && message.evaluation.keyPoints.length > 0 && (
                  <div className="mb-2">
                    <span className="text-xs font-medium text-gray-600 block mb-1">
                      Key Points:
                    </span>
                    <ul className="text-xs text-gray-600 space-y-1">
                      {message.evaluation.keyPoints.map((point, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-primary-500 mr-1">•</span>
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {message.evaluation.feedback && (
                  <p className="text-xs text-gray-600 italic">
                    "{message.evaluation.feedback}"
                  </p>
                )}
              </motion.div>
            )}
          </div>

          {/* Typing Indicator */}
          {isLatest && !isUser && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center mt-2 text-xs text-gray-500"
            >
              <div className="flex space-x-1 mr-2">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                  className="w-1 h-1 bg-gray-400 rounded-full"
                />
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                  className="w-1 h-1 bg-gray-400 rounded-full"
                />
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                  className="w-1 h-1 bg-gray-400 rounded-full"
                />
              </div>
              AI is thinking...
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  )
}