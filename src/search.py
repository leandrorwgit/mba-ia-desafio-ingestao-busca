import os
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_openai import ChatOpenAI

load_dotenv()
for k in ("GOOGLE_EMBEDDING_MODEL", "DATABASE_URL","PG_VECTOR_COLLECTION_NAME"):
    if not os.getenv(k):
        raise RuntimeError(f"Environment variable {k} is not set")

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

def search_prompt(question=None):
  if not question:
      return None
    
  # Busca similaridade no PGVector
  embeddings = GoogleGenerativeAIEmbeddings(model=os.getenv("GOOGLE_EMBEDDING_MODEL","models/embedding-001"))

  store = PGVector(
      embeddings=embeddings,
      collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
      connection=os.getenv("DATABASE_URL"),
      use_jsonb=True,
  )

  results = store.similarity_search_with_score(question, k=10)
  if not results:
      return "Nenhum resultado encontrado."

  # Formata contexto
  array_contexto = []
  for i, (doc, score) in enumerate(results, start=1):
    meta = doc.metadata or {}
    page = meta.get("page")
    source = meta.get("source", "")

    header = f"[Trecho {i}"
    if page is not None:
        header += f" - página {page}"
    if source:
        header += f" - {source}"
    header += "]"

    array_contexto.append(f"{header}\n{doc.page_content}")

  contexto = "\n\n---\n\n".join(array_contexto)

  # Gera resposta com LLM
  prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=question)

  try:
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0.5)
    response = llm.invoke(prompt)

    answer = response.content if hasattr(response, "content") else str(response)
    return answer
  except Exception as e:
    return f"Erro ao consultar modelo: {e}"
