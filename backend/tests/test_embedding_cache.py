"""Embedding service cache tests."""
import pytest
from app.vector_db.embeddings import EmbeddingService


def test_embedding_cache_hit():
	"""Test that embedding cache reuses vectors for identical text."""
	service = EmbeddingService()
	if not service.available:
		pytest.skip('Sentence-transformers not available')

	texts = ['Hello world', 'Hello world', 'Goodbye world']
	embeddings = service.embed_texts(texts)

	assert embeddings is not None
	assert len(embeddings) == 3
	# Same text should produce identical embeddings
	assert embeddings[0] == embeddings[1]
	# Different text should produce different embeddings
	assert embeddings[0] != embeddings[2]


def test_embedding_cache_size_limit():
	"""Test that embedding cache enforces maximum size."""
	service = EmbeddingService()
	if not service.available:
		pytest.skip('Sentence-transformers not available')

	original_max = service._cache_max_size
	service._cache_max_size = 5

	for i in range(10):
		service.embed_text(f'Text {i}')

	assert len(service._cache) <= 5
	service._cache_max_size = original_max


def test_embedding_single_vs_batch():
	"""Test that single and batch embedding produce same results."""
	service = EmbeddingService()
	if not service.available:
		pytest.skip('Sentence-transformers not available')

	text = 'Machine learning and NLP'
	single = service.embed_text(text)
	batch = service.embed_texts([text])[0] if service.embed_texts([text]) else None

	assert single is not None
	assert batch is not None
	assert single == batch
