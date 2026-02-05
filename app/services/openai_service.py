"""
AI Beauty Muse - OpenAI Service
Handles all interactions with OpenAI API for text generation and image analysis.
"""
import json
import base64
import httpx
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI

from app.config import settings


class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url if settings.openai_base_url else None,
        )
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
        self.image_model = settings.openai_image_model
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None,
    ) -> str:
        """
        Generate text using OpenAI chat completion.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            temperature: Creativity level (0-1)
            max_tokens: Maximum tokens in response
            response_format: Optional JSON schema for structured output
            
        Returns:
            Generated text response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.client.chat.completions.create(**kwargs)
        
        return response.choices[0].message.content
    
    async def analyze_image(
        self,
        image_url: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Analyze an image using OpenAI vision model.
        
        Args:
            image_url: URL of the image to analyze
            prompt: Analysis prompt
            system_prompt: System prompt for context
            temperature: Creativity level (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Analysis result as text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        })
        
        response = await self.client.chat.completions.create(
            model=self.vision_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "natural",
    ) -> str:
        """
        Generate an image using DALL-E.
        
        Args:
            prompt: Image generation prompt
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, hd)
            style: Image style (natural, vivid)
            
        Returns:
            URL of generated image
        """
        response = await self.client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
        )
        
        return response.data[0].url
    
    async def chat_with_context(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        image_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Chat with conversation context and optional image.
        
        Args:
            message: Current user message
            conversation_history: Previous messages
            image_url: Optional image for context
            system_prompt: System prompt
            
        Returns:
            Assistant's reply
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
        
        # Add current message with optional image
        if image_url:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            })
        else:
            messages.append({"role": "user", "content": message})
        
        response = await self.client.chat.completions.create(
            model=self.vision_model if image_url else self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )
        
        return response.choices[0].message.content


# Singleton instance
openai_service = OpenAIService()
