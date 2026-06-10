from item_reviser.prompting import AgentPromptConfig, agent_prompt_config


def test_inline_prompt_config_renders_template_values():
    prompt = AgentPromptConfig.from_config(
        {
            "template": "Question: ${question}\nOptions: ${response_options}",
            "max_retries": 2,
            "timeout_seconds": 5,
        }
    )

    rendered = prompt.render(
        {
            "question": "How satisfied are you?",
            "response_options": ["Very dissatisfied", "Very satisfied"],
        }
    )

    assert "How satisfied are you?" in rendered
    assert "Very dissatisfied" in rendered
    assert prompt.max_retries == 2
    assert prompt.timeout_seconds == 5


def test_agent_prompt_config_selects_named_agent_config():
    config = {
        "quality_checker": {
            "template": "Check: ${question}",
        }
    }

    prompt = agent_prompt_config(config, "quality_checker")

    assert prompt.render({"question": "Q?"}) == "Check: Q?"
