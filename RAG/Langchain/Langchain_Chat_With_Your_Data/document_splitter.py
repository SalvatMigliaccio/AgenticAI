from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter

chunk_size = 20
chunk_overlap = 4

r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap
    )
c_splitter = CharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap
)

text = "This is a sample text that will be split into chunks. It contains multiple sentences and should be divided based on the specified chunk size and overlap."

print(c_splitter.split_text(text))

text3 = "a b c d e f g h i j k l m n o p q r s t u v w x y z"

print(c_splitter.split_text(text3))
print(r_splitter.split_text(text3))

c_splitter = CharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    separator = ' '
)
print(c_splitter.split_text(text3))

#Recursive splitting details
#The recursive splitting strategy is designed to handle complex text structures by recursively breaking down the text into smaller chunks based on the specified chunk size and overlap. This approach ensures that the resulting chunks are manageable and maintain context, which is particularly useful for tasks such as document retrieval, summarization, or question answering.

some_text = """When writing documents, writers will use document structure to group content. \
This can convey to the reader, which idea's are related. For example, closely related ideas \
are in sentances. Similar ideas are in paragraphs. Paragraphs form a document. \n\n  \
Paragraphs are often delimited with a carriage return or two carriage returns. \
Carriage returns are the "backslash n" you see embedded in this string. \
Sentences have a period at the end, but also, have a space.\
and words are separated by space."""

print(len(some_text))
c_splitter = CharacterTextSplitter(
    chunk_size=450,
    chunk_overlap=0,
    separator = ' '
)
r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=450,
    chunk_overlap=0, 
    separators=["\n\n", "\n", " ", ""]
)
print(c_splitter.split_text(some_text))
print(r_splitter.split_text(some_text))

