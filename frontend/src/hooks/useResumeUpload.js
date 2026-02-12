import { useState } from 'react';
import resumeService from '../services/resumeService';

const useResumeUpload = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  const handleFileSelection = (files) => {
    setSelectedFiles(files);
    setError(null);
    setResults(null);
    setProgress(0);
  };

  const uploadResumes = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select files to upload');
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      const response = await resumeService.uploadResumes(
        selectedFiles,
        (progressValue) => {
          setProgress(progressValue);
        }
      );

      setResults(response);
      setSelectedFiles([]);
      setProgress(100);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to upload resumes');
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setSelectedFiles([]);
    setLoading(false);
    setProgress(0);
    setError(null);
    setResults(null);
  };

  return {
    selectedFiles,
    loading,
    progress,
    error,
    results,
    handleFileSelection,
    uploadResumes,
    reset,
  };
};

export default useResumeUpload;
