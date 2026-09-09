"""Command Line Interface (CLI) application."""

import sys
import dotenv
from app.config import Config
from app.rag.indexer import index_all_documents
from app.rag.generator import ask_question
import pageindex

def print_menu():
    print("\n=================================")
    print("      Vectorless RAG (PageIndex) ")
    print("=================================")
    print("1. Index documents in data/pdfs/")
    print("2. Ask a question")
    print("3. Exit")

def server_main(question:str):
    if not question:
        return "Question cannot be empty."
        
        
    print("\nThinking and traversing PageIndex tree...")
    result = ask_question(question)

    print("\n" + "="*40)
    print("Answer:")
    print(result["answer"])
    print("\nSources:")
    if result["sources"]:
        for src in set(result["sources"]):
            print(f" • {src}")
    else:
        print(" • No matching source pages found.")
    print("="*40)




def main():
    while True:
        print_menu()
        choice = input("Select an option (1-3): ").strip()
        
        if choice == "1":
            print("\nStarting indexing process...")
            saved = index_all_documents()
            if saved:
                print(f"\n[Success] Indexed {len(saved)} document(s). Indexes saved in {Config.INDEXES_DIR}")
            else:
                print(f"\n[Notice] No documents indexed. Drop PDF files in '{Config.DOCUMENTS_DIR}' first.")
                
        elif choice == "2":
            question = input("\nEnter your question: ").strip()
            if not question:
                print("Question cannot be empty.")
                continue
                
            print("\nThinking and traversing PageIndex tree...")
            result = ask_question(question)
            
            print("\n" + "="*40)
            print("Answer:")
            print(result["answer"])
            print("\nSources:")
            if result["sources"]:
                for src in set(result["sources"]):
                    print(f" • {src}")
            else:
                print(" • No matching source pages found.")
            print("="*40)
            
        elif choice == "3":
            print("\nGoodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please choose 1, 2, or 3.")

if __name__ == "__main__":
    main()

    
# ```python
# from langgraph.graph import StateGraph, MessagesState, START, END

# def mock_llm(state: MessagesState):
#     return {"messages": [{"role": "ai", "content": "hello world"}]}

# # Create a state graph with the messages state and add nodes for the LLM and an endpoint.
# graph = StateGraph(MessagesState)
# graph.add_node(mock_llm)

# # Add edges from the start node to the mock_llm node, and then to the end node.
# graph.add_edge(START, "mock_llm")
# graph.add_edge("mock_llm", END)

# # Compile the graph into a runnable agent.
# graph = graph.compile()

# # Invoke the agent with some user input.
# result = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})

# print(result["messages"][-1].content_blocks)
# ```

# how to add a real llm in this code