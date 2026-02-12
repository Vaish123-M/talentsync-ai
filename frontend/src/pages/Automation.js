import React, { useState } from 'react';

const Automation = () => {
  const [emailTemplate, setEmailTemplate] = useState(
    `Hi [Candidate Name],

We came across your profile and were impressed by your experience with [Skills]. We have an exciting opportunity that aligns well with your background.

Would you be interested in discussing this role further?

Best regards,
HR Team`
  );

  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [sending, setSending] = useState(false);

  const mockCandidates = [
    { id: 1, name: 'John Doe', email: 'john@example.com', skills: 'React, Node.js' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', skills: 'Python, Django' },
    { id: 3, name: 'Mike Johnson', email: 'mike@example.com', skills: 'Java, Spring' },
  ];

  const handleSendEmails = () => {
    setSending(true);
    // Mock sending emails
    setTimeout(() => {
      setSending(false);
      alert(`Emails sent to ${selectedCandidates.length} candidate(s)`);
      setSelectedCandidates([]);
    }, 2000);
  };

  const toggleCandidate = (id) => {
    if (selectedCandidates.includes(id)) {
      setSelectedCandidates(selectedCandidates.filter((cId) => cId !== id));
    } else {
      setSelectedCandidates([...selectedCandidates, id]);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Email Automation</h1>
        <p className="text-gray-600 mt-2">
          Automate your candidate outreach with AI-powered email templates
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Email Template Editor */}
        <div className="bg-white rounded-lg shadow-soft p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Email Template</h2>
            <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              Use AI Template
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject Line
              </label>
              <input
                type="text"
                placeholder="Exciting Opportunity at [Company Name]"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Message Body
              </label>
              <textarea
                value={emailTemplate}
                onChange={(e) => setEmailTemplate(e.target.value)}
                rows={12}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Available Placeholders:</strong>
                <br />
                [Candidate Name], [Skills], [Experience], [Company Name]
              </p>
            </div>
          </div>
        </div>

        {/* Email Preview */}
        <div className="bg-white rounded-lg shadow-soft p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Preview</h2>

          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center space-x-2 text-sm">
                <span className="text-gray-500">To:</span>
                <span className="text-gray-900">candidate@example.com</span>
              </div>
              <div className="flex items-center space-x-2 text-sm mt-1">
                <span className="text-gray-500">Subject:</span>
                <span className="text-gray-900">Exciting Opportunity</span>
              </div>
            </div>

            <div className="p-6 bg-white">
              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-line text-gray-700">{emailTemplate}</p>
              </div>
            </div>
          </div>

          <div className="mt-6 space-y-3">
            <button className="w-full px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors">
              Save Template
            </button>
            <button className="w-full px-4 py-3 border-2 border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors">
              Load Template
            </button>
          </div>
        </div>
      </div>

      {/* Candidate Selection */}
      <div className="bg-white rounded-lg shadow-soft p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Recipients</h2>

        <div className="space-y-3">
          {mockCandidates.map((candidate) => (
            <div
              key={candidate.id}
              className={`flex items-center justify-between p-4 border-2 rounded-lg cursor-pointer transition-all ${
                selectedCandidates.includes(candidate.id)
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => toggleCandidate(candidate.id)}
            >
              <div className="flex items-center space-x-4">
                <input
                  type="checkbox"
                  checked={selectedCandidates.includes(candidate.id)}
                  onChange={() => toggleCandidate(candidate.id)}
                  className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <div>
                  <p className="font-medium text-gray-900">{candidate.name}</p>
                  <p className="text-sm text-gray-500">{candidate.email}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">{candidate.skills}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            {selectedCandidates.length} candidate(s) selected
          </p>
          <button
            onClick={handleSendEmails}
            disabled={selectedCandidates.length === 0 || sending}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              selectedCandidates.length === 0 || sending
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {sending ? 'Sending...' : 'Send Emails'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-soft p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Emails Sent Today</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">0</p>
            </div>
            <svg
              className="w-12 h-12 text-primary-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-soft p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Response Rate</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">0%</p>
            </div>
            <svg
              className="w-12 h-12 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-soft p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Campaigns</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">0</p>
            </div>
            <svg
              className="w-12 h-12 text-orange-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Automation;
