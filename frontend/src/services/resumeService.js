import api from './api';

export const resumeService = {
  /**
   * Upload multiple resume files
   * @param {File[]} files - Array of PDF files
   * @param {Function} onProgress - Progress callback function
   * @returns {Promise} - Response with parsed candidates
   */
  uploadResumes: async (files, onProgress) => {
    const formData = new FormData();
    
    files.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const response = await api.post('/upload-resumes', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          if (onProgress) {
            onProgress(percentCompleted);
          }
        },
      });

      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Search candidates by query (placeholder for future implementation)
   * @param {string} query - Search query
   * @returns {Promise}
   */
  searchCandidates: async (query) => {
    try {
      const response = await api.post('/search-candidates', { query });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

export default resumeService;
