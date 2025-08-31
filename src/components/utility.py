"""
Discord Components v2 for Utility Commands
"""

import discord


class PingView(discord.ui.LayoutView):
    """View for ping command using Components v2"""
    
    def __init__(self, ws_latency: int, response_time: int):
        super().__init__()
        
        # Determine status
        if ws_latency < 100:
            status = "🟢 Excellent"
        elif ws_latency < 200:
            status = "🟡 Good"
        elif ws_latency < 300:
            status = "🟠 Fair"
        else:
            status = "🔴 Poor"
        
        content = (
            f"🏓 **Pong!**\n\n"
            f"**WebSocket Latency:** {ws_latency}ms\n"
            f"**Response Time:** {response_time}ms\n"
            f"**Status:** {status}"
        )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value  # Green for success
        )
        self.add_item(container)