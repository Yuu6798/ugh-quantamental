from pathlib import Path


def test_review_autofix_workflow_uses_trusted_execution_and_pr_data_checkout() -> None:
    workflow = Path('.github/workflows/review-autofix.yml').read_text(encoding='utf-8')
    assert "name: Check out trusted base revision" in workflow
    assert 'repository: ${{ github.repository }}' in workflow
    assert 'ref: ${{ github.event.pull_request.base.sha || github.sha }}' in workflow
    assert 'path: trusted-bot' in workflow
    assert "name: Check out PR head branch as data workspace" in workflow
    assert 'repository: ${{ github.event.pull_request.head.repo.full_name || github.repository }}' in workflow
    assert 'ref: ${{ github.event.pull_request.head.ref || github.ref_name }}' in workflow
    assert 'path: pr-head' in workflow
    assert 'working-directory: trusted-bot' in workflow
    assert 'working-directory: pr-head' in workflow
    assert 'TRUSTED_SRC: ${{ github.workspace }}/trusted-bot/src' in workflow
    assert 'os.environ["PYTHONPATH"] = trusted_src' in workflow
    assert 'runpy.run_module("ugh_quantamental.review_autofix.bot", run_name="__main__")' in workflow
    assert 'group: review-autofix-${{ github.event.pull_request.number || github.ref_name }}' in workflow
    assert 'cancel-in-progress: false' in workflow
