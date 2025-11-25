"""Unit tests for router - NO external API calls"""

import pytest
from it_service_desk_agent.core.agent import Agent
from it_service_desk_agent.core.models import AgentRequest, AgentResponse, RequestContext, AgentError
from it_service_desk_agent.orchestration.router import AgentRouter


class DummyAgent(Agent):
    """Test agent for router testing"""
    
    @property
    def name(self) -> str:
        return "dummy_agent"
    
    @property
    def supported_intents(self):
        return ["test.intent.one", "test.intent.two"]
    
    async def handle(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            success=True,
            data={"echo": request.intent, "params": request.parameters}
        )


class AnotherDummyAgent(Agent):
    """Another test agent"""
    
    @property
    def name(self) -> str:
        return "another_agent"
    
    @property
    def supported_intents(self):
        return ["test.intent.three"]
    
    async def handle(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            success=True,
            data={"agent": "another", "intent": request.intent}
        )


@pytest.mark.asyncio
async def test_router_routes_to_correct_agent():
    """Router should route request to agent that supports the intent"""
    router = AgentRouter([DummyAgent(), AnotherDummyAgent()])
    
    ctx = RequestContext(
        user_id="test_user",
        source="cli",
        correlation_id="test_123",
        risk_level="low"
    )
    
    # Route to DummyAgent
    req = AgentRequest(intent="test.intent.one", parameters={"key": "value"}, context=ctx)
    resp = await router.route(req)
    
    assert resp.success is True
    assert resp.data["echo"] == "test.intent.one"
    assert resp.data["params"] == {"key": "value"}
    assert resp.agent_name == "dummy_agent"


@pytest.mark.asyncio
async def test_router_routes_to_different_agent():
    """Router should route different intent to different agent"""
    router = AgentRouter([DummyAgent(), AnotherDummyAgent()])
    
    ctx = RequestContext(
        user_id="test_user",
        source="cli",
        correlation_id="test_456",
        risk_level="low"
    )
    
    # Route to AnotherDummyAgent
    req = AgentRequest(intent="test.intent.three", parameters={}, context=ctx)
    resp = await router.route(req)
    
    assert resp.success is True
    assert resp.data["agent"] == "another"
    assert resp.agent_name == "another_agent"


@pytest.mark.asyncio
async def test_router_unknown_intent_returns_error():
    """Router should return structured error for unknown intent"""
    router = AgentRouter([DummyAgent()])
    
    ctx = RequestContext(
        user_id="test_user",
        source="cli",
        correlation_id="test_789",
        risk_level="low"
    )
    
    req = AgentRequest(intent="unknown.intent", parameters={}, context=ctx)
    resp = await router.route(req)
    
    assert resp.success is False
    assert resp.error is not None
    assert resp.error.code == "UNKNOWN_INTENT"
    assert "unknown.intent" in resp.error.message
    assert "available_intents" in resp.error.details


def test_router_rejects_duplicate_intents():
    """Router should fail fast if multiple agents claim same intent"""
    
    class ConflictingAgent(Agent):
        @property
        def name(self) -> str:
            return "conflicting"
        
        @property
        def supported_intents(self):
            return ["test.intent.one"]  # Conflicts with DummyAgent
        
        async def handle(self, request: AgentRequest) -> AgentResponse:
            return AgentResponse(success=True)
    
    with pytest.raises(ValueError) as exc_info:
        AgentRouter([DummyAgent(), ConflictingAgent()])
    
    assert "test.intent.one" in str(exc_info.value)
    assert "claimed by both" in str(exc_info.value)


def test_router_get_available_intents():
    """Router should expose list of available intents"""
    router = AgentRouter([DummyAgent(), AnotherDummyAgent()])
    
    intents = router.get_available_intents()
    
    assert "test.intent.one" in intents
    assert "test.intent.two" in intents
    assert "test.intent.three" in intents
    assert len(intents) == 3


def test_router_get_agent_for_intent():
    """Router should return agent name for a given intent"""
    router = AgentRouter([DummyAgent(), AnotherDummyAgent()])
    
    assert router.get_agent_for_intent("test.intent.one") == "dummy_agent"
    assert router.get_agent_for_intent("test.intent.three") == "another_agent"
    assert router.get_agent_for_intent("unknown") == "unknown"
