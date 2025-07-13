#!/usr/bin/env python3
"""
Module 1: Basic MCP Server - Starter Code
TODO: Implement tools for analyzing git changes and suggesting PR templates
"""

import json
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("pr-agent")

# PR template directory (shared across all modules)
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


# TODO: Implement tool functions here
# Example structure for a tool:
# @mcp.tool()
# async def analyze_file_changes(base_branch: str = "main", include_diff: bool = True) -> str:
#     """Get the full diff and list of changed files in the current git repository.
#     
#     Args:
#         base_branch: Base branch to compare against (default: main)
#         include_diff: Include the full diff content (default: true)
#     """
#     # Your implementation here
#     pass

# Minimal stub implementations so the server runs
# TODO: Replace these with your actual implementations

@mcp.tool()
async def analyze_file_changes(base_branch: str = "main", include_diff: bool = True, max_diff_lines: int = 500) -> str:
    """
    Get the full diff and list of changed files in the current git repository.
    """
    try:
        # Claude의 작업 디렉토리(roots) 얻기
        context = mcp.get_context()
        roots_result = await context.session.list_roots()
        working_dir = roots_result.roots[0].uri.path

        # git diff 실행 (변경 내용)
        result = subprocess.run(
            ["git", "diff", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            cwd=working_dir
        )
        diff_output = result.stdout
        diff_lines = diff_output.split('\n')

        # diff가 너무 길면 자르기
        if len(diff_lines) > max_diff_lines:
            diff_output = '\n'.join(diff_lines[:max_diff_lines])
            diff_output += f"\n\n... Output truncated. Showing {max_diff_lines} of {len(diff_lines)} lines ..."

        # git diff --stat 실행 (통계 정보)
        stats_result = subprocess.run(
            ["git", "diff", "--stat", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            cwd=working_dir
        )

        # git diff --name-only 실행 (변경된 파일 목록)
        files_result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            cwd=working_dir
        )
        files_changed = files_result.stdout.strip().split('\n') if files_result.stdout else []

        # JSON으로 반환
        return json.dumps({
            "stats": stats_result.stdout,
            "total_lines": len(diff_lines),
            "diff": diff_output if include_diff else "Use include_diff=true to see diff",
            "files_changed": files_changed
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
    
    

@mcp.tool()
async def get_pr_templates() -> str:
    """List available PR templates with their content."""
    try:
        templates = []
        if TEMPLATES_DIR.exists():
            for template_file in TEMPLATES_DIR.glob("*.md"):
                with open(template_file, "r", encoding="utf-8") as f:
                    templates.append({
                        "name": template_file.stem,
                        "content": f.read()
                    })
        return json.dumps({"templates": templates})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def suggest_template(changes_summary: str, change_type: str) -> str:
    """
    Let Claude analyze the changes and suggest the most appropriate PR template.
    """
    try:
        mapping = {
            "feature": "Feature",
            "bugfix": "Bugfix",
            "refactor": "Refactor",
            "docs": "Docs",
            "test": "Test",
            # 필요에 따라 추가
        }
        template = mapping.get(change_type.lower(), "Feature")
        return json.dumps({"suggested_template": template})
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run()