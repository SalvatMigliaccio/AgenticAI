import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import ChatHuggingFace, HuggingFaceEmbeddings, HuggingFacePipeline


BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"

# Carica le variabili definite nel file .env
load_dotenv(dotenv_path=ENV_PATH)

for key in ["LANGCHAIN_API_KEY", "LANGCHAIN_ENDPOINT", "LANGCHAIN_TRACING_V2", "HUGGINGFACEHUB_API_TOKEN"]:
	value = os.getenv(key)
	if value:
		os.environ[key] = value.strip().strip('"').strip("'")

# Corregge endpoint LangSmith legacy (langchain.plus -> smith.langchain.com)
endpoint = os.environ.get("LANGCHAIN_ENDPOINT", "")
if "langchain.plus" in endpoint:
	os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# Disattiva tracing LangSmith per evitare errori 403/endpoint durante i test locali
os.environ["LANGCHAIN_TRACING_V2"] = "false"

# Embedding con modello Hugging Face (senza funzioni)
embedding = HuggingFaceEmbeddings(
	model_name="sentence-transformers/all-MiniLM-L6-v2",
	model_kwargs={"device": "cpu"},
	encode_kwargs={"normalize_embeddings": True},
)

vectordb = Chroma(persist_directory="db", embedding_function= embedding)
question = "What is the main idea of the text?"
docs = vectordb.similarity_search(question, k=3)
len(docs)

llm_name = os.getenv("HF_CHAT_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

# Modello da Hugging Face Hub eseguito in locale (no crediti Inference API richiesti)
llm = HuggingFacePipeline.from_model_id(
	model_id=llm_name,
	task="text-generation",
	pipeline_kwargs={"max_new_tokens": 256, "do_sample": False, "return_full_text": False},
)

# Equivalente di ChatOpenAI(...).predict("Hello world!") usando Hugging Face Hub
chat_llm = ChatHuggingFace(llm=llm)
hello_response = chat_llm.invoke("Hello world!")
print(hello_response.content)

# Build prompt
from langchain_classic.prompts import PromptTemplate
template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum. Keep the answer as concise as possible. Always say "thanks for asking!" at the end of the answer. 
{context}
Question: {question}
Helpful Answer:"""
QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"],template=template,)

# Run chain
from langchain_classic.chains import RetrievalQA
question = "Is probability a class topic?"
qa_chain = RetrievalQA.from_chain_type(chat_llm,
									   retriever=vectordb.as_retriever(),
									   return_source_documents=True,
									   chain_type_kwargs={"prompt": QA_CHAIN_PROMPT})


result = qa_chain({"query": question})
print(result["result"])

#memory
from langchain_classic.memory import ConversationBufferMemory
memory = ConversationBufferMemory(
    memory_key ="chat_history", 
    return_messages=True
)

from langchain_classic.chains import ConversationalRetrievalChain
retriver = vectordb.as_retriever()
qa = ConversationalRetrievalChain.from_llm(
    chat_llm, 
    retriever=retriver, 
    memory=memory
    )

question = "What is the main topic of the CBOM paper?"
result = qa({"question": question})
print(result.get("answer") or result.get("result") or result)

question = "Why CBOM is important?"
result = qa({"question": question})
print(result.get("answer") or result.get("result") or result)

