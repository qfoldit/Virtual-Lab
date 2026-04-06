"""Tests for web_search and pubmed_search parameter behaviour in run_meeting()."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openai import NOT_GIVEN
from openai.types.chat.completion_create_params import WebSearchOptions

from virtual_lab.agent import Agent
from virtual_lab.run_meeting import run_meeting


AGENT = Agent(
    title="Scientist",
    expertise="biology",
    goal="do science",
    role="researcher",
    model="gpt-5.2",
)


def _make_mock_response() -> MagicMock:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "done"
    mock_response.choices[0].message.tool_calls = None
    return mock_response


def _run(tmp_path: Path, pubmed_search: bool = False, web_search: bool = False) -> MagicMock:
    """Runs a minimal individual meeting with mocked OpenAI. Returns the mock create callable."""
    mock_create = MagicMock(return_value=_make_mock_response())

    with patch("virtual_lab.run_meeting.OpenAI") as MockOpenAI, \
         patch("virtual_lab.run_meeting.save_meeting"), \
         patch("virtual_lab.run_meeting.print_cost_and_time"), \
         patch("virtual_lab.run_meeting.count_discussion_tokens",
               return_value={"input": 0, "output": 0, "max": 0, "tool": 0}):

        MockOpenAI.return_value.chat.completions.create = mock_create

        run_meeting(
            meeting_type="individual",
            agenda="Test agenda",
            save_dir=tmp_path,
            team_member=AGENT,
            num_rounds=0,
            pubmed_search=pubmed_search,
            web_search=web_search,
        )

    return mock_create


def test_web_search_disabled_passes_not_given(tmp_path):
    """When web_search=False, web_search_options should be NOT_GIVEN."""
    mock_create = _run(tmp_path, web_search=False)
    kwargs = mock_create.call_args_list[0].kwargs
    assert kwargs.get("web_search_options") is NOT_GIVEN


def test_web_search_enabled_passes_web_search_options(tmp_path):
    """When web_search=True, web_search_options should be a WebSearchOptions instance."""
    mock_create = _run(tmp_path, web_search=True)
    kwargs = mock_create.call_args_list[0].kwargs
    # WebSearchOptions() is an empty dict (TypedDict doesn't support isinstance checks)
    assert kwargs.get("web_search_options") == {}


def test_web_search_does_not_affect_tools_list(tmp_path):
    """Enabling web_search should not add anything to the tools list."""
    mock_create = _run(tmp_path, web_search=True, pubmed_search=False)
    kwargs = mock_create.call_args_list[0].kwargs
    assert kwargs.get("tools") is NOT_GIVEN


def test_pubmed_and_web_search_can_be_combined(tmp_path):
    """Both pubmed_search and web_search can be enabled simultaneously."""
    mock_create = _run(tmp_path, pubmed_search=True, web_search=True)
    kwargs = mock_create.call_args_list[0].kwargs
    # tools list should contain PubMed tool
    assert kwargs.get("tools") is not NOT_GIVEN
    # web_search_options should be set (as a dict, not NOT_GIVEN)
    assert kwargs.get("web_search_options") == {}
    assert kwargs.get("web_search_options") is not NOT_GIVEN


def test_web_search_options_propagates_to_followup_create_call(tmp_path):
    """When a PubMed tool call fires, the follow-up create() call must also carry web_search_options."""
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

    # Build a mock tool call for PubMed so the first response triggers run_tools()
    fake_tool_call = MagicMock(spec=ChatCompletionMessageToolCall)
    fake_tool_call.id = "call_abc"
    fake_tool_call.function = MagicMock(spec=Function)
    fake_tool_call.function.name = "pubmed_search"
    fake_tool_call.function.arguments = '{"query": "test", "num_articles": 1}'

    # First create() returns a response with a tool call; second returns a normal response
    first_response = MagicMock()
    first_response.choices[0].message.content = None
    first_response.choices[0].message.tool_calls = [fake_tool_call]

    second_response = MagicMock()
    second_response.choices[0].message.content = "done"
    second_response.choices[0].message.tool_calls = None

    mock_create = MagicMock(side_effect=[first_response, second_response])

    with patch("virtual_lab.run_meeting.OpenAI") as MockOpenAI, \
         patch("virtual_lab.run_meeting.save_meeting"), \
         patch("virtual_lab.run_meeting.print_cost_and_time"), \
         patch("virtual_lab.run_meeting.count_discussion_tokens",
               return_value={"input": 0, "output": 0, "max": 0, "tool": 0}), \
         patch("virtual_lab.run_meeting.run_tools",
               return_value=(["pubmed result"], [{"role": "tool", "tool_call_id": "call_abc", "content": "result"}])):

        MockOpenAI.return_value.chat.completions.create = mock_create

        run_meeting(
            meeting_type="individual",
            agenda="Test agenda",
            save_dir=tmp_path,
            team_member=AGENT,
            num_rounds=0,
            pubmed_search=True,
            web_search=True,
        )

    # The second create() call (tool followup) should also carry web_search_options
    assert mock_create.call_count == 2
    second_call_kwargs = mock_create.call_args_list[1].kwargs
    # WebSearchOptions is a TypedDict, so we check it's a dict and not NOT_GIVEN
    assert second_call_kwargs.get("web_search_options") == {}
    assert second_call_kwargs.get("web_search_options") is not NOT_GIVEN
