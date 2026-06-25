from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

persist_directory = 'db'

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}, # oppure "cuda"
    encode_kwargs={"normalize_embeddings": True}
)
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
print(vectordb._collection.count())

# Similarity Search
text = [
     """The Amanita phalloides has a large and imposing epigeous (aboveground) fruiting body (basidiocarp).""",
    """A mushroom with a large fruiting body is the Amanita phalloides. Some varieties are all-white.""",
    """A. phalloides, a.k.a Death Cap, is one of the most poisonous of all known mushrooms.""",
]

smalldb = Chroma.from_texts(text, embedding)
question = "Tell me about all-white mushrooms with large fruiting bodies"
smalldb.similarity_search(question, k=2)
print(smalldb.similarity_search(question, k=2))

#MMR 
print(smalldb.max_marginal_relevance_search(question,k=2, fetch_k=3)) #fetch k = 3 fetch all 3 documents, but return only 2 that are most relevant and diverse

#Back to real Data
question = "What is the main topic of the CBOM paper?"
docs_ss = vectordb.similarity_search(question, k=3)
print(docs_ss[0].page_content)

#now we do MMR with the real data
docs_mmr = vectordb.max_marginal_relevance_search(question,k=3)
print(docs_mmr[0].page_content)


#now let's do a similarity search with a filter
question = "What is the main topic of the CBOM paper?"
docs = vectordb.similarity_search(question, k=3, filter={"source": "CBOM"})
for d in docs:
    print(d.metadata)

#working with metadata using self-query retriever
"""
To address this, we can use SelfQueryRetriever, which uses an LLM to extract:

The query string to use for vector search
A metadata filter to pass in as well
Most vector databases support metadata filters, so this doesn't require any new databases or indexes.
"""

from langchain_huggingface import HuggingFacePipeline, ChatHuggingFace
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_classic.chains.query_constructor.base import AttributeInfo

# LLM locale via HuggingFace (al posto di OpenAI).
# flan-t5 non riesce a produrre il JSON strutturato richiesto da SelfQueryRetriever:
# serve un modello instruct piu' capace. Lo definiamo UNA volta e lo riusiamo sotto.
_pipeline = HuggingFacePipeline.from_model_id(
    model_id="Qwen/Qwen2.5-3B-Instruct",
    task="text-generation",
    pipeline_kwargs={"max_new_tokens": 512, "do_sample": False, "return_full_text": False},
)
# ChatHuggingFace applica il chat template del modello: indispensabile per i modelli instruct.
chat_model = ChatHuggingFace(llm=_pipeline)

# Descrizione dei metadati su cui il retriever può filtrare
metadata_field_info = [
    AttributeInfo(
        name="source",
        description="La fonte del documento, es. 'CBOM'",
        type="string",
    ),
    AttributeInfo(
        name="page",
        description="Il numero di pagina del documento",
        type="integer",
    ),
]
document_content_description = "Documenti tecnici su crittografia post-quantum"

retriever = SelfQueryRetriever.from_llm(
    chat_model,
    vectordb,
    document_content_description,
    metadata_field_info,
    verbose=True,
)

question = "What is the main topic of the CBOM paper?"
docs = retriever.invoke(question)
for d in docs:
    print(d.metadata)
    print(d.page_content)

#Compression
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor

def pretty_print_docs(docs):
    print(f"\n{'-' * 100}\n".join([f"Document {i+1}:\n\n" + d.page_content for i, d in enumerate(docs)]))
    
# Wrap our vectorstore: riusiamo lo stesso chat_model definito sopra.
compressor = LLMChainExtractor.from_llm(chat_model)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, 
    base_retriever=vectordb.as_retriever()
    )

question = "What is the main topic of the CBOM paper?"
docs = compression_retriever.invoke(question)
pretty_print_docs(docs)


"""
It's worth noting that vectordb as not the only kind of tool to retrieve documents.

The LangChain retriever abstraction includes other ways to retrieve documents, such as TF-IDF or SVM.
"""

from langchain_classic.retrievers import SVMRetriever
from langchain_classic.retrievers import TFIDFRetriever
from langchain_classic.document_loaders import PyPDFLoader
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter

# Load PDF
loader = PyPDFLoader("CBOM_paper_FBK.pdf")
pages = loader.load()
all_page_text=[p.page_content for p in pages]
joined_page_text=" ".join(all_page_text)

# Split
text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1500,chunk_overlap = 150)
splits = text_splitter.split_text(joined_page_text)

# Retrieve
svm_retriever = SVMRetriever.from_texts(splits,embedding)
tfidf_retriever = TFIDFRetriever.from_texts(splits)

question = "What is the main topic of the CBOM paper?"
docs_svm=svm_retriever.invoke(question)
print(docs_svm[0])

docs_tfidf=tfidf_retriever.invoke(question)
print(docs_tfidf[0])