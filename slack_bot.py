import os
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from rag_system import RAGSystem
from config import Config

class SlackBot:
    def __init__(self):
        self.config = Config()
        self.rag_system = RAGSystem()
        
        # Initialize Slack app
        self.app = App(
            token=self.config.SLACK_BOT_TOKEN,
            signing_secret=self.config.SLACK_SIGNING_SECRET
        )
        
        # Set up event handlers
        self._setup_handlers()
        
        # Create FastAPI handler
        self.handler = SlackRequestHandler(self.app)
    
    def _setup_handlers(self):
        """Set up Slack event handlers"""
        
        @self.app.message("hello")
        def handle_hello(message, say):
            """Handle hello messages"""
            say(f"Hello <@{message['user']}>! I'm your RAG bot. Ask me anything about the documents in my knowledge base!")
        
        @self.app.message("help")
        def handle_help(message, say):
            """Handle help messages"""
            help_text = """
🤖 *RAG Bot Help*

I can help you find information from uploaded documents. Here's what you can do:

• Ask me questions about any topic in the knowledge base
• Upload documents by mentioning me with a file attachment
• Use `stats` to see knowledge base statistics
• Use `hello` to get a greeting
• Use `help` to see this message

Just mention me (@ragbot) followed by your question!
            """
            say(help_text)
        
        @self.app.message("stats")
        def handle_stats(message, say):
            """Handle stats request"""
            try:
                stats = self.rag_system.get_collection_stats()
                stats_text = f"""
📊 *Knowledge Base Statistics*

• Total document chunks: {stats['total_documents']}
• Collection: {stats['collection_name']}
                """
                say(stats_text)
            except Exception as e:
                say(f"Error getting stats: {str(e)}")
        
        @self.app.event("app_mention")
        def handle_app_mention(event, say):
            """Handle when the bot is mentioned"""
            try:
                # Extract the question (remove the bot mention)
                text = event.get('text', '')
                # Remove bot mention from text
                question = ' '.join(text.split()[1:])  # Remove first word (bot mention)
                
                if not question.strip():
                    say("Please ask me a question! For example: @ragbot What is machine learning?")
                    return
                
                # Show typing indicator
                say("🤔 Let me search through the knowledge base...")
                
                # Get response from RAG system
                response = self.rag_system.query(question)
                
                # Format response
                formatted_response = f"""
💡 *Answer to: "{question}"*

{response}

_Powered by FlexaAI RAG System_
                """
                
                say(formatted_response)
                
            except Exception as e:
                say(f"Sorry, I encountered an error: {str(e)}")
        
        @self.app.event("file_shared")
        def handle_file_upload(event, client, say):
            """Handle file uploads"""
            try:
                file_id = event['file_id']
                
                # Get file info
                file_info = client.files_info(file=file_id)
                file_data = file_info['file']
                
                if file_data['mimetype'] == 'application/pdf':
                    # Download file content
                    file_url = file_data['url_private']
                    headers = {'Authorization': f'Bearer {self.config.SLACK_BOT_TOKEN}'}
                    
                    import requests
                    response = requests.get(file_url, headers=headers)
                    
                    if response.status_code == 200:
                        # Add to RAG system
                        result = self.rag_system.add_pdf_document(
                            response.content, 
                            file_data['name']
                        )
                        say(f"✅ Successfully processed: {file_data['name']}\n{result}")
                    else:
                        say("❌ Failed to download the file")
                else:
                    say("📄 I currently only support PDF files. Please upload a PDF document.")
                    
            except Exception as e:
                say(f"Error processing file: {str(e)}")
    
    def get_handler(self):
        """Get the FastAPI handler"""
        return self.handler