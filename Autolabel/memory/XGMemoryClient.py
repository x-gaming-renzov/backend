from mem0 import Memory
from ..utils.llm_utils import LLM

config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 1500,
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small"
        }
    }
}

class XGMemoryClient:
    def __init__(self, user_name="XG"):
        self.memory = Memory.from_config(config)
        self.user_name = user_name

    def add_kb_memory(self, kb_memory : str):
        #print(self.user_name)
        self.memory.add(kb_memory, user_id=self.user_name, prompt="""
                        Study what user wants to do, what is he doing currently, 
                        divide whole kb based on meaningfull sections and save them as separate memories""")
        print(self.memory.search("what does user want to do", user_id=self.user_name))
        
        return "Memory added successfully"
    
    def get_memory(self, query, limit=5, user_name=None):
        return self.memory.search(query, limit=limit, user_id=self.user_name)
    
    def chat(self, query, user_name=None):
        llm = LLM()
        if user_name == "all":
            user_name = None
        if not user_name:
            user_name = self.user_name
        fetch_result = self.memory.search(query, user_id=user_name, limit=5)
        memories = "\n".join([f"Memory: {i+1}\n{memory['memory']}" for i, memory in enumerate(fetch_result)])
        response = llm.send_message_for_code(f"""
                        Context from memory: {memories}
                        User: {query}
                        Answer the user query based on context from memory
                    """)
        return response
    
