import json
from main import engine


def test_memory_bank():
    print("=== Memory Bank MCP Test ===\n")
    
    print("1. Creating memory session...")
    session_id = engine.start_session(
        problem="How to build a recommendation system?",
        criteria="Scalable system with <100ms response time",
        constraints=["Limited to open source tools", "$1000 budget"]
    )
    print(f"Started session: {session_id}\n")
    
    print("2. Adding initial memories...")
    memory1_id = engine.add_memory(
        content="First principle: recommendations match user preferences based on behavior patterns",
        confidence=0.9
    )
    print(f"Added memory: {memory1_id}")
    
    memory2_id = engine.add_memory(
        content="Need to collect user interaction data: clicks, purchases, time spent",
        dependencies=[memory1_id],
        confidence=0.8
    )
    print(f"Added memory: {memory2_id}")
    
    memory3_id = engine.add_memory(
        content="This approach is wrong - users don't always follow patterns",
        dependencies=[memory1_id],
        confidence=0.7
    )
    print(f"Added memory with contradiction: {memory3_id}\n")
    
    print("3. Creating collection for alternative approach...")
    collection_id = engine.create_collection(
        name="collaborative_filtering",
        from_memory=memory2_id,
        purpose="Explore user-user similarity approach"
    )
    print(f"Created collection: {collection_id}")
    
    collection_memory_id = engine.add_memory(
        content="Calculate user similarity using cosine similarity on interaction vectors",
        collection_id=collection_id,
        confidence=0.7
    )
    print(f"Added collection memory: {collection_memory_id}\n")
    
    print("4. Getting memory tree...")
    tree = engine.get_memory_tree()
    print(json.dumps(tree, indent=2))
    print()
    
    print("5. Analyzing memory quality...")
    analysis = engine.get_analysis()
    print(json.dumps(analysis, indent=2))
    print()
    
    print("6. Patterns detected:")
    print(json.dumps(engine.patterns, indent=2))


if __name__ == "__main__":
    test_memory_bank()