import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from ai_agent.agent import graph

load_dotenv()
app = Flask(__name__)

# Deduplication cache
processed_ids = set()

@app.route("/webhook", methods=["POST"])
@app.route("/api/webhook", methods=["POST"])
def webhook():
    data = request.json
    
    # 1. Deduplication: Stop Chatwoot retries from triggering double replies
    # Chatwoot sends a unique ID for every message. We store it to avoid repeats.
    message_id = data.get("id") or data.get("conversation", {}).get("id")
    event_type = data.get("event")
    
    # Strictly only process 'message_created'
    if event_type != "message_created":
        return jsonify({"status": "ignored event"}), 200

    # Ensure we don't process the same message ID twice in one session
    if message_id in processed_ids:
        print(f"⚠️ Duplicate ignored for ID: {message_id}")
        return jsonify({"status": "duplicate"}), 200
    
    processed_ids.add(message_id)

    # 2. Basic Info Extraction
    conv_id = data.get("conversation", {}).get("id")
    content = data.get("content")
    msg_type = data.get("message_type")

    # Ignore bot's own outgoing messages
    if msg_type != "incoming":
        return jsonify({"status": "ignored outgoing"}), 200

    print(f"💬 Processing: {content}")

    try:
        # 3. AI Processing
        config = {"configurable": {"thread_id": str(conv_id)}}
        result = graph.invoke({"messages": [("user", content)], "user_email": "student@vnaya.com"}, config)
        reply = result["messages"][-1].content

        # 4. Post back to Account ID 2
        cw_url = f"http://localhost:3000/api/v1/accounts/2/conversations/{conv_id}/messages"
        headers = {
            "api_access_token": os.getenv("CHATWOOT_TOKEN"),
            "Content-Type": "application/json"
        }
        
        requests.post(cw_url, json={"content": reply, "message_type": "outgoing"}, headers=headers)
        print(f"✅ AI Replied Successfully to Account 2")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        # Remove ID from set so we can try again if it actually failed
        processed_ids.discard(message_id)

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)