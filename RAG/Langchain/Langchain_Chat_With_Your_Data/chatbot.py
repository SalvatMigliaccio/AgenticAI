from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.document_loaders import PyPDFLoader
import os
import panel as pn
import param

llm_name = os.getenv("HF_CHAT_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
# Modello da Hugging Face Hub eseguito in locale (no crediti Inference API richiesti)
llm = HuggingFacePipeline.from_model_id(
	model_id=llm_name,
	task="text-generation",
    pipeline_kwargs={"max_new_tokens": 256, "do_sample": True, "temperature": 0.1, "return_full_text": False},
)

def load_db(file,chain_type, k):
    #load document(s)
    if isinstance(file, str):
        files = [file]
    else:
        files = list(file)

    documents = []
    for pdf_path in files:
        loader = PyPDFLoader(pdf_path)
        documents.extend(loader.load())
    #split document into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    #define embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    #creatre vectorstore
    db = DocArrayInMemorySearch.from_documents(docs, embeddings)
    #create retriever
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})
    #create a chatbot chain. memory is managed externally
    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type=chain_type,
        retriever=retriever,
        return_source_documents=True,
        return_generated_question=True,
    )
    return qa

class cbfs(param.Parameterized):
    chat_history = param.List([])
    answer = param.String("")
    db_query = param.String("")
    db_response = param.List([])
    
    def __init__(self, **params):
        super(cbfs, self).__init__(**params)
        self.panels = []
        self.loaded_file = "CBOM_paper_FBK.pdf"
        self.qa = load_db(self.loaded_file, chain_type="stuff", k=3)
        
    def call_load_db(self, file_bytes, count, file_name=None, button_load=None):
        if count == 0 or not file_bytes:
            return pn.pane.Markdown("Please upload a PDF file to load the database.", width=400)
        else:
            upload_dir = "uploaded_docs"
            os.makedirs(upload_dir, exist_ok=True)

            if isinstance(file_bytes, (bytes, bytearray)):
                file_bytes_list = [file_bytes]
            else:
                file_bytes_list = list(file_bytes)

            if isinstance(file_name, str) or file_name is None:
                file_names = [file_name or "uploaded_1.pdf"]
            else:
                file_names = list(file_name)

            saved_files = []
            for idx, content in enumerate(file_bytes_list):
                current_name = file_names[idx] if idx < len(file_names) and file_names[idx] else f"uploaded_{idx + 1}.pdf"
                safe_name = os.path.basename(current_name)
                if not safe_name.lower().endswith(".pdf"):
                    safe_name = f"{safe_name}.pdf"
                target_path = os.path.join(upload_dir, safe_name)
                with open(target_path, "wb") as temp_file:
                    temp_file.write(content)
                saved_files.append(target_path)

            self.loaded_file = ", ".join(os.path.basename(path) for path in saved_files)
            if hasattr(button_load, "button_style"):
                button_load.button_style = "outline"
            self.qa = load_db(saved_files, "stuff", 4)
            if hasattr(button_load, "button_style"):
                button_load.button_style = "solid"
        self.clr_history()
        return pn.pane.Markdown(f"Loaded {len(saved_files)} file(s): {self.loaded_file}")
    
    def convchain(self, query):
        if not query:
            return pn.WidgetBox(pn.Row('User:', pn.pane.Markdown("", width=600)), scroll=True)
        result = self.qa.invoke({"question": query, "chat_history": self.chat_history})
        answer_text = result.get("answer") or result.get("result") or "No answer available."
        self.chat_history.extend([(query, answer_text)])
        self.db_query = result.get("generated_question", "")
        self.db_response = result.get("source_documents", [])
        self.answer = answer_text
        self.panels.extend([
            pn.Row('User:', pn.pane.Markdown(query, width=600)),
            pn.Row('ChatBot:', pn.pane.Markdown(self.answer, width=600, styles={'background-color': '#F6F6F6'}))
        ])
        inp.value = ''  #clears loading indicator when cleared
        return pn.WidgetBox(*self.panels,scroll=True)
    
    @param.depends('db_query', )
    def get_lquest(self):
        if not self.db_query :
            return pn.Column(
                pn.Row(pn.pane.Markdown(f"Last question to DB:", styles={'background-color': '#F6F6F6'})),
                pn.Row(pn.pane.Str("no DB accesses so far"))
            )
        return pn.Column(
            pn.Row(pn.pane.Markdown(f"DB query:", styles={'background-color': '#F6F6F6'})),
            pn.pane.Str(self.db_query )
        )

    @param.depends('db_response', )
    def get_sources(self):
        if not self.db_response:
            return 
        rlist=[pn.Row(pn.pane.Markdown(f"Result of DB lookup:", styles={'background-color': '#F6F6F6'}))]
        for doc in self.db_response:
            rlist.append(pn.Row(pn.pane.Str(doc)))
        return pn.WidgetBox(*rlist, width=600, scroll=True)

    @param.depends('convchain', 'clr_history') 
    def get_chats(self):
        if not self.chat_history:
            return pn.WidgetBox(pn.Row(pn.pane.Str("No History Yet")), width=600, scroll=True)
        rlist=[pn.Row(pn.pane.Markdown(f"Current Chat History variable", styles={'background-color': '#F6F6F6'}))]
        for exchange in self.chat_history:
            rlist.append(pn.Row(pn.pane.Str(exchange)))
        return pn.WidgetBox(*rlist, width=600, scroll=True)

    def clr_history(self,count=0):
        self.chat_history = []
        return 


cb = cbfs()
file_input = pn.widgets.FileInput(accept='.pdf', multiple=True)
button_load = pn.widgets.Button(name="Load DB", button_type='primary')
button_clearhistory = pn.widgets.Button(name="Clear History", button_type='warning')
button_clearhistory.on_click(cb.clr_history)
inp = pn.widgets.TextInput( placeholder='Enter text here…')

bound_button_load = pn.bind(
    lambda file_bytes, clicks, file_name: cb.call_load_db(
        file_bytes,
        clicks,
        file_name=file_name,
        button_load=button_load,
    ),
    file_input,
    button_load.param.clicks,
    file_input.param.filename,
)
conversation = pn.bind(cb.convchain, inp) 

image_path = './img/convchain.jpg'
if os.path.exists(image_path):
    jpg_pane = pn.pane.Image(image_path)
else:
    jpg_pane = pn.pane.Markdown("Image not found: ./img/convchain.jpg")

tab1 = pn.Column(
    pn.Row(inp),
    pn.layout.Divider(),
    pn.panel(conversation,  loading_indicator=True, height=300),
    pn.layout.Divider(),
)
tab2= pn.Column(
    pn.panel(cb.get_lquest),
    pn.layout.Divider(),
    pn.panel(cb.get_sources ),
)
tab3= pn.Column(
    pn.panel(cb.get_chats),
    pn.layout.Divider(),
)
tab4=pn.Column(
    pn.Row( file_input, button_load, bound_button_load),
    pn.Row( button_clearhistory, pn.pane.Markdown("Clears chat history. Can use to start a new topic" )),
    pn.layout.Divider(),
    pn.Row(jpg_pane.clone(width=400))
)
dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# ChatWithYourData_Bot')),
    pn.Tabs(('Conversation', tab1), ('Database', tab2), ('Chat History', tab3),('Configure', tab4))
)

if __name__ == "__main__":
    pn.serve(
        {"ChatWithYourData_Bot": dashboard},
        port=5006,
        show=True,
    )