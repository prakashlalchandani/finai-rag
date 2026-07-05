import asyncio
import json
import re
from config.settings import settings
from config.clients import groq_client
from config.logger import logger
from services.generation_service import GenerationService
from services.retrieval_service import RetrievalService

class CustomEvaluator:
    def __init__(self):
        self.gen_service = GenerationService()
        self.ret_service = RetrievalService()
        # We use the direct Groq client for grading
        self.judge = groq_client 

    async def grade_pipeline(self, query: str, context: list, final_answer: str):
        """The 70B Judge that scores Faithfulness and Relevance."""
        
        # Combine the context list into a single string for the prompt
        context_str = "\n\n".join(context) if isinstance(context, list) else str(context)

        prompt = f"""
        You are a strict, impartial grader for a Financial AI.
        Evaluate this interaction based on the Context retrieved from the database.

        USER QUERY: {query}
        CONTEXT: {context_str}
        AI ANSWER: {final_answer}

        Provide a JSON response with exactly these keys:
        1. "faithfulness_score": (0 to 10) Are the numbers/facts in the AI ANSWER strictly found in the CONTEXT without hallucinations?
        2. "relevance_score": (0 to 10) Does the AI ANSWER actually answer the USER QUERY?
        3. "reasoning": A brief 1-sentence explanation of your scores.
        
        Output ONLY valid JSON. No Markdown. No introduction.
        """

        try:
            logger.info("⚖️ Sending output to Judge LLM for evaluation...")
            response = await self.judge.chat.completions.create(
                model="llama3-70b-8192", # Using a larger model for judging
                messages=[{"role": "system", "content": prompt}],
                temperature=0.0, # Must be zero for consistent grading
                response_format={"type": "json_object"} 
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Clean up the response just in case the LLM returned markdown
            raw_response = raw_response.replace('```json', '').replace('```', '')
            
            result = json.loads(raw_response)
            return result
        except Exception as e:
            logger.error(f"Failed to parse Judge's response: {e}")
            return {"faithfulness_score": 0, "relevance_score": 0, "reasoning": "Evaluation failed."}

    async def run_test_suite(self):
        """Runs a batch of test queries to evaluate the system."""
        
        print("\n" + "="*50)
        print("🚀 STARTING RAG EVALUATION PIPELINE")
        print("="*50 + "\n")

        # Define some standard test queries
        test_queries = [
            "What is the EMI amount?",
            "What is the late payment penalty?",
            "Who is the landlord in the lease agreement?"
        ]

        # Use the default session for testing (make sure you have uploaded docs in this session!)
        session_id = "default_user_1" 
        document_selector = "all"
        
        # We need to sync memory first before running the test
        logger.info("Initializing Retrieval Memory for Evaluation...")
        await self.ret_service.sync_memory_state(session_id)

        total_faithfulness = 0
        total_relevance = 0

        for query in test_queries:
            print(f"\n🧪 TESTING QUERY: '{query}'")
            try:
                # 1. Expand Query
                legal_synonyms = await self.gen_service.expand_query_with_synonyms(query)
                enriched_query = f"{query} {legal_synonyms}"
                expanded_queries = await self.gen_service.generate_multi_queries(query)

                # 2. Retrieve Context
                retrieved_chunks = await self.ret_service.execute_hybrid_search(
                    original_query=query, 
                    enriched_query=enriched_query,
                    expanded_queries=expanded_queries,
                    session_id=session_id,
                    document_selector=document_selector
                )

                if not retrieved_chunks:
                     print(f"⚠️ Skipping '{query}': No context found. (Did you upload documents?)")
                     continue

                # 3. Generate Answer (Mocking DB by passing None, since we just want the answer)
                final_answer = await self.gen_service.generate_answer(query, retrieved_chunks, session_id, db=None)

                # 4. Grade the Result
                grade = await self.grade_pipeline(query, retrieved_chunks, final_answer)
                
                print(f"✅ Faithfulness: {grade.get('faithfulness_score')}/10 | Relevance: {grade.get('relevance_score')}/10")
                print(f"📝 Reasoning: {grade.get('reasoning')}")
                
                total_faithfulness += int(grade.get('faithfulness_score', 0))
                total_relevance += int(grade.get('relevance_score', 0))

            except Exception as e:
                print(f"❌ Error during evaluation of '{query}': {e}")

        # Calculate Averages
        if len(test_queries) > 0:
            avg_f = total_faithfulness / len(test_queries)
            avg_r = total_relevance / len(test_queries)
            print("\n" + "="*50)
            print(f"🏆 FINAL SYSTEM SCORE")
            print(f"Average Faithfulness: {avg_f:.2f} / 10")
            print(f"Average Relevance:    {avg_r:.2f} / 10")
            print("="*50 + "\n")

if __name__ == "__main__":
    evaluator = CustomEvaluator()
    asyncio.run(evaluator.run_test_suite())