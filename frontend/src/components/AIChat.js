import React, { useMemo, useState } from 'react';
import aiService from '../services/aiService';

const SUGGESTED_QUERIES = [
	'Show me top Python backend developers with 3-5 years experience',
	'Find candidates similar to Jane Doe',
	'Top 5 React developers with API experience',
];

const AIChat = () => {
	const [messages, setMessages] = useState([
		{
			role: 'assistant',
			text: 'Ask me to search, filter, or recommend candidates using natural language.',
			candidates: [],
		},
	]);
	const [query, setQuery] = useState('');
	const [loading, setLoading] = useState(false);
	const recruiterId = useMemo(() => 'default', []);

	const handleSubmit = async (event) => {
		event.preventDefault();
		const trimmed = query.trim();
		if (!trimmed || loading) {
			return;
		}

		const userMessage = { role: 'user', text: trimmed, candidates: [] };
		setMessages((prev) => [...prev, userMessage]);
		setQuery('');
		setLoading(true);

		try {
			const data = await aiService.queryAssistant({
				query: trimmed,
				recruiterId,
				topK: 5,
			});

			setMessages((prev) => [
				...prev,
				{
					role: 'assistant',
					text: data.message,
					candidates: data.candidates || [],
					latencyMs: data.latency_ms,
				},
			]);
		} catch (error) {
			setMessages((prev) => [
				...prev,
				{
					role: 'assistant',
					text: error.message || 'AI assistant is unavailable right now. Please try again.',
					candidates: [],
				},
			]);
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="bg-white rounded-lg shadow-soft p-6">
			<div className="flex items-center justify-between mb-4">
				<h2 className="text-xl font-semibold text-gray-900">Recruiter AI Assistant</h2>
				{loading && <span className="text-sm text-primary-600">Thinking...</span>}
			</div>

			<div className="border border-gray-200 rounded-lg p-4 h-96 overflow-y-auto bg-gray-50 space-y-4">
				{messages.map((message, idx) => (
					<div key={idx} className={message.role === 'user' ? 'text-right' : 'text-left'}>
						<div
							className={`inline-block max-w-[90%] px-4 py-3 rounded-lg text-sm ${
								message.role === 'user'
									? 'bg-primary-600 text-white'
									: 'bg-white text-gray-800 border border-gray-200'
							}`}
						>
							<p>{message.text}</p>
							{typeof message.latencyMs === 'number' && (
								<p className="text-xs text-gray-500 mt-2">Latency: {message.latencyMs} ms</p>
							)}

							{message.candidates && message.candidates.length > 0 && (
								<div className="mt-3 space-y-2 text-left">
									{message.candidates.slice(0, 3).map((candidate) => (
										<div key={candidate.id} className="p-3 bg-gray-50 rounded border border-gray-200">
											<p className="font-medium text-gray-900">{candidate.name}</p>
											<p className="text-xs text-gray-600 mt-1">Match: {candidate.match_score ?? 'N/A'}</p>
											{candidate.reasoning && candidate.reasoning.length > 0 && (
												<ul className="mt-2 text-xs text-gray-600 list-disc pl-4">
													{candidate.reasoning.map((reason, rIdx) => (
														<li key={rIdx}>{reason}</li>
													))}
												</ul>
											)}
										</div>
									))}
								</div>
							)}
						</div>
					</div>
				))}
			</div>

			<form onSubmit={handleSubmit} className="mt-4 space-y-3">
				<div className="flex gap-2">
					<input
						type="text"
						value={query}
						onChange={(event) => setQuery(event.target.value)}
						placeholder="Ask candidate search questions in plain English..."
						className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
						disabled={loading}
					/>
					<button
						type="submit"
						disabled={loading || !query.trim()}
						className={`px-4 py-2 rounded-lg font-medium ${
							loading || !query.trim()
								? 'bg-gray-300 text-gray-500 cursor-not-allowed'
								: 'bg-primary-600 hover:bg-primary-700 text-white'
						}`}
					>
						Send
					</button>
				</div>

				<div className="flex flex-wrap gap-2">
					{SUGGESTED_QUERIES.map((item) => (
						<button
							key={item}
							type="button"
							onClick={() => setQuery(item)}
							className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full"
						>
							{item}
						</button>
					))}
				</div>
			</form>
		</div>
	);
};

export default AIChat;
