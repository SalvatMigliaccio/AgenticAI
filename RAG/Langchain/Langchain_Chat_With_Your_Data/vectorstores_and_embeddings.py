from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

loaders = [
            PyPDFLoader("CBOM_paper_FBK.pdf"),
            PyPDFLoader("Paper Hybrid Strategies for the Transition to Post-Quantum Cryptography.pdf"),
            PyPDFLoader("Software-assisted analysis of post-quantum cryptography migration for the European Digital Identity Wallet.pdf"),
           ]
docs = []
for loader in loaders:
    docs.extend(loader.load())
    
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)
splits = text_splitter.split_documents(docs)
len(splits)
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}, # oppure "cuda"
    encode_kwargs={"normalize_embeddings": True}
)

sentence1 = "i like dogs"
sentence2 = "i like canines"
sentence3 = "the weather is ugly outside"

embedding1 = embedding.embed_query(sentence1)
embedding2 = embedding.embed_query(sentence2)
embedding3 = embedding.embed_query(sentence3)

persistent_directory = 'db'

vectordb = Chroma.from_documents(
    documents=splits,
    embedding=embedding,
    persist_directory=persistent_directory
)

print(vectordb._collection.count())
    
question = "What is the main topic of the CBOM paper?"
docs = vectordb.similarity_search(question, k=3)
len(docs)
print(docs[0].page_content)
print(docs[1].page_content)

vectordb.persist()
