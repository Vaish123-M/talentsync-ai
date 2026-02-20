"""Intent detection for recruiter assistant queries."""
from typing import Literal


AssistantIntent = Literal['search', 'filter', 'recommendation', 'guidance']


def detect_intent(query: str) -> AssistantIntent:
    """Detect query intent using lightweight keyword heuristics."""
    lowered = (query or '').lower()

    recommendation_terms = ['similar to', 'similar candidates', 'recommend', 'like john', 'like ']
    if any(term in lowered for term in recommendation_terms):
        return 'recommendation'

    search_terms = ['find', 'show', 'search', 'top', 'best', 'developers', 'engineers']
    has_search_signal = any(term in lowered for term in search_terms)

    filter_terms = ['between', 'years', 'experience', 'only', 'without', 'at least', 'minimum']
    has_filter_signal = any(term in lowered for term in filter_terms)

    if has_filter_signal and has_search_signal:
        return 'filter'

    if has_search_signal:
        return 'search'

    if has_filter_signal:
        return 'filter'

    return 'guidance'
