from unstructured.partition.auto import partition
from llama_index.core import Document
from llama_index.core.node_parser import HierarchicalNodeParser

from config.settings import settings
from config.logger import logger
from config.clients import groq_client # <-- Importing the centralized client!

async def summarize_table(table_html):
    """Uses the lightning-fast Groq model to convert a raw table into natural sentences asynchronously."""
    prompt = f"""
    You are an expert data analyst. Read the following HTML table extracted from a legal PDF. 
    Write a highly detailed, natural language summary of every key-value pair and data point in this table.
    State the numbers clearly. Do not use formatting, just plain sentences.
    
    Table Data:
    {table_html}
    """
    
    try:
        # FIXED: Added 'await' to the async network call
        response = await groq_client.chat.completions.create(
            model=settings.ROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Table summarization failed. Error: {e}")
        return "Table summarization unavailable."

async def create_chunks(file_location):
    """Extracts and chunks text and tables asynchronously."""
    logger.info("Extracting text and tables using Unstructured...")
    
    # 1. The Pro-Level Table Extractor (Unstructured)
    elements = partition(
        filename=file_location,
        strategy="hi_res",
        infer_table_structure=True
    )
    
    processed_texts = []
    
    # 2. Intercept Tables for LLM Summarization
    for el in elements:
        if el.category == "Table":
            logger.info("Table detected! Generating semantic summary with Groq...")
            table_html = el.metadata.text_as_html if hasattr(el.metadata, 'text_as_html') and el.metadata.text_as_html else str(el)
            
            # FIXED: Added 'await' since summarize_table is now async
            table_summary = await summarize_table(table_html)
            
            processed_texts.append(f"RAW TABLE DATA:\n{str(el)}\n\nTABLE SUMMARY:\n{table_summary}")
        else:
            processed_texts.append(str(el).strip())
    
    clean_text = "\n\n".join([text for text in processed_texts if text])
    
    # 3. The Bridge: Wrap the clean text into a LlamaIndex Document object
    document = Document(text=clean_text)
    
    # 4. The Enterprise Chunking Tree (LlamaIndex)
    logger.info("Building Hierarchical nodes...")
    node_parser = HierarchicalNodeParser.from_defaults(
        chunk_sizes=[2048, 512, 128]
    )
    nodes = node_parser.get_nodes_from_documents([document])
    
    # 5. Extract the final text chunks
    chunks = []
    for node in nodes:
        text = node.text.strip()
        if text:
            text = " ".join(text.split()) 
            chunks.append(text)

    return chunks