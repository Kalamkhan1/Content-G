
from langchain_chroma import Chroma as ChromaVectorStore
from langchain_community.embeddings import SentenceTransformerEmbeddings
import chromadb
import os 

path = os.path.join(os.getcwd(),"chroma_db")
chroma_client = chromadb.PersistentClient(path=path)
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
db = ChromaVectorStore(client=chroma_client, embedding_function=embedding_function, collection_name="Knowledge")