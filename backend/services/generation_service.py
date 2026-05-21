import json
import asyncio
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# --- New Database Imports ---
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models.model as models
# ----------------------------

from config.settings import settings
from config.clients import groq_client
from config.logger import logger

class GenerationService:
    def __init__(self):
        self.client = groq_client
        self.llm = ChatGroq(
            model=settings.SYNTHESIS_MODEL,
            temperature=0,
            api_key=settings.GROQ_API_KEY
        )

    async def get_chat_history_from_db(self, db: AsyncSession, session_id: str):
        """PostgreSQL se specific session ki chat history nikalta hai."""
        stmt = select(models.Message).where(
            models.Message.session_id == session_id
        ).order_by(models.Message.created_at.asc())
        
        result = await db.execute(stmt)
        db_messages = result.scalars().all()
        
        # LangChain compatible format mein convert karo
        langchain_history = []
        for msg in db_messages:
            if msg.role == "user":
                langchain_history.append(HumanMessage(content=msg.text))
            elif msg.role == "ai":
                langchain_history.append(AIMessage(content=msg.text))
        return langchain_history

    async def save_message_to_db(self, db: AsyncSession, session_id: str, role: str, text: str):
        """Naye chat message ko database mein permanently save karta hai."""
        # Ensure session exists first
        session_check = await db.get(models.ChatSession, session_id)
        if not session_check:
            new_session = models.ChatSession(id=session_id, user_id=1, session_name=f"Chat {session_id[:8]}")
            db.add(new_session)
            await db.flush() # Memory state validate karo bina commit kiye
            
        new_msg = models.Message(session_id=session_id, role=role, text=text)
        db.add(new_msg)
        await db.commit()
        return new_msg

    async def route_query(self, user_query: str):
        """The Front Door Supervisor Agent."""
        system_prompt = """
        You are a high-speed routing agent for a Financial Auditor AI.
        Classify the query into:
        1. "chat": General greetings or pleasantries.
        2. "rag": Questions about loans, EMIs, interest rates, or document terms.
        
        Respond in JSON with exactly two keys: "route" and "chat_response".
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.0, 
                response_format={"type": "json_object"} 
            )
            decision = json.loads(response.choices[0].message.content)
            logger.info(f"Routing Decision: {decision['route'].upper()}")
            return decision
        except Exception as e:
            logger.error(f"Router failed. Error: {e}")
            return {"route": "rag", "chat_response": ""}

    async def expand_query_with_synonyms(self, user_query: str):
        """Acts as a financial translator."""
        system_prompt = """
        Generate 3 to 5 highly specific legal/financial synonyms for the user's query.
        Output ONLY a comma-separated list. Do not answer the question.
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1
            )
            synonyms = response.choices[0].message.content.strip()
            logger.info(f"Query Expanded with Synonyms: {synonyms}")
            return synonyms
        except Exception as e:
            logger.error(f"Query expansion failed. Error: {e}")
            return ""
        
    async def generate_multi_queries(self, query: str, max_retries: int = 3) -> list:
        """Rewrites the query into multiple formal variations using Groq."""
        prompt = f"""
        Rewrite the following search query into 3 different variations using formal financial and banking terminology.
        Return only the queries, separated by newlines. Do not use bullet points or numbers.
        Original query: '{query}'
        """
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=settings.ROUTER_MODEL,
                    temperature=0.2
                )
                
                text_output = response.choices[0].message.content.strip()
                queries = [q.strip() for q in text_output.split('\n') if q.strip()]
                logger.info(f"Multi-queries generated: {queries}")
                return queries
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Groq API busy. Retrying Multi-Query in {wait_time}s... Error: {e}")
                    await asyncio.sleep(wait_time) # Non-blocking wait!
                else:
                    logger.error(f"Groq API unavailable. Skipping Multi-Query. Error: {e}")
                    return []

    async def generate_answer(self, query: str, retrieved_chunks: list, session_id: str, db: AsyncSession):
        """Synthesizes the final answer using DB Chat History."""
        context = "\n\n".join(retrieved_chunks)
        
        system_prompt = (
            "You are an elite financial auditor. Follow these rules:\n"
            "1. NO MENTAL MATH.\n"
            "2. ALWAYS use the provided EMI.\n"
            "3. EXTRACT CAREFULLY.\n"
        )

        # 1. DB se pichli history lekar aao
        chat_history = await self.get_chat_history_from_db(db, session_id)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"), 
            ("human", "Context:\n{context}\n\nQuestion: {query}")
        ])

        chain = prompt | self.llm
        logger.info(f"Synthesizing response for session: {session_id} using DB history...")

        # 2. Invoke Chain with active history list
        response = await chain.ainvoke({
            "query": query, 
            "context": context,
            "chat_history": chat_history
        })

        # 3. Save User Query and AI Response to DB asynchronously
        await self.save_message_to_db(db, session_id, "user", query)
        await self.save_message_to_db(db, session_id, "ai", response.content)

        return response.content