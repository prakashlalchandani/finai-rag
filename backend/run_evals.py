import asyncio
import json
from config.settings import settings
from config.clients import groq_client
from config.logger import logger
from services.generation_service import GenerationService
from services.retrieval_service import RetrievalService

class CustomEvaluator:
    def __init__(self):
        self.gen_service = GenerationService()
        self.ret_service = RetrievalService()
        self.judge = groq_client # We use the direct Groq client for grading

    async def grade_pipeline(self, query: str, context: list, final_answer: str):
        """The 70B Judge that scores Faithfulness and Relevance."""
        prompt = f"""
        You are a strict, impartial grader for a Financial AI. 
        Evaluate this interaction based on the Context retrieved from the database.
        
        USER QUERY: {query}
        CONTEXT: {context}
        AI ANSWER: {final_answer}
        
        Provide a JSON response with exactly these keys:
        1. "faithfulness_score": (0 to 10) Are the numbers/facts in the AI ANSWER strictly found in the CONTEXT without hallucinations?
        2. "relevance_score": (0 to 10) Does the AI ANSWER actually answer the USER QUERY?
        3. "reasoning": A brief 1-sentence explanation of your scores.
        """
        try:
            response = await self.judge.chat.completions.create(
                model="llama3-70b-8192", # The heavy, smart model for grading
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e)}

    async def run_evaluation(self):
        logger.info("Booting up Custom Evaluation Suite...")
        
        # 1. Ensure Qdrant memory is loaded
        if self.ret_service.__class__._chunks is None:
            await self.ret_service.sync_memory_state()

        test_questions = [
            "What is the EMI amount?",
            "What is the interest rate?",
            "How much is the total loan amount sanctioned?",
            "What happens if I miss a payment?"
        ]

        results = []

        # 2. Run the tests
        for query in test_questions:
            logger.info(f"Testing: {query}")
            
            # Step A: Run your actual pipeline
            synonyms = await self.gen_service.expand_query_with_synonyms(query)
            enriched_query = f"{query} {synonyms}"
            multi_queries = await self.gen_service.generate_multi_queries(query)
            
            chunks = await self.ret_service.execute_hybrid_search(query, enriched_query, multi_queries)
            answer = await self.gen_service.generate_answer(query, chunks, "eval")

            # Step B: Grade the results
            grades = await self.grade_pipeline(query, chunks, answer)
            
            # Step C: Log the scorecard
            scorecard = {
                "Question": query,
                "Faithfulness": grades.get("faithfulness_score"),
                "Relevance": grades.get("relevance_score"),
                "Judge_Feedback": grades.get("reasoning")
            }
            results.append(scorecard)

        # 3. Print a beautiful summary
        print("\n" + "="*50)
        print("🏆 EVALUATION SCORECARD 🏆")
        print("="*50)
        print(json.dumps(results, indent=4))

if __name__ == "__main__":
    evaluator = CustomEvaluator()
    asyncio.run(evaluator.run_evaluation())