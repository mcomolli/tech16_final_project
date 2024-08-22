from pyngrok import ngrok

# Start an HTTP tunnel on port 3000
http_tunnel = ngrok.connect(3000)
print("ngrok tunnel created at:", http_tunnel.public_url)

# Your application code here
# e.g., starting a Flask app
# app.run(port=3000)

# To keep the tunnel open, you might need to block or keep the script running
try:
    input("Press Enter to exit...\n\n")
except KeyboardInterrupt:
    print("Shutting down ngrok tunnel...")

# Stop the ngrok tunnel when done
ngrok.disconnect(http_tunnel.public_url)
ngrok.kill()