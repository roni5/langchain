import asyncio
from abc import ABC, abstractmethod
from inspect import signature
from typing import List, Optional, Sequence, Union

from langchain_core.document_transformers import BaseDocumentTransformer
from langchain_core.documents import Document
from langchain_core.pydantic_v1 import BaseModel

from langchain.callbacks.manager import Callbacks


class BaseDocumentCompressor(BaseModel, ABC):
    """Base class for document compressors."""

    @abstractmethod
    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """Compress retrieved documents given the query context."""

    async def acompress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """Compress retrieved documents given the query context."""
        return await asyncio.get_running_loop().run_in_executor(
            None, self.compress_documents, documents, query, callbacks
        )


class DocumentCompressorPipeline(BaseDocumentCompressor):
    """Document compressor that uses a pipeline of Transformers."""

    transformers: List[Union[BaseDocumentTransformer, BaseDocumentCompressor]]
    """List of document filters that are chained together and run in sequence."""

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """Transform a list of documents."""
        for _transformer in self.transformers:
            if isinstance(_transformer, BaseDocumentCompressor):
                accepts_callbacks = (
                    signature(_transformer.compress_documents).parameters.get(
                        "callbacks"
                    )
                    is not None
                )
                if accepts_callbacks:
                    documents = _transformer.compress_documents(
                        documents, query, callbacks=callbacks
                    )
                else:
                    documents = _transformer.compress_documents(documents, query)
            elif isinstance(_transformer, BaseDocumentTransformer):
                documents = _transformer.transform_documents(documents)
            else:
                raise ValueError(f"Got unexpected transformer type: {_transformer}")
        return documents

    async def acompress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """Compress retrieved documents given the query context."""
        for _transformer in self.transformers:
            if isinstance(_transformer, BaseDocumentCompressor):
                accepts_callbacks = (
                    signature(_transformer.acompress_documents).parameters.get(
                        "callbacks"
                    )
                    is not None
                )
                if accepts_callbacks:
                    documents = await _transformer.acompress_documents(
                        documents, query, callbacks=callbacks
                    )
                else:
                    documents = await _transformer.acompress_documents(documents, query)
            elif isinstance(_transformer, BaseDocumentTransformer):
                documents = await _transformer.atransform_documents(documents)
            else:
                raise ValueError(f"Got unexpected transformer type: {_transformer}")
        return documents
