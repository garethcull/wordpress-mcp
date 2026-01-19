# WordPress MCP Server

[![Run on Google Cloud](https://www.prototypr.ai/static/img/run_on_google_cloud_cta.webp)](https://deploy.cloud.run?git_repo=https://github.com/garethcull/wordpress-mcp)

A Model Context Protocol (MCP) server that exposes WordPress pages, posts, and media assets to MCP clients such as Prototypr.ai, Cursor, or OpenAI’s Responses API.

This MCP Server is implemented as a Python application and can run locally, on Google Cloud Run, or on your own infrastructure.

---

## WordPress MCP Tools

This WordPress MCP Server provides MCP tools to help marketing teams, designers, and AI agents work directly with WordPress:

- get_wordpress_site_details  
- get_wordpress_content_by_id  
- publish_new_page_to_wordpress  
- get_wordpress_image_assets  
- upload_image_to_wordpress  

These tools enable natural‑language and programmatic workflows such as:

- Exploring site structure (pages and posts)  
- Pulling existing WordPress content into AI workflows  
- Publishing fully‑formed HTML landing pages  
- Reusing and remixing existing image assets  
- Saving generated images back to the WordPress media library  

---

## Authentication

This MCP server requires authorization via a shared token (MCP_TOKEN).

All requests to the /mcp endpoint must include:

Authorization: Bearer MCP_TOKEN

This token is validated in app.py.

---

## Set Up Your Environment

### Create a Virtual Environment

You can use standard Python venv, Anaconda, or any environment manager you prefer.

Recommended: Anaconda Navigator

1. Open Anaconda Navigator  
2. Go to Environments  
3. Create a new environment (Python 3.11 recommended)  
4. Activate it before running the project  

This provides an isolated environment and avoids dependency conflicts.

---

### Install Dependencies

From the root of the repo:

bash  
pip install -r requirements.txt

---

### Configure Environment Variables

The following environment variables must be set:

- WORDPRESS_SITE_URL  
  Base URL of your WordPress site (for example https://example.com)

- WORDPRESS_USERNAME  
  WordPress username with Application Password access

- APPLICATION_PASSWORD  
  WordPress Application Password (not your main password)

- MCP_TOKEN  
  Shared secret used to authenticate MCP requests

These variables are referenced in app.py and mcp_helper.py.

---

## Optional: Full‑Fidelity HTML Page Publishing

By default, WordPress applies formatting filters that can modify raw HTML.

To publish pages exactly as designed (1:1 HTML output), add a lightweight page template to your active WordPress theme.

### Why This Exists

- Prevents WordPress from altering generated HTML  
- Ensures pixel‑perfect parity with AI‑generated or human HTML output  
- Scoped only to pages using this template  

### Add the Template

Create a file named *page-full-html.php* in your ACTIVE theme. Use a Wordpress plugin like Filester - WordPress File Manager Pro (which is what I used) to upload the page-full-html.php file to your active theme drectory like this:

/wp-content/themes/your-theme/page-full-html.php

Paste the following as a php file.

```php
<?php
/*
Template Name: Full HTML Output
Template Post Type: page
*/
remove_filter('the_content', 'wptexturize');
remove_filter('the_content', 'wpautop');

while ( have_posts() ) : the_post();
  echo get_post_field('post_content', get_the_ID());
endwhile;

exit;
```

---

## Configuring Your MCP Client

### prototypr.ai MCP Client

This MCP server was originally designed to work with the prototypr.ai MCP Client.

To connect:

1. Open your AI Workspace in prototypr.ai  
2. Click MCP Tools  
3. Add a new server  
4. Paste the configuration below  

```json  
{  
  "wordpress-mcp": {  
    "url": "https://<google cloud run domain>/mcp",  
    "displayName": "WordPress MCP",  
    "description": "A custom WordPress MCP Server to support content creation and publishing. Developed by protorypr.ai.",  
    "icon": "https://upload.wikimedia.org/wikipedia/commons/9/98/WordPress_blue_logo.svg",  
    "headers": {  
      "Authorization": "Bearer MCP_TOKEN"  
    },  
    "transport": "stdio"  
  }  
}
```

The Prototypr.ai Studio integration builds a visual publishing and asset‑remixing experience on top of this MCP and requires a Plus membership.

---

### Other MCP Clients (Cursor, OpenAI Responses API)

You can also connect this MCP to other MCP‑compatible clients.

Example for OpenAI’s Responses API:

```python  
tools = [  
  {  
    "type": "mcp",  
    "server_label": "wordpress-mcp",  
    "server_url": "https://<domain>/mcp",  
    "headers": {  
      "Authorization": "Bearer "  
    },  
    "require_approval": "never"  
  }  
]
```

More details:  
https://cookbook.openai.com/examples/mcp/mcp_tool_guide

---

## About This MCP Architecture

This MCP server contains two core files.

### app.py

- Flask app with POST /mcp  
- Validates MCP_TOKEN  
- Handles JSON‑RPC notifications (204 No Content)  
- Delegates logic to mcp_helper.py  

### mcp_helper.py

- Routes initialize, tools/list, and tools/call  
- Dispatches tool calls to WordPress REST API  
- Normalizes WordPress responses into MCP‑shaped outputs  

---

## Endpoints and Protocol

- Protocol: JSON‑RPC MCP  
- Endpoint: POST /mcp  
- Auth: Authorization: Bearer MCP_TOKEN  
- Content-Type: application/json  

Supported methods:

- initialize  
- tools/list  
- tools/call  
- notifications/initialized (204 only)  

---

## Deploying to Google Cloud Run

This MCP server is designed to be deployed on Google Cloud Run.

[![Run on Google Cloud](https://www.prototypr.ai/static/img/run_on_google_cloud_cta.webp)](https://deploy.cloud.run?git_repo=https://github.com/garethcull/wordpress-mcp)

Important notes:

- Cloud Run is a paid service  
- Billing must be enabled  
- Environment variables must be configured  

Helpful guide:  
https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service

---

## License

MIT License

---

## Contributions and Support

Feedback, issues, and PRs are welcome. Due to bandwidth constraints, no timelines are guaranteed for free updates.

If you need help customizing this MCP server or integrating it into a broader AI workflow, I’m available for paid consulting.

Connect on LinkedIn:  
https://www.linkedin.com/in/garethcull/

---

Thanks for checking out the WordPress MCP Server. I hope it helps you and your team ship faster and closer to production. Happy publishing.

---
