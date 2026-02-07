import os
import json

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional, List
from rag_engine import RagEngine
import PIL.Image

# Define Pydantic models for structured output
class AISubs(BaseModel):
    I_rag: int = Field(description="Score 0-5 for RAG implementation (Vector Store, GraphRAG, HyDE)")
    I_agent: int = Field(description="Score 0-5 for Agentic behavior (ReAct, LangGraph, Tool Use)")
    I_ft: int = Field(description="Score 0-5 for Fine-tuning (LoRA, Custom Model)")
    I_safety: int = Field(description="Score 0-5 for Safety (Guardrails, PII Masking)")
    reasoning: str = Field(description="Brief explanation for the scores")

class GeneralScores(BaseModel):
    S_tech: int = Field(description="Technical Complexity score (1-10)")
    S_imp: int = Field(description="Impact score (1-10)")
    S_via: int = Field(description="Viability score (1-10)")
    reasoning: str = Field(description="Brief reasoning for these scores")

import base64
from langchain_core.messages import HumanMessage

class Evaluator:
    def __init__(self, groq_api_key):
        # Gemini Key removed. RAG Engine now uses Local Embeddings, so no key needed there either.
        self.rag_engine = RagEngine() 
        self.groq_api_key = groq_api_key
        
        if not groq_api_key:
            raise ValueError("Groq API Key is required.")

        # Initialize Groq for Text
        self.llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.0, groq_api_key=groq_api_key)
        
        # Initialize Groq for Vision
        # Using Llama 4 Scout (Vision/Multimodal)
        # Full ID required: meta-llama/llama-4-scout-17b-16e-instruct
        self.vision_model = ChatGroq(model_name="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0.0, groq_api_key=groq_api_key)

    def analyze_text_components(self, description, tech_stack):
        """
        Uses LLM to extract AI sub-scores and General scores.
        """
        prompt_text = f"""
        Analyze the following Hackathon Project:
        
        Project Description:
        {description}
        
        Tech Stack:
        {tech_stack}
        
        ---
        Task 1: Evaluate AI Implementation Details (0-5 scale each):
        - I_rag: Look for "Vector Store", "GraphRAG", "HyDE".
        - I_agent: Look for "ReAct", "LangGraph", "Tool Use".
        - I_ft: Look for "LoRA", "Fine-tuning", "Custom Model".
        - I_safety: Look for "Guardrails", "PII Masking".
        
        Task 2: Evaluate General Metrics (1-10 scale each):
        - S_tech: Technical Complexity.
        - S_imp: Impact.
        - S_via: Viability.
        
        Return a JSON object with strictly these keys:
        {{
            "ai_scores": {{
                "I_rag": <int>,
                "I_agent": <int>,
                "I_ft": <int>,
                "I_safety": <int>,
                "reasoning": "<string summary of AI scores>"
            }},
            "general_scores": {{
                "S_tech": <int>,
                "S_imp": <int>,
                "S_via": <int>,
                "reasoning": "<string summary of General scores>"
            }}
        }}
        """
        
        response = self.llm.invoke(prompt_text)
        content = response.content
        
        # Clean markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            # Fallback default
            return {
                "ai_scores": {"I_rag": 0, "I_agent": 0, "I_ft": 0, "I_safety": 0, "reasoning": "Failed to parse"},
                "general_scores": {"S_tech": 5, "S_imp": 5, "S_via": 5, "reasoning": "Failed to parse"}
            }
            
        return data

    def analyze_design(self, image_path):
        """
        Uses Groq (Llama 3.2 Vision) to analyze UI.
        """
        if not image_path:
            return 5.0, "No image provided."

        try:
            # Encode image to base64
            def encode_image(image_path):
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            
            base64_image = encode_image(image_path)
            
            prompt = "Rate this UI (1-10) on hierarchy, accessibility, and polish. Return ONLY the number."
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ]
            )
            
            response = self.vision_model.invoke([message])
            text = response.content.strip()
            
            # Extract number
            import re
            match = re.search(r'\d+(\.\d+)?', text)
            if match:
                score = float(match.group())
                return min(10.0, max(1.0, score)), text
            else:
                return 5.0, "Could not extract score from Groq response: " + text
        except Exception as e:
            print(f"Groq Vision Error: {e}")
            return 5.0, f"Error analyzing image: {str(e)}"

    def audit_project(self, description, tech_stack, image_path=None):
        # Step 1: Novelty (RAG)
        s_nov, similar_projects = self.rag_engine.calculate_novelty_score(description + " " + tech_stack)
        
        # Step 2 & 4: AI & General (LLM)
        analysis = self.analyze_text_components(description, tech_stack)
        ai_data = analysis.get("ai_scores", {})
        gen_data = analysis.get("general_scores", {})
        
        # Calculate S_ai
        # Math: S_ai = 0.25(I_rag) + 0.25(I_agent) + 0.25(I_ft) + 0.25(I_safety)
        # Note: Input is 0-5. Sum is 0-20. 0.25 * Sum is 0-5. 
        # Requirement says "Scaled to 10". So we multiply by 2.
        i_rag = ai_data.get("I_rag", 0)
        i_agent = ai_data.get("I_agent", 0)
        i_ft = ai_data.get("I_ft", 0)
        i_safety = ai_data.get("I_safety", 0)
        
        raw_ai_sum = (0.25 * i_rag) + (0.25 * i_agent) + (0.25 * i_ft) + (0.25 * i_safety)
        s_ai = raw_ai_sum * 2 # Scale to 10
        
        # Step 3: Design (Vision)
        s_des, des_reasoning = self.analyze_design(image_path)
        
        # Step 4: General Scores
        s_tech = gen_data.get("S_tech", 5)
        s_imp = gen_data.get("S_imp", 5)
        s_via = gen_data.get("S_via", 5)
        
        # Final Formula
        # S_total = 0.2(S_nov) + 0.2(S_tech) + 0.2(S_imp) + 0.1(S_via) + 0.2(S_ai) + 0.1(S_des)
        s_total = (0.2 * s_nov) + (0.2 * s_tech) + (0.2 * s_imp) + (0.1 * s_via) + (0.2 * s_ai) + (0.1 * s_des)
        
        return {
            "S_total": round(s_total, 1),
            "metrics": {
                "S_nov": s_nov,
                "S_tech": s_tech,
                "S_imp": s_imp,
                "S_via": s_via,
                "S_ai": s_ai,
                "S_des": s_des
            },
            "ai_breakdown": {
                "I_rag": i_rag,
                "I_agent": i_agent,
                "I_ft": i_ft,
                "I_safety": i_safety
            },
            "similar_projects": similar_projects,
            "reasoning": {
                "ai": ai_data.get("reasoning", ""),
                "general": gen_data.get("reasoning", ""),
                "design": des_reasoning
            }
        }
