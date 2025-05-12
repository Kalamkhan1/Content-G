from utils import path
from langchain_community.vectorstores import Chroma as ChromaVectorStore
from langchain_community.embeddings import SentenceTransformerEmbeddings
import chromadb

chroma_client = chromadb.PersistentClient(path=path)
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
db = ChromaVectorStore(client=chroma_client, embedding_function=embedding_function, collection_name="Knowledge")