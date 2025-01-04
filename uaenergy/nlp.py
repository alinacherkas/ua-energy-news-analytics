"""
Functions for running natural language processing on website articles.
"""

from dataclasses import dataclass
from spacy.tokens import Doc


__all__ = ["extract_entities"]


@dataclass
class NamedEntity:
    """
    Named entity object with context.
    """

    name: str
    lemma: str
    label: str
    context: list[str]


def extract_entities(doc: Doc, context_size: int = 2) -> list[NamedEntity]:
    """
    Extract named entities from a document.

    Parameters
    ----------
    doc : Doc
        SpaCy document object.
    context_size: int
        Number of sentences before and after the entity to include as a context.

    Returns
    -------
    list[NamedEntity]
        List of named entity objects with context.
    """
    entities = []
    # token indices that denote the start and end of each sentence
    indices = [(sentence.start, sentence.end) for sentence in doc.sents]
    for index, (start, end) in enumerate(indices):
        for entity in doc[start:end].ents:
            if entity.label_ not in {"ORG", "PER", "LOC"}:
                continue
            index_start = max(index - context_size, 0)
            start, _ = indices[index_start]
            index_end = min(index + context_size, len(indices) - 1)
            _, end = indices[index_end]
            entity = NamedEntity(
                name=entity.text,
                lemma=entity.lemma_,
                label=entity.label_,
                context=list(doc[start:end].sents),
            )
            entities.append(entity)
    return entities
