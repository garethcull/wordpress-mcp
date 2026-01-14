# Install Modules
from datetime import datetime
import json
import uuid
import os
import base64
import requests
from requests.auth import HTTPBasicAuth
import mimetypes
import uuid
from urllib.parse import urlparse
import os

# =============================================================================
# Variables
# =============================================================================

# Wordpress Settings
wordpress_username = os.getenv("WORDPRESS_USERNAME")
application_password = os.getenv("APPLICATION_PASSWORD")
site_url = os.getenv("WORDPRESS_SITE_URL")

# Blank wordpress template to post html page
# This must be created and added to your current active template folder
template_id = "page-full-html.php"

# =============================================================================
# MCP Protocol Request Routing
# =============================================================================

def handle_request(method, params):
    """
    Main request router for MCP (Model Context Protocol) JSON-RPC methods.
    Supported:
      - initialize
      - tools/list
      - tools/call
    Notifications (notifications/*) are handled in app.py (204 No Content).
    """
    if method == "initialize":
        return handle_initialize()
    elif method == "tools/list":
        return handle_tools_list()
    elif method == "tools/call":
        return handle_tool_call(params)
    else:
        # Let app.py wrap unknown methods into a proper JSON-RPC error
        raise ValueError(f"Method not found: {method}")


# =============================================================================
# MCP Protocol Handlers
# =============================================================================

def handle_initialize():
    """
    JSON-RPC initialize response.
    Keep protocolVersion consistent with your current implementation.
    """
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "wordpress_mcp",
            "version": "0.1.0"
        },
        "capabilities": {
            "tools": {}
        }
    }


def handle_tools_list():
    """
    JSON-RPC tools/list result.
    IMPORTANT: For JSON-RPC MCP, schema field is camelCase: inputSchema
    """
    return {
        "tools": [            
            {
                "name": "get_wordpress_site_details",
                "description": "Get domain details and a list of pages and blog posts that have been published on the wordpress site.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string", 
                            "description": "The user query requesting site details for the MCP Connector."
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "get_wordpress_content_by_id",
                "description": "Get WordPress content for a specific page or blog post by its ID.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content_id": {
                            "type": "integer", 
                            "description": "The numeric ID of the WordPress content."
                        },
                        "content_type": {
                            "type": "string", 
                            "enum": ["page", "post"],
                            "description": "The type of WordPress content to retrieve."
                        }
                    },
                    "required": ["content_id", "content_type"],
                    "additionalProperties": False
                }
            },
            {
                "name": "publish_new_page_to_wordpress",
                "description": "Publishes a fully prepared HTML landing page to WordPress, automatically embedding Google Tag Manager and adding validated SEO friendly structured data.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "string", 
                            "description": "The full HTML content of the landing page to be published."
                        },
                        "title": {
                            "type": "string", 
                            "description": "The title of the web page that is being published."
                        },
                        "slug": {
                            "type": "string", 
                            "description": "The page path or seo slug that this html page will be published to. (eg. products/prototypr-ai)"
                        },
                        "page_id": {
                            "type": "string", 
                            "description": "The id of the page to be updated. If no id is present, please default to New."
                        },
                        "status": {
                            "type": "string", 
                            "enum": ["publish", "draft"],
                            "description": "Set the publish status of a page to publish or draft. "
                        }
                    },
                    "required": ["html", "title", "slug", "page_id"],
                    "additionalProperties": False
                }
            },
            {
                "name": "get_wordpress_image_assets",
                "description": "Returns an object of image assets for the WordPress site.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string", 
                            "description": "The user query requesting site details for the MCP Connector."
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            },
            {
                "name": "upload_image_to_wordpress",
                "description": "Upload an image to WordPress from either a base64 string or a source URL and return a normalized image asset object.",
                "annotations": {"read_only": False},
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "img_type": {
                            "type": "string", 
                            "enum": ["base64", "src_url"],
                            "description": "How the image is provided"
                        },
                        "base64_img": {
                            "type": "string", 
                            "description": "Base64-encoded image data. Required when img_type is 'base64'."
                        },
                        "img_src": {
                            "type": "string", 
                            "description": "Public URL of an image. Required when img_type is 'src_url'."
                        },
                        "title": {
                            "type": "string", 
                            "description": "Optional title for the image attachment in WordPress"
                        },
                        "alt_text": {
                            "type": "string", 
                            "description": "Optional alt text for the image (accessibility and semantic context)."
                        }
                    },
                    "required": ["img_type"],
                    "additionalProperties": False
                }
            }
        ]
    }



def handle_tool_call(params):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    # Decode string args if needed
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except Exception:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "Invalid arguments: expected object or JSON string."}]
            }

    if tool_name == "get_wordpress_site_details":
        data = get_all_posts_and_pages(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}   

    elif tool_name == "get_wordpress_content_by_id":
        data = get_wordpress_content_by_id(arguments)
        return {"content": [{"type": "text", "text": str(data)}]}   
    
    elif tool_name == "publish_new_page_to_wordpress":
        data = publish_new_page_to_wordpress(arguments)
        return {"content": [{"type": "text", "text": str(data)}]} 

    elif tool_name == "get_wordpress_image_assets":
        data = get_wordpress_image_assets(arguments)
        return {"content": [{"type": "text", "text": str(data)}]} 

    elif tool_name == "upload_image_to_wordpress":
        data = upload_image_to_wordpress(arguments)
        return {"content": [{"type": "text", "text": str(data)}]} 
    
    else:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Tool not found: {tool_name}"}]
        }


# =============================================================================
# Wordpress Functions
# =============================================================================


def fetch_wordpress_items(endpoint, per_page=100):
    """
    Fetch all items from a WordPress REST endpoint.

    :param endpoint: Full WordPress REST endpoint URL
    :param per_page: Number of items per request (max 100)
    :return: List of normalized items
    """
    page_number = 1
    items = []

    while True:
        response = requests.get(
            endpoint,
            params={
                "per_page": per_page,
                "page": page_number,
                "_fields": "id,slug,type,link,title,date,modified"
            }
        )

        # WordPress returns 400 when page exceeds bounds
        if response.status_code == 400:
            break

        response.raise_for_status()
        data = response.json()

        if not data:
            break

        for item in data:
            items.append({
                "id": item.get("id"),
                "title": item.get("title", {}).get("rendered"),
                "url": item.get("link"),
                "type": item.get("type"),
                "date": item.get("date"),
                "modified": item.get("modified"),
            })

        page_number += 1

    return items


def get_all_posts_and_pages(arguments):
    """
    Fetch all WordPress posts and pages and return them grouped by type.

    :param site_url: Base WordPress URL (e.g. https://example.com)
    :param per_page: Number of items per request (max 100)
    :return: Dict with 'posts' and 'pages' keys
    """

    query = arguments.get("query")

    # Current Max Limit 
    per_page = 100

    # Wordpress Endpoints
    posts_endpoint = f"{site_url}/wp-json/wp/v2/posts"
    pages_endpoint = f"{site_url}/wp-json/wp/v2/pages"

    # Fetch wordpress data
    posts = fetch_wordpress_items(posts_endpoint, per_page)
    pages = fetch_wordpress_items(pages_endpoint, per_page)

    return {
        "domain": site_url,
        "posts": posts,
        "pages": pages
    }



def get_wordpress_content_by_id(arguments):
    """
    Fetch a single WordPress post or page by ID.

    :param site_url: Base WordPress URL (e.g. https://example.com)
    :param content_id: WordPress ID of the content
    :param content_type: 'post' or 'page'
    :return: Normalized content dictionary or None
    """

    content_id = arguments.get("content_id")
    content_type = arguments.get("content_type")

    if content_type not in ["post", "page"]:
        raise ValueError("content_type must be 'post' or 'page'")

    endpoint = f"{site_url}/wp-json/wp/v2/{content_type}s/{content_id}"

    response = requests.get(
        endpoint,
        params={
            "_fields": "id,date,modified,slug,status,type,link,title,content"
        }
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    item = response.json()

    return {
        "id": item.get("id"),
        "date": item.get("date"),
        "modified": item.get("modified"),
        "slug": item.get("slug"),
        "status": item.get("status"),
        "type": item.get("type"),
        "link": item.get("link"),
        "title": {
            "rendered": item.get("title", {}).get("rendered")
        },
        "content": {
            "rendered": item.get("content", {}).get("rendered")
        }
    }



def publish_new_page_to_wordpress(arguments):
    """
    Fetches the schema for a specific BigQuery table and returns it
    as a list of dictionaries.

    Args:        
        table_id (string): ID of the table to get the schema for e.g. "prototypr-ai.llm_brand_visibility.brand_questions_to_monitor"

    def create_wp_page_with_slug(username, app_password, site_url, slug, html_content):

    Returns:
        schema_list (list): List of dictionaries representing the schema
    """

    slug = arguments.get("slug")
    html_content = arguments.get("html")
    title = arguments.get("title")
    page_id = arguments.get("page_id")
    status = arguments.get("status")

    if page_id == "New":
        # WordPress Pages Endpoint
        endpoint = f"{site_url}/wp-json/wp/v2/pages"
        method = "POST"

    else:
        endpoint = f"{site_url}/wp-json/wp/v2/pages/{page_id}"
        method = "PUT"


    payload = {
        "title": title,
        "slug": slug,
        "content": html_content,
        "template": template_id,
        "status": status
    }

    if method == "POST":
        # create a new page
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            auth=HTTPBasicAuth(wordpress_username, application_password)
        )
    else:
        # update an existing page by its id
        response = requests.put(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            auth=HTTPBasicAuth(wordpress_username, application_password)
        )

    print("STATUS:", response.status_code)
    print("RAW RESPONSE:", response.text)

    try:
        return response.json()
    except:
        return {"error": "Invalid JSON returned"}


def get_wordpress_image_assets(arguments):

    """
    # Build the WordPress REST API endpoint for image media items
    # media_type=image ensures only images are returned
    # per_page=100 is the maximum number WordPress allows per request
    """

    query = arguments.get("query")

    endpoint = f"{site_url}/wp-json/wp/v2/media?media_type=image&per_page=100"

    # Make the HTTP GET request to WordPress
    response = requests.get(endpoint)

    # If the request fails, log the error and return an empty list
    if response.status_code != 200:
        print("Error:", response.text)
        return []

    # Parse the JSON response into Python objects
    media_items = response.json()

    # Prepare a list to hold normalized image asset data
    results = []

    # Iterate over each media item returned by WordPress
    for item in media_items:
        # Unique WordPress ID for the image
        img_id = item.get("id")

        # Date the image was uploaded
        timestamp = item.get("date")

        # Public URL to the image file
        src = item.get("source_url")

        # Alternative text for accessibility (may be empty)
        alt = item.get("alt_text", "")

        # File path/name as stored by WordPress
        file_name = item.get("media_details", {}).get("file", "")

        # Original image dimensions
        dimensions = {
            "width": item.get("media_details", {}).get("width"),
            "height": item.get("media_details", {}).get("height")
        }

        # Append the normalized image object to the results list
        results.append({
            "img_id": img_id,
            "date": timestamp,
            "src": src,
            "file_name": file_name,
            "alt": alt,
            "dimensions": dimensions
        })

    # Return the full list of image assets
    return results


def upload_image_to_wordpress(arguments):
    
    """
    MCP tool: upload an image to WordPress from base64 or src_url.
    """

    username = wordpress_username
    app_password = application_password

    img_type = arguments.get("img_type")
    base64_img = arguments.get("base64_img")
    img_src = arguments.get("img_src")
    title = arguments.get("title")
    alt_text = arguments.get("alt_text")

    endpoint = f"{site_url}/wp-json/wp/v2/media"

    # -----------------------------------
    # Normalize input → base64
    # -----------------------------------
    if img_type == "src_url":
        if not img_src:
            raise ValueError("img_src is required when img_type='src_url'")

        response = requests.get(
            img_src,
            timeout=30,
            headers={"User-Agent": "prototypr.ai"}
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            raise ValueError(
                f"URL did not return an image. Content-Type={content_type}"
            )

        base64_img = base64.b64encode(response.content).decode("utf-8")

        parsed = urlparse(img_src)
        filename = os.path.basename(parsed.path)
        if not filename:
            ext = content_type.split("/")[-1]
            filename = f"upload-{uuid.uuid4().hex}.{ext}"

        if not title:
            title = os.path.splitext(filename)[0].replace("-", " ").replace("_", " ")

        if not alt_text:
            alt_text = title

    elif img_type == "base64":
        if not base64_img:
            raise ValueError("base64_img is required when img_type='base64'")

        filename = f"upload-{uuid.uuid4().hex}.png"

        if not title:
            title = "Uploaded image"

        if not alt_text:
            alt_text = title

    else:
        raise ValueError("img_type must be 'base64' or 'src_url'")

    # -----------------------------------
    # Decode base64 → raw bytes
    # -----------------------------------
    image_bytes = base64.b64decode(base64_img)
    if not image_bytes:
        raise ValueError("Decoded image bytes are empty")

    # -----------------------------------
    # Detect mime type
    # -----------------------------------
    mime_type, _ = mimetypes.guess_type(filename)
    mime_type = mime_type or "application/octet-stream"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": mime_type
    }

    # -----------------------------------
    # Upload to WordPress
    # -----------------------------------
    wp_response = requests.post(
        endpoint,
        headers=headers,
        data=image_bytes,
        auth=(username, app_password),
        timeout=30
    )

    if wp_response.status_code not in [200, 201]:
        raise RuntimeError(
            f"Upload failed: {wp_response.status_code} {wp_response.text}"
        )

    item = wp_response.json()
    if isinstance(item, list):
        item = item[0]

    media_id = item.get("id")

    # -----------------------------------
    # Update title and alt text
    # -----------------------------------
    meta_payload = {
        "title": title,
        "alt_text": alt_text
    }

    requests.post(
        f"{endpoint}/{media_id}",
        json=meta_payload,
        auth=(username, app_password),
        timeout=20
    )

    # -----------------------------------
    # Normalize output
    # -----------------------------------
    return {
        "id": media_id,
        "date": item.get("date"),
        "src": item.get("source_url"),
        "file_name": item.get("media_details", {}).get("file"),
        "title": title,
        "alt_text": alt_text,
        "dimensions": {
            "width": item.get("media_details", {}).get("width"),
            "height": item.get("media_details", {}).get("height")
        }
    }



