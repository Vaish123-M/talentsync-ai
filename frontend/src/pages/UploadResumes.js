import React, { useState } from 'react';
import FileUploader from '../components/FileUploader';
import ProgressBar from '../components/ProgressBar';
import LoadingSpinner from '../components/LoadingSpinner';
import CandidateCard from '../components/CandidateCard';
import NotificationToast from '../components/NotificationToast';
import useResumeUpload from '../hooks/useResumeUpload';

const UploadResumes = () => {
  const {
    selectedFiles,
    loading,
    progress,
    error,
    results,
    handleFileSelection,
    uploadResumes,
    reset,
  } = useResumeUpload();

  const [notification, setNotification] = useState(null);

  const handleFilesSelected = (files) => {
    handleFileSelection(files);
  };

  const handleUpload = async () => {
    await uploadResumes();
  };

  const handleRemoveFile = (index) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    handleFileSelection(newFiles);
  };

  React.useEffect(() => {
    if (results && results.candidates) {
      setNotification({
        type: 'success',
        message: `Successfully uploaded ${results.candidates.length} resume(s)`,
      });
    }
  }, [results]);

  React.useEffect(() => {
    if (error) {
      setNotification({
        type: 'error',
        message: error,
      });
    }
  }, [error]);

  return (
    <div className="space-y-6">
      {notification && (
        <NotificationToast
          type={notification.type}
          message={notification.message}
          onClose={() => setNotification(null)}
        />
      )}

      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Resumes</h1>
        <p className="text-gray-600 mt-2">
          Upload candidate resumes in PDF format. Our AI will automatically extract key information.
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-soft p-6">
        <FileUploader
          onFilesSelected={handleFilesSelected}
          accept=".pdf"
          multiple={true}
        />

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Selected Files ({selectedFiles.length})
            </h3>
            <div className="space-y-2">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <svg
                      className="w-8 h-8 text-red-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="text-red-500 hover:text-red-700"
                    disabled={loading}
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>

            {/* Upload Button */}
            <div className="mt-4 flex items-center space-x-4">
              <button
                onClick={handleUpload}
                disabled={loading || selectedFiles.length === 0}
                className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                  loading || selectedFiles.length === 0
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-primary-600 hover:bg-primary-700 text-white'
                }`}
              >
                {loading ? 'Uploading...' : 'Upload Resumes'}
              </button>

              {selectedFiles.length > 0 && !loading && (
                <button
                  onClick={reset}
                  className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Clear All
                </button>
              )}
            </div>

            {/* Progress Bar */}
            {loading && (
              <div className="mt-4">
                <ProgressBar progress={progress} />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow-soft p-12">
          <LoadingSpinner size="lg" text="Processing resumes..." />
        </div>
      )}

      {/* Results Section */}
      {results && results.candidates && results.candidates.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">
              Parsed Candidates ({results.candidates.length})
            </h2>
            <button
              onClick={reset}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Upload More
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.candidates.map((candidate, index) => (
              <CandidateCard key={index} candidate={candidate} />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !results && selectedFiles.length === 0 && (
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No resumes uploaded yet</h3>
          <p className="text-gray-600">
            Upload your first resume to get started with AI-powered candidate parsing.
          </p>
        </div>
      )}
    </div>
  );
};

export default UploadResumes;
