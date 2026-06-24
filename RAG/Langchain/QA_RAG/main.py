
from langchain_core.tools import tool
from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain.agents import create_agent

load_dotenv()
model = ChatGroq(model_name='qwen/qwen3-32b', reasoning_format = 'parsed')

print("Model loaded successfully.")
print("loading document...")
loader = PyPDFLoader('AgentiAI_Survey.pdf')
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

print("building embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = InMemoryVectorStore.from_documents(all_splits, embeddings)

@tool
def retrieve_context(query):
    """Retrieves relevant information from the document based on the query. Returns the content and source of the relevant information."""
    similar_docs = vector_store.similarity_search(query, k=5)
    data = []
    for doc in similar_docs:
        data.append(f'''
            content: {doc.page_content},
            source: {doc.metadata.get('source', 'unknown')}
        ''')
    return "\n\n".join(data)


prompt = """You are an assistant for answering questions about the content of a document. You have access to a tool called 'retrieve_context' that allows you to retrieve relevant information from the document based on a query. When you receive a question, use the 'retrieve_context' tool to gather relevant information from the document, and then use that information to formulate a comprehensive answer to the question. Always cite the source of the information you use in your answer."""
agent = create_agent(model=model, tools=[retrieve_context], system_prompt=prompt)
query = "What are the main findings of the AgentiAI survey?"

for step in agent.stream({ "messages": [
    {
        "role": "user",
        "content": query
    }
]}, stream_mode='values'):
    step['messages'][-1].pretty_print()