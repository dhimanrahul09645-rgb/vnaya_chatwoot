import pandas as pd
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()

def ingest_data(file_path, collection_name):
    if not os.path.exists(file_path):
        print(f"❌ Error: {file_path} not found!")
        return

    df = pd.read_csv(file_path)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    docs = [
        Document(page_content=str(row['content']), metadata={"topic": str(row['topic'])}) 
        for _, row in df.iterrows()
    ]
    
    persist_dir = f"./chroma_db/{collection_name}"
    Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_dir)
    print(f"✅ Ingested {len(docs)} rows into {collection_name}")

if __name__ == "__main__":
    ingest_data("files/technical_data.csv", "technical")
    ingest_data("files/vnaya_policies.csv", "policy")