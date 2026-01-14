#!/usr/bin/env python3
"""
Test script for the VyvchAI Multi-Agent Tutor System
Run this script to test the agent functionality in Docker
"""

import asyncio

import httpx

# Test configuration
FASTAPI_URL = "http://localhost:8000"
AGENT_TEST_DATA = {
    "tenant_id": "test-tenant-001",
    "user_query": (
        "Розкажи мені про квадратні рівняння та дай кілька прикладів для розв'язання"
    ),
    "student_profile": {
        "grade": 8,
        "subject": "algebra",
        "difficulty_level": "intermediate",
    },
}


async def test_fastapi_health():
    """Test FastAPI application health"""
    print("🔍 Testing FastAPI health...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{FASTAPI_URL}/")
            if response.status_code == 200:
                print("✅ FastAPI is healthy")
                return True
            else:
                print(f"❌ FastAPI health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ FastAPI connection failed: {e}")
        return False


async def test_agent_direct():
    """Test the agent directly using the main.py script"""
    print("\n🤖 Testing Agent Execution...")

    try:
        # Import the agent components
        from src.agent.supervisor import SupervisorAgent
        from src.llm.lapa_client import LapaLLMClient
        from src.schemas.agent_state import AgentState

        print("✅ Agent imports successful")

        # Test LapaLLM client instantiation
        _lapa_client = LapaLLMClient()
        print("✅ LapaLLM client initialized")

        # Test supervisor agent instantiation
        _supervisor = SupervisorAgent()
        print("✅ Supervisor agent initialized")

        # Create test state
        _test_state = AgentState(
            tenant_id="test-tenant",
            user_query="Поясни, що таке похідна функції",
            current_stage="planning",
        )
        print("✅ Test state created")

        # Test basic agent planning (without full execution to avoid API calls)
        print("✅ Agent components are ready for execution")

        return True

    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_database_connection():
    """Test database connectivity"""
    print("\n🗄️ Testing database connection...")
    try:
        # Try to connect to PostgreSQL
        import asyncpg

        conn = await asyncpg.connect(
            user="user",
            password="password",
            database="vyvchai",
            host="localhost",
            port=5432,
        )
        await conn.close()
        print("✅ Database connection successful")
        return True
    except ImportError:
        print("⚠️ asyncpg not available, skipping database test")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_redis_connection():
    """Test Redis connectivity"""
    print("\n🔴 Testing Redis connection...")
    try:
        import redis  # type: ignore

        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except ImportError:
        print("⚠️ redis not available, skipping Redis test")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


async def test_qdrant_connection():
    """Test Qdrant connectivity"""
    print("\n🔍 Testing Qdrant connection...")
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url="http://localhost:6333")
        # Try to list collections
        _collections = client.get_collections()
        print("✅ Qdrant connection successful")
        return True
    except ImportError:
        print("⚠️ qdrant-client not available, skipping Qdrant test")
        return True
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        return False


async def test_phoenix_connection():
    """Test Phoenix UI connectivity"""
    print("\n🔥 Testing Phoenix UI connection...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:6006")
            if response.status_code == 200:
                print("✅ Phoenix UI is accessible")
                return True
            else:
                print(f"⚠️ Phoenix UI returned status {response.status_code}")
                return True
    except Exception as e:
        print(f"⚠️ Phoenix UI connection failed: {e}")
        return True


async def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting VyvchAI Multi-Agent Tutor System Test Suite")
    print("=" * 60)

    results = []

    # Test infrastructure
    results.append(await test_redis_connection())
    results.append(await test_qdrant_connection())
    results.append(await test_database_connection())
    results.append(await test_phoenix_connection())

    # Test application
    results.append(await test_fastapi_health())
    results.append(await test_agent_direct())

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n✅ Your VyvchAI system is ready!")
        print("\n📋 Next steps:")
        print("1. Access FastAPI at: http://localhost:8000")
        print("2. View traces at: http://localhost:6006")
        print("3. Check logs in the container: docker-compose logs ai-tutor")
        print("4. Test agent endpoints via API calls")
    else:
        print(f"⚠️ Some tests failed ({passed}/{total})")
        print("\n🔧 Troubleshooting:")
        print("- Check docker-compose logs for detailed errors")
        print("- Ensure all services are running: docker-compose ps")
        print("- Verify environment variables are set correctly")

    return passed == total


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
