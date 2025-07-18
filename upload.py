
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from chrome.Chrome import db

def ingest_document(file_path: str) -> None:
    """
    Load a document, split it into chunks, and add to Chroma DB.

    Args:
        file_path (str): Path to the input file.
        db (Chroma): Chroma database instance.
    """
    try:
        if file_path.lower().endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            docs = loader.load()
        elif file_path.lower().endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            docs = [Document(page_content=text, metadata={"source": file_path})]
        elif file_path.lower().endswith(".csv"):
            loader = CSVLoader(file_path)
            docs = loader.load()
        elif file_path.lower().endswith(".xlsx"):
            loader = UnstructuredExcelLoader(file_path)
            docs = loader.load()
        else:
            raise ValueError("Unsupported file type. Only .pdf, .txt, .csv, .xlsx are supported.")

        splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=25)
        chunks = splitter.split_documents(docs)
        db.add_documents(chunks)
        print(f"✅ Successfully ingested {len(chunks)} chunks from {file_path}")
    except Exception as e:
        print(f"❌ Error ingesting document: {e}")
