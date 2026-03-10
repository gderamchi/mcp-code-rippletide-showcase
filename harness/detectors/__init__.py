from .avoid_unnecessary_questions import detect as detect_avoid_unnecessary_questions
from .branch_sandbox_discipline import detect as detect_branch_sandbox_discipline
from .complete_end_to_end import detect as detect_complete_end_to_end
from .minimal_change import detect as detect_minimal_change
from .no_destructive_commands import detect as detect_no_destructive_commands
from .no_hallucinated_repo_assumptions import detect as detect_no_hallucinated_repo_assumptions
from .preserve_user_changes import detect as detect_preserve_user_changes
from .proper_tool_usage import detect as detect_proper_tool_usage
from .secret_and_instruction_safety import detect as detect_secret_and_instruction_safety
from .validate_before_conclude import detect as detect_validate_before_conclude

RULE_DETECTORS = {
    '1_validate_before_conclude': detect_validate_before_conclude,
    '2_minimal_change': detect_minimal_change,
    '3_no_hallucinated_repo_assumptions': detect_no_hallucinated_repo_assumptions,
    '4_preserve_user_changes': detect_preserve_user_changes,
    '5_no_destructive_commands': detect_no_destructive_commands,
    '6_proper_tool_usage': detect_proper_tool_usage,
    '7_complete_end_to_end': detect_complete_end_to_end,
    '8_avoid_unnecessary_questions': detect_avoid_unnecessary_questions,
    '9_branch_sandbox_discipline': detect_branch_sandbox_discipline,
    '10_secret_and_instruction_safety': detect_secret_and_instruction_safety,
}

