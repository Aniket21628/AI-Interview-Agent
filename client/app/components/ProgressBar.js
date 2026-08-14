'use client'

import { motion } from 'framer-motion'

export default function ProgressBar({ current, max, phase }) {
  const progress = Math.min((current / max) * 100, 100)
  
  const getPhaseColor = (phase) => {
    switch (phase) {
      case 'greeting':
      case 'introduction':
        return 'bg-blue-500'
      case 'technical':
        return 'bg-purple-500'
      case 'behavioral':
        return 'bg-green-500'
      case 'closing':
        return 'bg-orange-500'
      default:
        return 'bg-primary-500'
    }
  }

  const getPhaseLabel = (phase) => {
    switch (phase) {
      case 'greeting':
        return 'Welcome'
      case 'introduction':
        return 'Introduction'
      case 'technical':
        return 'Technical Questions'
      case 'behavioral':
        return 'Behavioral Questions'
      case 'closing':
        return 'Closing'
      default:
        return 'Interview'
    }
  }

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-700">
              Interview Progress
            </span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${getPhaseColor(phase)}`}>
              {getPhaseLabel(phase)}
            </span>
          </div>
          <span className="text-sm text-gray-500">
            {current} of {max} questions
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <motion.div
            className={`h-2 rounded-full ${getPhaseColor(phase)}`}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
        
        {/* Phase Indicators */}
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span className={phase === 'introduction' ? 'text-blue-600 font-medium' : ''}>
            Introduction
          </span>
          <span className={phase === 'technical' ? 'text-purple-600 font-medium' : ''}>
            Technical
          </span>
          <span className={phase === 'behavioral' ? 'text-green-600 font-medium' : ''}>
            Behavioral
          </span>
          <span className={phase === 'closing' ? 'text-orange-600 font-medium' : ''}>
            Closing
          </span>
        </div>
      </div>
    </div>
  )
}