from strands import Agent, AgentSkills
from strands.models import BedrockModel
from strands.session.s3_session_manager import S3SessionManager

# NOT WORKING in this environment: the IAM role has no S3 permissions
# (s3:CreateBucket and s3:PutObject are denied, verified 2026-08-03), so a
# session bucket can neither be created nor written to. The model adjustment
# (nova-lite) is applied anyway for reference.
from customer_service_tools import lookup_customer, get_order_history, process_refund
from steering_handlers import RefundWorkflowHandler, tone_handler

SYSTEM_PROMPT = """You are a customer service agent for an online electronics store.
Be helpful, professional, and concise. Use the available tools to look up customer
information and process requests. When a customer needs help, activate the appropriate
skill for step-by-step guidance.

Important guidelines:
- Always ask for the customer ID first if you don't have it.
- Use the data returned by tools to answer questions. Do not ask the customer for
  information that is already available in the tool results.
- Never show internal IDs, system formats, or example data to the customer.
- Be warm but efficient. Customers want their problem solved, not a long conversation."""

skills_plugin = AgentSkills(skills=["./skills"])

session_manager = S3SessionManager(
    session_id="customer-session-001",
    bucket="your-agent-sessions-bucket",
    prefix="production/",
    region_name="us-east-1",
)

agent = Agent(
    # Adjusted: use amazon.nova-lite-v1:0 (only permitted model) in us-east-1
    model=BedrockModel(model_id="amazon.nova-lite-v1:0", region_name="us-east-1"),
    tools=[lookup_customer, get_order_history, process_refund],
    plugins=[
        skills_plugin,
        RefundWorkflowHandler(),
        tone_handler,
    ],
    system_prompt=SYSTEM_PROMPT,
    # Adjusted: conversation_manager="auto" is not supported in strands-agents 1.45.0
    # (string mode belongs to context_manager); use the default conversation manager.
    session_manager=session_manager,
)

print("Customer Service Agent with S3 Persistence (type 'quit' to exit)")
print("-" * 60)
print(f"Session: {session_manager.session_id}")
print(f"Restored messages: {len(agent.messages)}")

while True:
    user_input = input("\nCustomer: ").strip()
    if user_input.lower() in ("quit", "exit", "q"):
        print("Goodbye!")
        break
    if not user_input:
        continue
    print()
    agent(user_input)
