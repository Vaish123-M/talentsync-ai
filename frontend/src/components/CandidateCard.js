import React from 'react';

const CandidateCard = ({ candidate }) => {
  const { name, skills, experience_years, summary } = candidate;

  return (
    <div className="bg-white rounded-lg shadow-soft p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center">
            <span className="text-white font-semibold text-lg">
              {name ? name.charAt(0).toUpperCase() : '?'}
            </span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{name || 'Unknown'}</h3>
          </div>
        </div>
      </div>

      {summary && (
        <div className="mb-4">
          <p className="text-sm text-gray-600 line-clamp-3">{summary}</p>
        </div>
      )}

      {skills && skills.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">Skills</h4>
          <div className="flex flex-wrap gap-2">
            {skills.slice(0, 8).map((skill, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded-full"
              >
                {skill}
              </span>
            ))}
            {skills.length > 8 && (
              <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">
                +{skills.length - 8} more
              </span>
            )}
          </div>
        </div>
      )}

      {typeof experience_years === 'number' && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">Experience</h4>
          <p className="text-sm text-gray-600">{experience_years} year(s)</p>
        </div>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
          View Details
        </button>
        <button className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors">
          Contact
        </button>
      </div>
    </div>
  );
};

export default CandidateCard;

