#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
#     "mcp",
# ]
# ///
"""
Playbook Lab — Unipile LinkedIn MCP (versão estendida)

Baseado no unipile-linkedin-mcp (bhaktatejas922), mantendo a mesma estrutura e
mesmas regras. Adiciona a família de endpoints de POSTS da API da Unipile que
não existia no servidor original:
- Listar posts de um perfil/empresa  (análise de mercado)
- Obter um post específico
- Criar post                          (publicar de verdade)
- Listar e criar comentários
- Listar e enviar reações

Como rodar (deps instaladas automaticamente pelo uv):
    UNIPILE_BASE_URL=... UNIPILE_API_KEY=... UNIPILE_ACCOUNT_ID=... \
        uv run playbook_unipile_mcp.py
"""

import os
import sys
import json
import logging
from typing import Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Configure logging to stderr (not stdout, which is for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("playbook-unipile-linkedin")

# Initialize FastMCP server
mcp = FastMCP("playbook-unipile-linkedin")


class UnipileClient:
    """HTTP client for Unipile API"""

    def __init__(self):
        self.base_url = os.getenv("UNIPILE_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("UNIPILE_API_KEY", "")
        self.account_id = os.getenv("UNIPILE_ACCOUNT_ID", "")

        if not self.base_url or not self.api_key:
            raise ValueError("UNIPILE_BASE_URL and UNIPILE_API_KEY must be set")

        self.headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        account_id: Optional[str] = None
    ) -> dict:
        """Make an HTTP request to the Unipile API (JSON body)."""
        url = f"{self.base_url}{endpoint}"

        if params is None:
            params = {}

        acc_id = account_id or self.account_id
        if acc_id and "account_id" not in params:
            params["account_id"] = acc_id

        if json_data is not None and acc_id:
            if "account_id" not in json_data:
                json_data["account_id"] = acc_id

        logger.info(f"Request: {method} {url}")
        logger.debug(f"Params: {params}, Body: {json_data}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data
            )

            logger.info(f"Response status: {response.status_code}")

            if response.status_code >= 400:
                error_text = response.text
                logger.error(f"API Error: {error_text}")
                return {"error": error_text, "status_code": response.status_code}

            try:
                return response.json()
            except json.JSONDecodeError:
                return {"raw_response": response.text}

    async def request_form(
        self,
        method: str,
        endpoint: str,
        data: dict,
        account_id: Optional[str] = None
    ) -> dict:
        """Make a multipart/form-data request to the Unipile API.

        The Unipile posts endpoint expects multipart/form-data (it supports file
        attachments). We send only text fields here.
        """
        url = f"{self.base_url}{endpoint}"

        acc_id = account_id or self.account_id
        if acc_id and "account_id" not in data:
            data["account_id"] = acc_id

        # Drop None values so they are not sent as the literal string "None"
        data = {k: v for k, v in data.items() if v is not None}

        # Multipart: do NOT set Content-Type manually (httpx sets the boundary)
        headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}

        logger.info(f"Request (form): {method} {url}")
        logger.debug(f"Form data: {data}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                data=data
            )

            logger.info(f"Response status: {response.status_code}")

            if response.status_code >= 400:
                error_text = response.text
                logger.error(f"API Error: {error_text}")
                return {"error": error_text, "status_code": response.status_code}

            try:
                return response.json()
            except json.JSONDecodeError:
                return {"raw_response": response.text}


# Initialize client
client = UnipileClient()


# =============================================================================
# ACCOUNT MANAGEMENT
# =============================================================================

@mcp.tool()
async def list_accounts() -> dict:
    """
    List all connected LinkedIn accounts.

    Returns information about all accounts linked to your Unipile integration,
    including account IDs, status, and provider information.
    """
    return await client.request("GET", "/accounts", params={})


@mcp.tool()
async def get_my_profile() -> dict:
    """
    Get the authenticated user's full LinkedIn profile.

    Returns comprehensive profile data including name, headline, summary,
    experience, education, skills, and more for the currently connected account.
    """
    return await client.request("GET", "/users/me")


# =============================================================================
# LINKEDIN SEARCH (CORE FOCUS)
# =============================================================================

@mcp.tool()
async def search_people(
    keywords: Optional[str] = None,
    location: Optional[list[str]] = None,
    industry: Optional[list[str]] = None,
    company: Optional[list[str]] = None,
    past_company: Optional[list[str]] = None,
    network_distance: Optional[list[int]] = None,
    profile_language: Optional[list[str]] = None,
    limit: int = 25,
    cursor: Optional[str] = None
) -> dict:
    """
    Search for people on LinkedIn using Classic LinkedIn filters.

    This is the standard LinkedIn search available to all users.
    Use get_search_params() to find valid IDs for location, industry, and company filters.

    Args:
        keywords: Free text search (name, title, company, etc.)
        location: List of location IDs (use get_search_params to find IDs)
        industry: List of industry IDs
        company: List of current company IDs
        past_company: List of past company IDs
        network_distance: Connection degree [1, 2, 3] - 1=1st degree, 2=2nd degree, 3=3rd+
        profile_language: ISO language codes (e.g., ["en", "fr"])
        limit: Max results per page (1-50, default 25)
        cursor: Pagination cursor from previous response

    Returns:
        Search results with profiles and pagination cursor
    """
    body = {
        "api": "classic",
        "category": "people",
        "limit": min(limit, 50)
    }

    if keywords:
        body["keywords"] = keywords
    if location:
        body["location"] = location
    if industry:
        body["industry"] = industry
    if company:
        body["company"] = company
    if past_company:
        body["past_company"] = past_company
    if network_distance:
        body["network_distance"] = network_distance
    if profile_language:
        body["profile_language"] = profile_language
    if cursor:
        body["cursor"] = cursor

    return await client.request("POST", "/linkedin/search", json_data=body)


@mcp.tool()
async def search_people_sales_nav(
    keywords: Optional[str] = None,
    location: Optional[list[str]] = None,
    industry: Optional[list[str]] = None,
    company: Optional[list[str]] = None,
    past_company: Optional[list[str]] = None,
    network_distance: Optional[list[int]] = None,
    profile_language: Optional[list[str]] = None,
    tenure: Optional[dict] = None,
    seniority_level: Optional[list[str]] = None,
    function: Optional[list[str]] = None,
    company_headcount: Optional[list[dict]] = None,
    changed_jobs: Optional[bool] = None,
    posted_on_linkedin: Optional[bool] = None,
    limit: int = 25,
    cursor: Optional[str] = None
) -> dict:
    """
    Search for people using LinkedIn Sales Navigator (requires Sales Nav subscription).

    Sales Navigator provides advanced filters not available in Classic LinkedIn.
    Use get_search_params() to find valid IDs for filters.

    Args:
        keywords: Free text search
        location: List of location IDs
        industry: List of industry IDs
        company: List of current company IDs
        past_company: List of past company IDs
        network_distance: Connection degree [1, 2, 3]
        profile_language: ISO language codes
        tenure: Years at current company, e.g., {"min": 1, "max": 5}
        seniority_level: Job levels (e.g., ["Director", "VP", "CXO"])
        function: Job functions (e.g., ["Engineering", "Sales"])
        company_headcount: Company size ranges, e.g., [{"min": 51, "max": 200}]
        changed_jobs: True to find people who recently changed jobs
        posted_on_linkedin: True to find active LinkedIn posters
        limit: Max results per page (1-100, default 25)
        cursor: Pagination cursor from previous response

    Returns:
        Search results with profiles and pagination cursor
    """
    body = {
        "api": "sales_navigator",
        "category": "people",
        "limit": min(limit, 100)
    }

    if keywords:
        body["keywords"] = keywords
    if location:
        body["location"] = location
    if industry:
        body["industry"] = industry
    if company:
        body["company"] = company
    if past_company:
        body["past_company"] = past_company
    if network_distance:
        body["network_distance"] = network_distance
    if profile_language:
        body["profile_language"] = profile_language
    if tenure:
        body["tenure"] = tenure
    if seniority_level:
        body["seniority_level"] = seniority_level
    if function:
        body["function"] = function
    if company_headcount:
        body["company_headcount"] = company_headcount
    if changed_jobs is not None:
        body["changed_jobs"] = changed_jobs
    if posted_on_linkedin is not None:
        body["posted_on_linkedin"] = posted_on_linkedin
    if cursor:
        body["cursor"] = cursor

    return await client.request("POST", "/linkedin/search", json_data=body)


@mcp.tool()
async def search_companies(
    keywords: Optional[str] = None,
    industry: Optional[list[str]] = None,
    location: Optional[list[str]] = None,
    headcount_min: Optional[int] = None,
    headcount_max: Optional[int] = None,
    has_job_offers: Optional[bool] = None,
    limit: int = 25,
    cursor: Optional[str] = None
) -> dict:
    """
    Search for companies on LinkedIn.

    Use get_search_params() to find valid IDs for industry and location filters.

    Args:
        keywords: Company name or description keywords
        industry: List of industry IDs
        location: List of location IDs (headquarters)
        headcount_min: Minimum employee count
        headcount_max: Maximum employee count
        has_job_offers: True to find companies currently hiring
        limit: Max results per page (1-50, default 25)
        cursor: Pagination cursor from previous response

    Returns:
        Search results with company profiles and pagination cursor
    """
    body = {
        "api": "classic",
        "category": "companies",
        "limit": min(limit, 50)
    }

    if keywords:
        body["keywords"] = keywords
    if industry:
        body["industry"] = industry
    if location:
        body["location"] = location
    if headcount_min is not None or headcount_max is not None:
        body["headcount"] = {}
        if headcount_min is not None:
            body["headcount"]["min"] = headcount_min
        if headcount_max is not None:
            body["headcount"]["max"] = headcount_max
    if has_job_offers is not None:
        body["has_job_offers"] = has_job_offers
    if cursor:
        body["cursor"] = cursor

    return await client.request("POST", "/linkedin/search", json_data=body)


@mcp.tool()
async def search_posts(
    keywords: str,
    sort_by: Optional[str] = None,
    date_posted: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = 25,
    cursor: Optional[str] = None
) -> dict:
    """
    Search for LinkedIn posts/content.

    Args:
        keywords: Content keywords to search for (required)
        sort_by: "relevance" or "date" (default: relevance)
        date_posted: "past_day", "past_week", or "past_month"
        content_type: "videos", "images", or "documents"
        limit: Max results per page (1-50, default 25)
        cursor: Pagination cursor from previous response

    Returns:
        Search results with posts and pagination cursor
    """
    body = {
        "api": "classic",
        "category": "posts",
        "keywords": keywords,
        "limit": min(limit, 50)
    }

    if sort_by:
        body["sort_by"] = sort_by
    if date_posted:
        body["date_posted"] = date_posted
    if content_type:
        body["content_type"] = content_type
    if cursor:
        body["cursor"] = cursor

    return await client.request("POST", "/linkedin/search", json_data=body)


@mcp.tool()
async def get_search_params(
    param_type: str,
    query: Optional[str] = None
) -> dict:
    """
    Get valid parameter IDs for search filters.

    LinkedIn search filters require specific IDs (not names). Use this tool
    to look up the IDs for locations, industries, companies, etc.

    Args:
        param_type: Parameter type (case-insensitive) - one of:
            Common parameters:
            - "LOCATION" - Geographic locations
            - "INDUSTRY" - Industry categories
            - "COMPANY" - Companies
            - "SCHOOL" - Educational institutions
            - "PEOPLE" - People
            - "CONNECTIONS" - Connections
            - "SERVICE" - Services
            - "JOB_FUNCTION" - Job functions
            - "JOB_TITLE" - Job titles
            - "EMPLOYMENT_TYPE" - Employment types
            - "SKILL" - Skills

            Sales Navigator specific:
            - "REGION" - Regions
            - "DEPARTMENT" - Departments
            - "PERSONA" - Personas

        query: Optional search string to filter results (e.g., "San Francisco")

    Returns:
        List of valid parameter IDs and names for the specified type
    """
    params = {"type": param_type.upper()}
    if query:
        params["q"] = query

    return await client.request("GET", "/linkedin/search/parameters", params=params)


# =============================================================================
# PROFILE OPERATIONS
# =============================================================================

@mcp.tool()
async def get_profile(
    provider_id: str,
    sections: Optional[list[str]] = None
) -> dict:
    """
    Get a LinkedIn user's full profile by their provider ID.

    Args:
        provider_id: The LinkedIn provider ID (from search results or profile URL)
        sections: Optional list of sections to include. Available sections:
            - about
            - experience
            - education
            - skills
            - certifications
            - languages
            - volunteering_experience
            - projects
            - recommendations_received
            - recommendations_given
            If not specified, returns all available sections.

    Returns:
        Full profile data including requested sections
    """
    params = {}
    if sections:
        params["sections"] = ",".join(sections)

    return await client.request("GET", f"/users/{provider_id}", params=params)


@mcp.tool()
async def get_company_profile(company_id: str) -> dict:
    """
    Get a company's LinkedIn profile/page details.

    Args:
        company_id: The LinkedIn company ID or vanity URL name

    Returns:
        Company profile data including description, industry, size, specialties, etc.
    """
    return await client.request("GET", f"/linkedin/company/{company_id}")


# =============================================================================
# CONNECTIONS & INVITATIONS
# =============================================================================

@mcp.tool()
async def send_invitation(
    provider_id: str,
    message: Optional[str] = None
) -> dict:
    """
    Send a connection request to a LinkedIn user.

    Note: LinkedIn limits invitation messages to 300 characters.
    Daily limits apply: ~80-100/day for paid accounts, ~15/week for free.

    Args:
        provider_id: The LinkedIn provider ID of the person to connect with
        message: Optional personalized message (max 300 characters)

    Returns:
        Confirmation of invitation sent or error
    """
    body = {"provider_id": provider_id}

    if message:
        if len(message) > 300:
            return {"error": "Invitation message must be 300 characters or less"}
        body["message"] = message

    return await client.request("POST", "/users/invite", json_data=body)


@mcp.tool()
async def list_invitations_sent(
    limit: int = 50,
    cursor: Optional[str] = None
) -> dict:
    """
    List pending outbound connection requests.

    Args:
        limit: Max results per page (default 50)
        cursor: Pagination cursor from previous response

    Returns:
        List of pending sent invitations with recipient details
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    return await client.request("GET", "/users/invite/sent", params=params)


@mcp.tool()
async def list_invitations_received(
    limit: int = 50,
    cursor: Optional[str] = None
) -> dict:
    """
    List inbound connection requests awaiting response.

    Args:
        limit: Max results per page (default 50)
        cursor: Pagination cursor from previous response

    Returns:
        List of pending received invitations with sender details
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    return await client.request("GET", "/users/invite/received", params=params)


@mcp.tool()
async def accept_invitation(invitation_id: str) -> dict:
    """
    Accept a received connection request.

    Args:
        invitation_id: The ID of the invitation to accept (from list_invitations_received)

    Returns:
        Confirmation of acceptance
    """
    return await client.request("POST", f"/users/invite/received/{invitation_id}", json_data={"action": "accept"})


@mcp.tool()
async def decline_invitation(invitation_id: str) -> dict:
    """
    Decline a received connection request.

    Args:
        invitation_id: The ID of the invitation to decline (from list_invitations_received)

    Returns:
        Confirmation of decline
    """
    return await client.request("POST", f"/users/invite/received/{invitation_id}", json_data={"action": "decline"})


@mcp.tool()
async def cancel_invitation(invitation_id: str) -> dict:
    """
    Withdraw a sent connection request that hasn't been accepted yet.

    Args:
        invitation_id: The ID of the sent invitation to cancel (from list_invitations_sent)

    Returns:
        Confirmation of cancellation
    """
    return await client.request("DELETE", f"/users/invite/{invitation_id}")


@mcp.tool()
async def list_relations(
    limit: int = 50,
    cursor: Optional[str] = None
) -> dict:
    """
    List your 1st degree connections on LinkedIn.

    Args:
        limit: Max results per page (default 50)
        cursor: Pagination cursor from previous response

    Returns:
        List of connections with profile summaries
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    return await client.request("GET", "/users/relations", params=params)


# =============================================================================
# MESSAGING
# =============================================================================

@mcp.tool()
async def list_chats(
    limit: int = 50,
    cursor: Optional[str] = None,
    unread_only: bool = False
) -> dict:
    """
    List LinkedIn message conversations.

    Args:
        limit: Max results per page (default 50)
        cursor: Pagination cursor from previous response
        unread_only: If True, only return chats with unread messages

    Returns:
        List of chat conversations with latest message preview
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    if unread_only:
        params["unread"] = "true"

    return await client.request("GET", "/chats", params=params)


@mcp.tool()
async def get_chat_messages(
    chat_id: str,
    limit: int = 50,
    cursor: Optional[str] = None
) -> dict:
    """
    Get messages from a specific chat conversation.

    Args:
        chat_id: The chat/conversation ID (from list_chats)
        limit: Max messages per page (default 50)
        cursor: Pagination cursor from previous response

    Returns:
        List of messages in the chat with sender info and timestamps
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    return await client.request("GET", f"/chats/{chat_id}/messages", params=params)


@mcp.tool()
async def send_message(
    chat_id: str,
    text: str
) -> dict:
    """
    Send a message in an existing chat conversation.

    Use this for ongoing conversations with existing connections.
    For new conversations, use start_chat instead.

    Args:
        chat_id: The chat/conversation ID (from list_chats)
        text: The message content to send

    Returns:
        Confirmation with sent message details
    """
    body = {"text": text}

    return await client.request("POST", f"/chats/{chat_id}/messages", json_data=body)


@mcp.tool()
async def start_chat(
    attendees_ids: list[str],
    text: str
) -> dict:
    """
    Start a new conversation with one or more LinkedIn users.

    Use this to initiate messaging with 1st degree connections.
    For non-connections (2nd/3rd degree), use send_inmail instead.

    Args:
        attendees_ids: List of LinkedIn provider IDs to message
        text: The initial message content

    Returns:
        New chat details including chat_id for follow-up messages
    """
    body = {
        "attendees_ids": attendees_ids,
        "text": text
    }

    return await client.request("POST", "/chats", json_data=body)


# =============================================================================
# INMAIL (PREMIUM)
# =============================================================================

@mcp.tool()
async def send_inmail(
    attendees_ids: list[str],
    subject: str,
    text: str
) -> dict:
    """
    Send an InMail message to non-connections (requires LinkedIn Premium or Sales Navigator).

    InMail allows you to message 2nd and 3rd degree connections without
    connecting first. Uses InMail credits - check get_inmail_credits() first.

    Args:
        attendees_ids: List of LinkedIn provider IDs to message
        subject: InMail subject line (required for InMail)
        text: The message body content

    Returns:
        Confirmation with sent InMail details
    """
    body = {
        "attendees_ids": attendees_ids,
        "subject": subject,
        "text": text,
        "linkedin": {
            "inmail": True
        }
    }

    return await client.request("POST", "/chats", json_data=body)


@mcp.tool()
async def get_inmail_credits() -> dict:
    """
    Check remaining InMail credits for the connected LinkedIn account.

    InMail credits are used when messaging non-connections.
    Premium users get a monthly allocation that varies by subscription tier.

    Returns:
        Current InMail credit balance and any additional quota info
    """
    return await client.request("GET", "/linkedin/inmail_balance")


# =============================================================================
# POSTS, COMMENTS & REACTIONS  (NOVO — extensão Playbook Lab)
# =============================================================================
# IMPORTANTE sobre IDs de post:
# O LinkedIn usa vários IDs para o mesmo post. Para QUALQUER ação de escrita
# (comentar, reagir, repostar) use sempre o "social_id" retornado pela API
# (ex: "urn:li:activity:7473064432252887041"), não o número solto da URL.
# Os endpoints de leitura (get_user_posts, get_post) já devolvem o social_id.

@mcp.tool()
async def get_user_posts(
    provider_id: str,
    limit: int = 10,
    cursor: Optional[str] = None
) -> dict:
    """
    List the posts published by a specific LinkedIn user OR company.

    Great for market analysis: see what a prospect, competitor, or thought
    leader has been posting, including engagement metrics (reactions, comments,
    impressions) and each post's social_id for further interactions.

    Args:
        provider_id: The LinkedIn provider ID of the person (e.g.
            "ACoAAB0wd3QBlaiZ85t5PUw7PrlPxbgp4GWJKz4") or the company ID.
            Note: the public vanity name (e.g. "victorzbaggio") does NOT work
            here — resolve it first with get_profile/search if needed.
        limit: Max posts to return (default 10)
        cursor: Pagination cursor from previous response

    Returns:
        List of posts with text, engagement counters, attachments and social_id
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    return await client.request("GET", f"/users/{provider_id}/posts", params=params)


@mcp.tool()
async def get_post(post_id: str) -> dict:
    """
    Retrieve a single LinkedIn post by its id.

    Useful to resolve the reliable "social_id" of a post before commenting or
    reacting, and to read the full post content and engagement metrics.

    Args:
        post_id: The post id or social_id (e.g. "urn:li:activity:7473064432252887041")

    Returns:
        Full post details including text, author, counters and social_id
    """
    return await client.request("GET", f"/posts/{post_id}")


@mcp.tool()
async def create_post(
    text: str,
    as_organization: Optional[str] = None,
    external_link: Optional[str] = None,
    repost_id: Optional[str] = None
) -> dict:
    """
    Publish a new post on LinkedIn from the connected account.

    Sent as multipart/form-data (the Unipile posts endpoint supports file
    attachments; this tool sends text-only content).

    Args:
        text: The post content/body
        as_organization: Optional LinkedIn company/organization ID to post as a
            company page instead of the personal profile
        external_link: Optional URL to attach as a link preview
        repost_id: Optional social_id of an existing post to repost/share

    Returns:
        Confirmation with the created post id/social_id, or error
    """
    data = {"text": text}
    if as_organization:
        data["as_organization"] = as_organization
    if external_link:
        data["external_link"] = external_link
    if repost_id:
        data["repost"] = repost_id

    return await client.request_form("POST", "/posts", data=data)


@mcp.tool()
async def list_post_comments(
    post_social_id: str,
    limit: int = 25,
    cursor: Optional[str] = None
) -> dict:
    """
    List the comments on a LinkedIn post.

    Useful for market analysis and warm prospecting (who is engaging with a
    given post).

    Args:
        post_social_id: The post's social_id (e.g. "urn:li:activity:7473...")
        limit: Max comments per page (default 25)
        cursor: Pagination cursor from previous response

    Returns:
        List of comments with author info and text
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    return await client.request("GET", f"/posts/{post_social_id}/comments", params=params)


@mcp.tool()
async def comment_on_post(
    post_social_id: str,
    text: str,
    comment_id: Optional[str] = None
) -> dict:
    """
    Post a comment on a LinkedIn post (or reply to an existing comment).

    Args:
        post_social_id: The post's social_id (e.g. "urn:li:activity:7473...")
        text: The comment content
        comment_id: Optional id of a comment to reply to (threaded reply)

    Returns:
        Confirmation with the created comment details, or error
    """
    body = {"text": text}
    if comment_id:
        body["comment_id"] = comment_id

    return await client.request("POST", f"/posts/{post_social_id}/comments", json_data=body)


@mcp.tool()
async def list_post_reactions(
    post_social_id: str,
    limit: int = 25,
    cursor: Optional[str] = None
) -> dict:
    """
    List the reactions on a LinkedIn post (who reacted and how).

    Useful for warm prospecting from people who engaged with a post.

    Args:
        post_social_id: The post's social_id (e.g. "urn:li:activity:7473...")
        limit: Max reactions per page (default 25)
        cursor: Pagination cursor from previous response

    Returns:
        List of reactions with author info and reaction type
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    return await client.request("GET", f"/posts/{post_social_id}/reactions", params=params)


@mcp.tool()
async def react_to_post(
    post_social_id: str,
    reaction_type: str = "like"
) -> dict:
    """
    Add a reaction to a LinkedIn post.

    Args:
        post_social_id: The post's social_id (e.g. "urn:li:activity:7473...")
        reaction_type: One of LinkedIn's reaction types. Common values:
            "like", "celebrate", "support", "love", "insightful", "funny".
            (The API validates the value.)

    Returns:
        Confirmation of the reaction, or error
    """
    body = {"reaction_type": reaction_type}

    return await client.request("POST", f"/posts/{post_social_id}/reactions", json_data=body)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
