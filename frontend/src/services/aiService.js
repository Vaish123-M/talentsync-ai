import api from './api';

const aiService = {
	queryAssistant: async ({ query, recruiterId = 'default', topK = 5 }) => {
		try {
			const response = await api.post('/api/assistant/query', {
				query,
				recruiter_id: recruiterId,
				top_k: topK,
			});
			return response.data;
		} catch (error) {
			const message = error?.response?.data?.message || 'Failed to query AI assistant';
			throw new Error(message);
		}
	},
};

export default aiService;
