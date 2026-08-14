'use client'

import { motion } from 'framer-motion'
import { 
  UserIcon, 
  BriefcaseIcon, 
  ClockIcon,
  ChatBubbleLeftRightIcon,
  AcademicCapIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

export default function InterviewStats({ candidateProfile, interviewStatus, messages }) {
  const userMessages = messages.filter(m => m.role === 'user')
  const assistantMessages = messages.filter(m => m.role === 'assistant')
  
  // Calculate average response length
  const avgResponseLength = userMessages.length > 0 
    ? Math.round(userMessages.reduce((sum, msg) => sum + msg.content.length, 0) / userMessages.length)
    : 0

  // Calculate interview duration (mock - in real app would track actual time)
  const interviewDuration = Math.max(1, Math.floor(messages.length * 1.5)) // Rough estimate

  const stats = [
    {
      label: 'Questions Asked',
      value: interviewStatus.questionCount,
      icon: ChatBubbleLeftRightIcon,
      color: 'text-blue-600'
    },
    {
      label: 'Responses Given',
      value: userMessages.length,
      icon: UserIcon,
      color: 'text-green-600'
    },
    {
      label: 'Avg Response Length',
      value: `${avgResponseLength} chars`,
      icon: ChartBarIcon,
      color: 'text-purple-600'
    },
    {
      label: 'Duration',
      value: `${interviewDuration} min`,
      icon: ClockIcon,
      color: 'text-orange-600'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Candidate Profile */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Candidate Profile</h3>
        <div className="space-y-3">
          <div className="flex items-center">
            <UserIcon className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-900">{candidateProfile.name}</p>
              <p className="text-xs text-gray-500">Full Name</p>
            </div>
          </div>
          
          <div className="flex items-center">
            <BriefcaseIcon className="w-5 h-5 text-gray-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-900">{candidateProfile.position}</p>
              <p className="text-xs text-gray-500">Position</p>
            </div>
          </div>
          
          {candidateProfile.experience && (
            <div className="flex items-center">
              <AcademicCapIcon className="w-5 h-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">{candidateProfile.experience} years</p>
                <p className="text-xs text-gray-500">Experience</p>
              </div>
            </div>
          )}
          
          {candidateProfile.skills && candidateProfile.skills.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">Skills</p>
              <div className="flex flex-wrap gap-1">
                {candidateProfile.skills.map((skill, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Interview Statistics */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Interview Statistics</h3>
        <div className="grid grid-cols-2 gap-4">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gray-50 rounded-lg p-3"
            >
              <div className="flex items-center justify-between">
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
                <span className="text-lg font-semibold text-gray-900">
                  {stat.value}
                </span>
              </div>
              <p className="text-xs text-gray-600 mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Current Phase */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Phase</h3>
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-primary-900 capitalize">
              {interviewStatus.phase.replace('_', ' ')}
            </span>
            <span className="text-xs text-primary-600">
              {Math.round((interviewStatus.questionCount / interviewStatus.maxQuestions) * 100)}% Complete
            </span>
          </div>
          
          <div className="w-full bg-primary-200 rounded-full h-2">
            <motion.div
              className="bg-primary-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ 
                width: `${(interviewStatus.questionCount / interviewStatus.maxQuestions) * 100}%` 
              }}
              transition={{ duration: 0.5 }}
            />
          </div>
          
          <p className="text-xs text-primary-700 mt-2">
            {interviewStatus.complete 
              ? 'Interview completed successfully!'
              : `${interviewStatus.maxQuestions - interviewStatus.questionCount} questions remaining`
            }
          </p>
        </div>
      </div>

      {/* Tips */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Interview Tips</h3>
        <div className="space-y-3">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <h4 className="text-sm font-medium text-blue-900 mb-1">Voice Input</h4>
            <p className="text-xs text-blue-700">
              Speak clearly and at a normal pace. The system will automatically detect when you finish speaking.
            </p>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <h4 className="text-sm font-medium text-green-900 mb-1">Be Specific</h4>
            <p className="text-xs text-green-700">
              Provide concrete examples and details to support your answers.
            </p>
          </div>
          
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <h4 className="text-sm font-medium text-purple-900 mb-1">Ask Questions</h4>
            <p className="text-xs text-purple-700">
              Don't hesitate to ask for clarification if you don't understand a question.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="space-y-2">
          <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            📝 Review my responses
          </button>
          <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            💡 Get interview tips
          </button>
          <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            🔊 Adjust voice settings
          </button>
        </div>
      </div>
    </div>
  )
}