import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from config.settings import settings
from config.clients import groq_client
from config.logger import logger

class GenerationService:
    def __init__(self):
        # State isolated to this specific service instance
        self.store = {}
        self.client = groq_client
        
        # Initialize LangChain LLM once when the service is created
        self.llm = ChatGroq(
            model=settings.SYNTHESIS_MODEL,
            temperature=0,
            api_key=settings.GROQ_API_KEY
        )

    def _get_session_history(self, session_id: str):
        """Internal helper to manage chat history."""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

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

    async def generate_answer(self, query: str, retrieved_chunks: list, session_id: str):
        """Synthesizes the final answer using LangChain."""
        context = "\n\n".join(retrieved_chunks)
        
        system_prompt = (
            "You are an elite financial auditor. Follow these rules:\n"
            "1. NO MENTAL MATH.\n"
            "2. ALWAYS use the provided EMI.\n"
            "3. EXTRACT CAREFULLY.\n"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"), 
            ("human", "Context:\n{context}\n\nQuestion: {query}")
        ])

        chain = prompt | self.llm

        chain_with_history = RunnableWithMessageHistory(
            chain,
            self._get_session_history,
            input_messages_key="query",
            history_messages_key="chat_history",
        )

        logger.info(f"Synthesizing response for session: {session_id}...")

        response = await chain_with_history.ainvoke(
            {"query": query, "context": context},
            config={"configurable": {"session_id": session_id}}
        )
        return response.content