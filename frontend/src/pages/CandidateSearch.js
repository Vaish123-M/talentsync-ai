import React, { useMemo, useState } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';

const CandidateSearch = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [compareIds, setCompareIds] = useState([]);

  const compareCandidates = useMemo(
    () => results.filter((candidate) => compareIds.includes(candidate.id)),
    [compareIds, results]
  );

  const handleSearch = () => {
    // Placeholder for future implementation
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      // Mock results for UI demonstration
      setResults([
        {
          id: 1,
          name: 'John Doe',
          matchScore: 95,
          skills: ['React', 'Node.js', 'Python', 'AWS'],
          experience: '5 years',
          status: 'New',
          score_breakdown: {
            skills_score: 0.92,
            experience_score: 0.9,
            summary_similarity: 0.85,
            semantic_score: 0.88,
          },
          score_reasoning: [
            'Matched skills: react, python, aws',
            'Experience fit score: 0.9',
            'Semantic similarity: 0.88',
          ],
        },
        {
          id: 2,
          name: 'Jane Smith',
          matchScore: 88,
          skills: ['React', 'TypeScript', 'GraphQL'],
          experience: '3 years',
          status: 'Contacted',
          score_breakdown: {
            skills_score: 0.86,
            experience_score: 0.7,
            summary_similarity: 0.82,
            semantic_score: 0.8,
          },
          score_reasoning: [
            'Matched skills: react, graphql',
            'Experience fit score: 0.7',
            'Semantic similarity: 0.8',
          ],
        },
      ]);
    }, 1500);
  };

  const toggleCompare = (candidateId) => {
    setCompareIds((prev) => {
      if (prev.includes(candidateId)) {
        return prev.filter((id) => id !== candidateId);
      }
      if (prev.length >= 2) {
        return [prev[1], candidateId];
      }
      return [...prev, candidateId];
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Candidate Search</h1>
        <p className="text-gray-600 mt-2">
          Search for candidates using natural language queries powered by AI
        </p>
      </div>

      {/* Search Section */}
      <div className="bg-white rounded-lg shadow-soft p-6">
        <div className="space-y-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Search Query
            </label>
            <div className="relative">
              <input
                type="text"
                id="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Find React developers with 2+ years experience"
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <svg
                className="absolute right-4 top-3.5 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleSearch}
              disabled={!query.trim() || loading}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                !query.trim() || loading
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-primary-600 hover:bg-primary-700 text-white'
              }`}
            >
              {loading ? 'Searching...' : 'Search Candidates'}
            </button>

            {results.length > 0 && (
              <button
                onClick={() => {
                  setQuery('');
                  setResults([]);
                }}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Example Queries */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm font-medium text-gray-700 mb-3">Example queries:</p>
          <div className="flex flex-wrap gap-2">
            {[
              'Senior Python developers with ML experience',
              'Frontend engineers with React expertise',
              'Full-stack developers with startup experience',
              'Data scientists with 3+ years experience',
            ].map((example, index) => (
              <button
                key={index}
                onClick={() => setQuery(example)}
                className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-sm text-gray-700 rounded-full transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow-soft p-12">
          <LoadingSpinner size="lg" text="Searching candidates..." />
        </div>
      )}

      {/* Results Section */}
      {!loading && results.length > 0 && (
        <div className="bg-white rounded-lg shadow-soft overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Results ({results.length} candidates found)
            </h2>
          </div>

          {compareCandidates.length === 2 && (
            <div className="p-6 border-b border-gray-200 bg-gray-50">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Candidate Comparison</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {compareCandidates.map((candidate) => (
                  <div key={candidate.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <p className="font-semibold text-gray-900 mb-2">{candidate.name}</p>
                    <p className="text-sm text-gray-600">Match Score: {candidate.matchScore}%</p>
                    <div className="mt-3 text-xs text-gray-600 space-y-1">
                      <p>Skills: {candidate.score_breakdown?.skills_score ?? 'N/A'}</p>
                      <p>Experience: {candidate.score_breakdown?.experience_score ?? 'N/A'}</p>
                      <p>Summary: {candidate.score_breakdown?.summary_similarity ?? 'N/A'}</p>
                      <p>Semantic: {candidate.score_breakdown?.semantic_score ?? 'N/A'}</p>
                    </div>
                    {candidate.score_reasoning && (
                      <ul className="mt-3 text-xs text-gray-600 list-disc pl-4">
                        {candidate.score_reasoning.map((reason, index) => (
                          <li key={index}>{reason}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Candidate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Match Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Skills
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Experience
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((candidate) => (
                  <tr key={candidate.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center">
                          <span className="text-white font-semibold">
                            {candidate.name.charAt(0)}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {candidate.name}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm font-semibold text-primary-600">
                          {candidate.matchScore}%
                        </span>
                        <div className="ml-2 w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary-600 rounded-full"
                            style={{ width: `${candidate.matchScore}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {candidate.skills.slice(0, 3).map((skill, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded"
                          >
                            {skill}
                          </span>
                        ))}
                        {candidate.skills.length > 3 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded">
                            +{candidate.skills.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {candidate.experience}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          candidate.status === 'New'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {candidate.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button className="text-primary-600 hover:text-primary-900 font-medium">
                        View Profile
                      </button>
                      <button
                        onClick={() => toggleCompare(candidate.id)}
                        className={`ml-4 text-sm font-medium ${
                          compareIds.includes(candidate.id)
                            ? 'text-primary-700'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        {compareIds.includes(candidate.id) ? 'Selected' : 'Compare'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && results.length === 0 && !query && (
        <div className="bg-white rounded-lg shadow-soft p-12 text-center">
          <svg
            className="w-16 h-16 text-gray-400 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Start searching</h3>
          <p className="text-gray-600">
            Enter a search query to find the perfect candidates for your role.
          </p>
        </div>
      )}
    </div>
  );
};

export default CandidateSearch;
