from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from tools import get_patch, ddgs_search, get_routines
import os

# Ollama3 GPU LLM
llm = OllamaLLM(model="llama3", temperature=0.7)
embeddings = OllamaEmbeddings(model="llama3")

# Load RAG for LoL
if os.path.isdir("lol_rag_index"):
    vectorstore = FAISS.load_local("lol_rag_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k":3})
else:
    retriever = None

def TipAgent(game: str, query: str) -> str:
    if "lol" in game.lower() and retriever:
        docs = retriever.get_relevant_documents(query)
        context = "\n".join([d.page_content for d in docs])
    else:
        context = ""
    prompt = f"Game: {game}\nContext: {context}\nQuestion: {query}\nTips for beginners:"
    return llm(prompt)

def MetaAgent(game: str) -> str:
    patch_info = get_patch.invoke(game)
    meta_info = ddgs_search(f"{game} {patch_info} current op meta",max_results=6)
    return f"Patch info: {patch_info}\nMeta info: {meta_info}"

def RoutineAgent(game: str) -> str:
    return get_routines(game)
