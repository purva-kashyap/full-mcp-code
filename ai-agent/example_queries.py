"""
Example queries to test the AI Agent

This file contains various example queries you can use to test
the agent's capabilities.
"""
import asyncio
from agent import AIAgent
from rich.console import Console

console = Console()


async def run_examples():
    """Run various example queries"""
    
    agent = AIAgent()
    await agent.initialize()
    
    examples = [
        # User management queries
        {
            "category": "User Management",
            "queries": [
                "List all users in the organization",
                "How many users do we have?",
                "Show me external guest users",
            ]
        },
        
        # Email queries
        {
            "category": "Email Operations",
            "queries": [
                "Show me the 5 most recent emails from the first user",
                "Search for emails about 'meeting' in john@company.com's mailbox",
                "Get the details of the latest email",
            ]
        },
        
        # Teams queries
        {
            "category": "Microsoft Teams",
            "queries": [
                "What teams exist in our organization?",
                "Who are the members of the first team?",
                "List all teams and their member counts",
            ]
        },
        
        # Profile queries
        {
            "category": "User Profiles",
            "queries": [
                "Get the profile information for the first user",
                "What is the job title of user@company.com?",
            ]
        },
        
        # Complex queries
        {
            "category": "Complex Queries",
            "queries": [
                "Find all users and show me emails from the first one",
                "List teams and show members of the Marketing team if it exists",
                "Search for urgent emails in the CEO's mailbox",
            ]
        },
    ]
    
    for example_set in examples:
        console.print(f"\n[bold magenta]{'='*80}[/bold magenta]")
        console.print(f"[bold yellow]{example_set['category']}[/bold yellow]")
        console.print(f"[bold magenta]{'='*80}[/bold magenta]\n")
        
        for query in example_set['queries']:
            console.print(f"[bold green]Query:[/bold green] {query}")
            console.print("[dim]Processing...[/dim]")
            
            try:
                response = await agent.ask(query)
                console.print(f"[bold cyan]Response:[/bold cyan]")
                console.print(response)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            
            console.print("\n" + "-"*80 + "\n")
            await asyncio.sleep(1)  # Small delay between queries
    
    await agent.close()


if __name__ == "__main__":
    asyncio.run(run_examples())
