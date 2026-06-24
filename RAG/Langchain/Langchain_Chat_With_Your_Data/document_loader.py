from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.blob_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.parsers import OpenAIWhisperParser
from langchain_community.document_loaders.blob_loaders.youtube_audio import YoutubeAudioLoader
from langchain_community.document_loaders import WebBaseLoader

pdf_path = Path(__file__).parent / "CBOM_paper_FBK.pdf"
loader = PyPDFLoader(str(pdf_path))
pages = loader.load()

print(len(pages))

page = pages[0]
print(page.page_content[:100])
print(page.metadata)

url="https://www.youtube.com/watch?v=jGwO_UgTS7I"
save_dir="docs/youtube/"
loader = GenericLoader(
    #YoutubeAudioLoader([url],save_dir),  # fetch from youtube
    FileSystemBlobLoader(save_dir, glob="*.m4a"),   #fetch locally
    OpenAIWhisperParser()
)
docs = loader.load()




loader = WebBaseLoader("https://github.com/basecamp/handbook/blob/master/titles-for-programmers.md")