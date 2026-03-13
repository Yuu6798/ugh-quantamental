from pathlib import Path


def test_review_autofix_workflow_uses_pr_head_repository_checkout() -> None:
    workflow = Path('.github/workflows/review-autofix.yml').read_text(encoding='utf-8')
    assert 'repository: ${{ github.event.pull_request.head.repo.full_name || github.repository }}' in workflow
    assert 'ref: ${{ github.event.pull_request.head.ref || github.ref_name }}' in workflow
    assert 'group: review-autofix-${{ github.event.pull_request.number || github.ref_name }}' in workflow
    assert 'cancel-in-progress: false' in workflow
