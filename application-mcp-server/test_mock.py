"""
Test script for the MOCK MCP Server

This demonstrates the mock server with fake data.
No Microsoft credentials required!
"""
import asyncio
import json
from fastmcp import Client


async def main():
    """Test the MOCK Application MCP Server"""
    
    print("🚀 MOCK Application MCP Server - Test Client")
    print("="*70)
    print("⚠️  Using MOCK data - no real Microsoft credentials needed!")
    print()
    
    async with Client("http://localhost:8001/mcp") as client:
        print("📡 Connecting to mock server...")
        print("✅ Connected!\n")

        # Test 1: List available tools
        print("=" * 70)
        print("TEST 1: List Available Tools")
        print("=" * 70)
        tools_result = await client.call_tool("list_tools", {})
        tools_data = json.loads(tools_result.content[0].text)
        print(f"Found {len(tools_data)} tools:")
        for idx, tool in enumerate(tools_data[:5], 1):
            print(f"  {idx}. {tool['name']}")
        print()
        
        # Test 2: List users
        print("=" * 70)
        print("TEST 2: List Users")
        print("=" * 70)
        users_result = await client.call_tool("list_users", {"limit": 5})
        users = json.loads(users_result.content[0].text)
        print(f"Found {len(users)} mock users:")
        for user in users:
            display_name = user.get('displayName', 'N/A')
            email = user.get('email', 'N/A')
            is_external = user.get('isExternal', False)
            user_type = '(External Guest)' if is_external else '(Internal)'
            print(f"  • {display_name} {user_type}")
            print(f"    Email: {email}")
        print()
        
        # Test 3: Get user profile
        print("=" * 70)
        print("TEST 3: Get User Profile")
        print("=" * 70)
        first_user_email = users[0]['email']
        profile_result = await client.call_tool("get_user_profile", {"user_email": first_user_email})
        profile = json.loads(profile_result.content[0].text)
        print(f"Profile for {first_user_email}:")
        print(f"  Display Name: {profile.get('displayName')}")
        print(f"  Job Title: {profile.get('jobTitle')}")
        print(f"  Department: {profile.get('department')}")
        print(f"  Office: {profile.get('officeLocation')}")
        print()
        
        # Test 4: List emails
        print("=" * 70)
        print("TEST 4: List Emails")
        print("=" * 70)
        emails_result = await client.call_tool("list_emails", {
            "user_email": first_user_email,
            "limit": 5
        })
        emails = json.loads(emails_result.content[0].text)
        print(f"Found {len(emails)} mock emails for {first_user_email}:")
        for idx, email in enumerate(emails, 1):
            print(f"\n  {idx}. {email.get('subject')}")
            print(f"     From: {email.get('from', {}).get('emailAddress', {}).get('name')}")
            print(f"     Date: {email.get('receivedDateTime')}")
            print(f"     Preview: {email.get('bodyPreview', '')[:60]}...")
        print()
        
        # Test 5: Search emails
        print("=" * 70)
        print("TEST 5: Search Emails")
        print("=" * 70)
        search_result = await client.call_tool("search_emails", {
            "user_email": first_user_email,
            "query": "meeting",
            "limit": 3
        })
        search_emails = json.loads(search_result.content[0].text)
        print(f"Found {len(search_emails)} emails matching 'meeting':")
        for idx, email in enumerate(search_emails, 1):
            print(f"  {idx}. {email.get('subject')}")
        print()
        
        # Test 6: List teams
        print("=" * 70)
        print("TEST 6: List Teams")
        print("=" * 70)
        teams_result = await client.call_tool("list_teams", {})
        teams = json.loads(teams_result.content[0].text)
        print(f"Found {len(teams)} mock teams:")
        for team in teams:
            print(f"  • {team.get('displayName')}")
            print(f"    Description: {team.get('description')}")
            print(f"    Members: {team.get('memberCount')}")
        print()
        
        # Test 7: Get team members
        print("=" * 70)
        print("TEST 7: Get Team Members")
        print("=" * 70)
        first_team_id = teams[0]['id']
        members_result = await client.call_tool("get_team_members", {"team_id": first_team_id})
        members = json.loads(members_result.content[0].text)
        print(f"Members of {teams[0]['displayName']}:")
        for member in members:
            print(f"  • {member.get('displayName')} ({member.get('email')})")
        print()
        
        # Test 8: List calendar events
        print("=" * 70)
        print("TEST 8: List Calendar Events")
        print("=" * 70)
        events_result = await client.call_tool("list_calendar_events", {
            "user_email": first_user_email,
            "limit": 3
        })
        events = json.loads(events_result.content[0].text)
        print(f"Found {len(events)} calendar events for {first_user_email}:")
        for idx, event in enumerate(events, 1):
            print(f"\n  {idx}. {event.get('subject')}")
            print(f"     Start: {event.get('start', {}).get('dateTime')}")
            print(f"     Location: {event.get('location', {}).get('displayName')}")
        print()
        
        print("=" * 70)
        print("✅ All tests completed successfully!")
        print("=" * 70)


if __name__ == "__main__":
    print("\n⚠️  Make sure the MOCK server is running:")
    print("   python main_mock.py\n")
    
    asyncio.run(main())
