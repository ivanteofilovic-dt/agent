"""Flask app for Slack integration."""
import os
from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bot import SlackBotHandler
from config import Config

# Initialize Flask app
flask_app = Flask(__name__)

# Initialize Slack app and bot handler
if Config.SLACK_BOT_TOKEN and Config.SLACK_SIGNING_SECRET:
    slack_app = App(
        token=Config.SLACK_BOT_TOKEN,
        signing_secret=Config.SLACK_SIGNING_SECRET
    )
    handler = SlackRequestHandler(slack_app)
    bot_handler = SlackBotHandler()
else:
    slack_app = None
    handler = None
    bot_handler = None
    print("⚠️  Slack integration not configured. Set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET in .env")


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events."""
    if not handler:
        return jsonify({"error": "Slack not configured"}), 500
    
    return handler.handle(request)


if slack_app:
    @slack_app.event("message")
    def handle_message(event, say):
        """Handle message events."""
        if not bot_handler:
            return
        
        # Process message through bot handler
        result = bot_handler.handle_message(event)
        
        # If bot_handler didn't send a message, we might need to respond
        if result and not result.get("ok"):
            say("❌ Error processing your message. Please try again.")


    @slack_app.event("file_shared")
    def handle_file_shared(event, say):
        """Handle file shared events."""
        if not bot_handler:
            return
        
        result = bot_handler.handle_file_shared(event)
        
        if result and not result.get("ok"):
            say("❌ Error processing file. Please try again.")


    @slack_app.command("/mrs-salesforce")
    def handle_command(ack, respond, command):
        """Handle slash commands."""
        ack()
        
        if not bot_handler:
            respond("❌ Slack integration not configured. Please check your environment variables.")
            return
        
        text = command.get("text", "").strip()
        user_id = command.get("user_id")
        channel_id = command.get("channel_id")
        
        if not text:
            respond("Please provide a transcript to process. Usage: `/mrs-salesforce <transcript>`")
            return
        
        # Process as transcript
        result = bot_handler._process_transcript(user_id, channel_id, text)
        
        if result and not result.get("ok"):
            respond("❌ Error processing transcript. Please try again.")


@flask_app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "slack_configured": slack_app is not None})


@flask_app.route("/", methods=["GET"])
def index():
    """Root endpoint."""
    return jsonify({
        "service": "Mrs. Salesforce Slack Integration",
        "status": "running",
        "slack_configured": slack_app is not None
    })


if __name__ == "__main__":
    port = Config.SLACK_PORT
    flask_app.run(host="0.0.0.0", port=port, debug=False)
