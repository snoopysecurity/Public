import json
import requests
from string import Template
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, data, prompt_template, json_mode=True):
        pass

    def _parse_json(self, content):
        """Common helper to parse JSON from LLM responses."""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content)

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        
    def generate(self, data, prompt_template, json_mode=True):
        prompt = Template(prompt_template).safe_substitute(**data)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        if json_mode:
             messages.insert(0, {"role": "system", "content": "You are a security expert. Respond with valid JSON only."})
        else:
             messages.insert(0, {"role": "system", "content": "You are a security expert."})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        
        resp_json = response.json()
        content = resp_json["choices"][0]["message"]["content"]
        usage = resp_json.get("usage", {})
        
        if json_mode:
            return self._parse_json(content), usage
        else:
            return content, usage

class GeminiProvider(LLMProvider):
    def __init__(self, api_key, model="gemini-pro"):
        self.api_key = api_key
        self.model = model
        
    def generate(self, data, prompt_template, json_mode=True):
        prompt = Template(prompt_template).safe_substitute(**data)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        text_part = prompt
        if json_mode:
            text_part += "\n\nRespond with valid JSON."

        payload = {
            "contents": [{
                "parts": [{"text": text_part}]
            }]
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        usage = result.get("usageMetadata", {})
        stats = {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0)
        }

        try:
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            if json_mode:
                return self._parse_json(content), stats
            else:
                return content, stats
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected Gemini response: {result}") from e

class OllamaProvider(LLMProvider):
    def __init__(self, model="llama2", api_url="http://localhost:11434"):
        self.model = model
        self.api_url = api_url
        
    def generate(self, data, prompt_template, json_mode=True):
        prompt = Template(prompt_template).safe_substitute(**data)
        
        url = f"{self.api_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        if json_mode:
            payload["prompt"] += "\n\nRespond with valid JSON: {\"status\": \"TP\"|\"FP\", \"reason\": \"...\"}"
            payload["format"] = "json"
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        resp = response.json()
        content = resp["response"]
        stats = {
            "prompt_tokens": resp.get("prompt_eval_count", 0),
            "completion_tokens": resp.get("eval_count", 0)
        }
        
        if json_mode:
            return json.loads(content), stats
        else:
            return content, stats

def create_provider(name, config):
    """Factory to create a provider instance from config."""
    key = config.get("api_key")
    model = config.get("model")
    
    if name == "openai":
        if not key: raise ValueError("OpenAI requires api_key")
        return OpenAIProvider(key, model or "gpt-3.5-turbo")
    elif name == "gemini":
        if not key: raise ValueError("Gemini requires api_key")
        return GeminiProvider(key, model or "gemini-pro")
    elif name == "ollama":
        return OllamaProvider(model or "llama2")
    else:
        raise ValueError(f"Unknown provider: {name}")
